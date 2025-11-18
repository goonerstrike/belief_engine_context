# Pipeline Description

## Overview
End-to-end belief extraction and longitudinal tracking pipeline with 9 major stages, checkpointing, parallelization, and comprehensive error handling.

## Pipeline Architecture

```
Diarized Transcript
    ↓
1. INGESTION ────────→ Episode + Utterances
    ↓ [checkpoint: utterances.json]
2. UTTERANCE SPLIT ──→ Atomic Utterances
    ↓ [checkpoint: utterances.json]
3. BELIEF EXTRACTION → Raw Beliefs (parallel)
    ↓ [checkpoint: beliefs_raw.json]
4. REGISTRY LOOKUP ──→ Match existing canonical beliefs
    ↓
5. CANONICALIZATION → Canonical Beliefs (parallel)
    ↓ [checkpoint: canonical_beliefs.json]
6. CLUSTERING ───────→ Global Clusters (parallel)
    ↓ [checkpoint: clusters_updated.json]
7. ONTOLOGY ─────────→ Hierarchical Ontology
    ↓
8. MATRIX BUILDING ──→ Weighted Belief Matrix
    ↓
9. TIMELINE/CONTRARIAN → Drift Detection + Contradictions
    ↓
[Quality Report + W&B Artifacts]
```

---

## Stage 1: Ingestion

### Purpose
Parse diarized transcript files and create Episode + Utterance objects.

### Input
Diarized transcript file with format:
```
SPEAKER_A | HH:MM:SS | HH:MM:SS | utterance text
SPEAKER_B | HH:MM:SS | HH:MM:SS | utterance text
```

### Process
1. Load transcript file
2. Parse each line:
   - Extract speaker ID
   - Extract start/end timestamps
   - Extract utterance text
3. Create Episode object
4. Create Utterance objects with source linkage

### Error Handling
- **Malformed line**: Log warning, skip line, continue
- **Missing timestamp**: Use fallback (previous + 1 second)
- **Empty text**: Skip line, log info
- **Invalid format**: Try alternative parsing, log error if fail

### Quality Tracking
- Count: `parsing_errors`, `malformed_lines`
- Track: Lines parsed, utterances created

### Output
- Episode object
- List of Utterance objects

### W&B Logging
```python
wandb.log({"utterances_parsed": count})
wandb.log({"errors_count": parsing_errors})
```

### Checkpoint
None (entry point)

---

## Stage 2: Utterance Splitting

### Purpose
Split long utterances into atomic statements while preserving speaker and timestamp info.

### Input
List of Utterance objects

### Process
1. For each utterance:
   - Split on sentence boundaries (., !, ?)
   - Preserve speaker and timestamp
   - Generate unique utterance IDs
   - Calculate audio snippet URIs if audio available

### Error Handling
- **Invalid timestamp**: Use fallback, log warning
- **Empty after split**: Skip, log info

### Quality Tracking
- Count: Invalid timestamps, empty utterances

### Output
- List of atomic Utterance objects

### W&B Logging
```python
wandb.log({"utterances_created": count})
```

### Checkpoint
`checkpoints/episode_XXX/utterances.json`

---

## Stage 3: Belief Extraction (PARALLELIZED)

### Purpose
Extract atomic, declarative beliefs from utterances using OpenAI GPT-4.

### Input
List of Utterance objects

### Process (Parallel)
1. **Batch utterances** (BATCH_SIZE=10)
2. **Parallel processing** (MAX_WORKERS=5):
   - For each batch:
     - Construct extraction prompt
     - Call OpenAI API with retry logic
     - Parse response (JSON format)
     - Extract beliefs with extraction_flags (q16-q26)
3. **Rate limiting**: Respect API_RATE_LIMIT_RPM and TPM
4. **Create Belief objects** with utterance_id linkage

### Prompt Template
```
You are extracting atomic, declarative beliefs from the following utterance.

Utterance: "{utterance_text}"
Speaker: {speaker}

Extract all beliefs as declarative statements. For each belief, provide:
1. belief_text: The atomic belief statement
2. confidence: Confidence score 0.0-1.0
3. original_quote: Direct quote from utterance
4. extraction_flags: Boolean flags q16-q26

Extraction Flags:
- q16_first_principles: Core belief (first principles)
- q17_worldview: Worldview belief
- q18_moral_framework: Moral/ethical framework
- q19_epistemology: How knowledge is acquired
- q20_ontology: Nature of reality
- q21_reasoning_pattern: Reasoning/logic pattern
- q22_assumption: Underlying assumption
- q23_surface_opinion: Surface-level opinion
- q24_factual_claim: Factual claim
- q25_prediction: Future prediction
- q26_value_judgment: Value judgment

Return JSON list of beliefs.
```

### Error Handling
- **API timeout**: Retry with exponential backoff (MAX_RETRIES=3)
- **Rate limit 429**: Wait and retry with backoff
- **Invalid JSON**: Log error, try to parse partial, fallback to retry
- **Max retries exceeded**: Skip utterance, log error, continue
- **Malformed belief**: Log as malformed_belief, skip

### Quality Tracking
- Count: `api_errors`, `retries_count`, `malformed_beliefs_count`
- Track: Beliefs extracted, API calls, tokens used, cost

### Parallelization
```python
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    with RateLimiter(rpm=API_RATE_LIMIT_RPM, tpm=API_RATE_LIMIT_TPM):
        futures = [executor.submit(extract_batch, batch) for batch in batches]
        for future in as_completed(futures):
            beliefs.extend(future.result())
```

### Output
- List of Belief objects (with utterance_id)

### W&B Logging
```python
wandb.log({
    "beliefs_extracted": count,
    "api_calls_total": api_calls,
    "api_tokens_used": tokens,
    "api_cost_usd": cost,
    "api_latency_avg": avg_latency,
    "api_errors": error_count,
    "api_retries": retry_count
})
```

### Checkpoint
`checkpoints/episode_XXX/beliefs_raw.json`

---

## Stage 4: Registry Lookup

### Purpose
Match extracted beliefs against global registry to identify existing canonical beliefs.

### Input
- List of Belief objects
- Global BeliefRegistry

### Process
1. Load global registry from disk
2. For each belief:
   - Check alias mapping (exact text match)
   - If no match, generate embedding
   - Calculate cosine similarity with existing canonical beliefs
   - If similarity > threshold (e.g., 0.85), map to existing
   - Else, mark as new canonical belief candidate

### Error Handling
- **Corrupted registry**: Backup and rebuild from episodes
- **Embedding API failure**: Use cached embeddings, log error
- **Mismatch**: Count as registry_mismatch

### Quality Tracking
- Count: `registry_mismatches_count`

### Output
- Mapping: belief_id → canonical_belief_id (or None for new)

### W&B Logging
```python
wandb.log({"registry_mismatches": count})
```

---

## Stage 5: Canonicalization (PARALLELIZED)

### Purpose
Standardize belief phrasing and create/update CanonicalBelief objects.

### Input
- List of Belief objects
- Mapping from registry lookup

### Process (Parallel)
1. **Linguistic Normalization**:
   - Lowercase
   - Remove punctuation
   - Normalize synonyms
   - Hash for exact duplicates
2. **Fuzzy Matching** (parallel):
   - Calculate Levenshtein distance
   - Calculate semantic similarity (embeddings)
   - Group similar beliefs (threshold-based)
3. **LLM Fallback** (when fuzzy insufficient):
   - Use OpenAI to canonicalize phrasing
   - Preserve semantic meaning
4. **Create CanonicalBelief objects**:
   - canonical_text
   - belief_ids[] (all raw beliefs mapped)
   - source_utterance_ids[] (CRITICAL)
   - example_quotes[]

### Error Handling
- **Normalization failure**: Use original text, log warning
- **Fuzzy match timeout**: Skip to LLM fallback
- **LLM canonicalization error**: Use normalized text as canonical

### Quality Tracking
- Count: Canonicalization errors, fuzzy match failures

### Output
- List of CanonicalBelief objects

### W&B Logging
```python
wandb.log({"canonical_beliefs_created": count})
```

### Checkpoint
`checkpoints/episode_XXX/canonical_beliefs.json`

---

## Stage 6: Clustering (PARALLELIZED, GLOBAL)

### Purpose
Group semantically similar canonical beliefs into global clusters.

### Input
- List of CanonicalBelief objects (from current episode)
- Global ClusterStore

### Process (Parallel, Global)
1. **Load global cluster store** from disk
2. **Generate embeddings** (parallel, EMBEDDING_WORKERS=3):
   - Use OpenAI embeddings API
   - Cache embeddings
3. **Calculate distances** (parallel):
   - Cosine distance between all belief pairs
4. **Incremental clustering**:
   - For each new canonical belief:
     - Find closest existing cluster
     - If distance < threshold, assign to cluster
     - Else, check if forms new cluster with other new beliefs
5. **Filter micro-clusters**:
   - Remove clusters with size < MIN_CLUSTER_SIZE (default: 3)
   - Mark as outliers or merge with nearest cluster
6. **Update global cluster store**
7. **Persist to disk**

### Error Handling
- **Cluster corruption**: Rebuild from all canonical beliefs
- **Embedding API failure**: Use cached embeddings
- **Micro-cluster**: Filter or merge, log warning

### Quality Tracking
- Count: `micro_clusters_filtered`
- Track: Clusters created, average cluster size

### Configuration
```python
MIN_CLUSTER_SIZE = 3
CLUSTERING_DISTANCE_THRESHOLD = 0.3
```

### Output
- List of Cluster objects
- Updated global ClusterStore

### W&B Logging
```python
wandb.log({
    "clusters_total": total_clusters,
    "avg_cluster_size": avg_size,
    "micro_clusters_filtered": filtered_count
})
```

### Checkpoint
`checkpoints/episode_XXX/clusters_updated.json`

---

## Stage 7: Ontology Building

### Purpose
Build hierarchical belief ontology with tier assignment.

### Input
- List of Cluster objects

### Process
1. **Tier Assignment** (RULES-BASED, NOT GPT):
   - For each cluster:
     - Aggregate extraction_flags from all beliefs
     - Apply rules:
       - If majority q16_first_principles or q20_ontology → "core"
       - If majority q17_worldview or q18_moral_framework → "worldview"
       - If majority q21_reasoning_pattern or q22_assumption → "reasoning"
       - If majority q23_surface_opinion or q24_factual_claim → "surface"
2. **Hierarchy Building**:
   - Group clusters by tier
   - Identify parent-child relationships (semantic containment)
   - Build tree structure
3. **Store source linkage** at every node:
   - source_utterance_ids[]
   - example_quotes[]

### Error Handling
- **Missing extraction flags**: Default to "surface" tier
- **Ambiguous tier**: Use majority vote, log info

### Quality Tracking
- Count: Default tier assignments

### Output
- Hierarchical Ontology (tree structure)
- Tier counts

### W&B Logging
```python
wandb.log({
    "ontology_tiers": {
        "core": count_core,
        "worldview": count_worldview,
        "reasoning": count_reasoning,
        "surface": count_surface
    }
})
```

---

## Stage 8: Matrix Building

### Purpose
Build weighted episode × canonical_beliefs matrix.

### Input
- List of episodes (current + historical)
- List of all canonical beliefs

### Process
1. **Initialize matrix**: episodes × canonical_beliefs
2. **For each episode**:
   - For each canonical belief:
     - Calculate weights:
       - `conviction_avg`: Mean confidence of all raw beliefs mapped to canonical
       - `frequency`: Count of mentions
       - `stability_score`: Consistency within episode (stddev of confidences)
       - `presence_flag`: True if belief mentioned, False otherwise
3. **Export**:
   - CSV format (for analysis)
   - JSON format (structured)

### Error Handling
- **Weight calculation error**: Use default weights (0.0, 0, 0.0, False)

### Output
- BeliefMatrix object
- CSV export
- JSON export

### W&B Logging
```python
wandb.log({"matrix_dimensions": f"{n_episodes}x{n_beliefs}"})
wandb.save("belief_matrix.csv")
```

---

## Stage 9: Timeline & Contrarian Detection

### Purpose
Detect belief drift and contradictions.

### Submodule A: Timeline Drift Detection

**Process:**
1. Compare current episode with previous episodes
2. For each canonical belief, detect drift_type:
   - **new**: First appearance
   - **dropped**: Was present, now absent
   - **strengthening**: Conviction or frequency increased > threshold
   - **weakening**: Conviction or frequency decreased > threshold
   - **reversal**: Speaker contradicts own previous belief
3. Calculate magnitude of change
4. Generate timeline report

**Output:**
- List of BeliefDrift objects
- Timeline report (JSON)

### Submodule B: Contrarian Detection (PARALLELIZED)

**Process (Parallel):**
1. Generate all belief pairs (within episode or across episodes)
2. **Parallel opposition scoring**:
   - Calculate semantic similarity
   - Detect negation patterns
   - Use LLM verification for ambiguous cases
3. Filter pairs with opposition_score > threshold (e.g., 0.7)
4. Classify:
   - `within_speaker`: Same speaker, different beliefs
   - `cross_speaker`: Different speakers
5. Mark reversals (same speaker, different episodes)

**Output:**
- List of Contradiction objects
- Contradiction report

### W&B Logging
```python
wandb.log({
    "drift_new": count_new,
    "drift_dropped": count_dropped,
    "drift_strengthening": count_strengthening,
    "drift_weakening": count_weakening,
    "drift_reversal": count_reversal,
    "contradictions_detected": count
})

# Upload contradiction table
wandb.log({
    "contradictions": wandb.Table(
        columns=["belief_a", "belief_b", "opposition_score", "type"],
        data=contradiction_rows
    )
})
```

---

## Stage 10: Quality Report & Finalization

### Purpose
Generate comprehensive quality report for the episode.

### Process
1. **Aggregate quality metrics**:
   - errors_count
   - retries_count
   - malformed_beliefs_count
   - registry_mismatches_count
2. **Calculate quality score**:
   ```python
   base_score = 100
   base_score -= (errors_count * 2)
   base_score -= (retries_count * 0.5)
   base_score -= (malformed_beliefs_count * 1)
   base_score -= (registry_mismatches_count * 0.5)
   quality_score = max(0, base_score)
   ```
3. **Assign quality grade**:
   - A: 90-100
   - B: 80-89
   - C: 70-79
   - D: 60-69
   - F: 0-59
4. **Export quality report** to `checkpoints/episode_XXX/quality_report.json`
5. **Upload all artifacts to W&B**
6. **Close W&B run**

### W&B Logging
```python
wandb.log({
    "quality_score": score,
    "quality_grade": grade,
    "total_duration_seconds": duration,
    "throughput_beliefs_per_minute": throughput
})

# Upload artifacts
wandb.log_artifact("checkpoints", type="checkpoint")
wandb.log_artifact("belief_matrix.csv", type="matrix")
wandb.log_artifact("ontology.json", type="ontology")
wandb.log_artifact("quality_report.json", type="report")

# Summary
wandb.summary["beliefs_total"] = total_beliefs
wandb.summary["quality_grade"] = grade
```

---

## Data Flow Diagram

```
┌─────────────────┐
│ Transcript.txt  │
└────────┬────────┘
         ↓
    [INGESTION]
         ↓
┌─────────────────┐
│   Utterances    │ ←──────┐
└────────┬────────┘        │
         ↓                 │
  [BELIEF EXTRACT]         │ Source
    (Parallel)             │ Linkage
         ↓                 │ Chain
┌─────────────────┐        │
│  Raw Beliefs    │ ───────┘
└────────┬────────┘
         ↓
  [REGISTRY LOOKUP]
         ↓
 [CANONICALIZATION]
    (Parallel)
         ↓
┌─────────────────┐
│ Canonical       │
│ Beliefs         │
└────────┬────────┘
         ↓
   [CLUSTERING]
    (Parallel)
         ↓
┌─────────────────┐
│   Clusters      │
└────────┬────────┘
         ↓
   [ONTOLOGY]
         ↓
┌─────────────────┐
│  Hierarchy      │
└────────┬────────┘
         ↓
  [MATRIX BUILD]
         ↓
┌─────────────────┐
│ Belief Matrix   │
└────────┬────────┘
         ↓
 [TIMELINE/CONTRARIAN]
         ↓
┌─────────────────┐
│ Reports & W&B   │
└─────────────────┘
```

---

## Checkpointing Strategy

### Checkpoint Locations
1. After Utterance Split: `utterances.json`
2. After Belief Extraction: `beliefs_raw.json`
3. After Canonicalization: `canonical_beliefs.json`
4. After Clustering: `clusters_updated.json`

### Checkpoint Format
```json
{
  "metadata": {
    "episode_id": "episode_001",
    "phase": "beliefs_raw",
    "timestamp": "2025-01-15T10:30:00Z",
    "stats": {
      "count": 150,
      "errors": 2,
      "processing_time_seconds": 45.2
    }
  },
  "data": [...]
}
```

### Recovery
If pipeline fails:
1. Detect last valid checkpoint
2. Load checkpoint data
3. Resume from next phase
4. Skip already-processed data

---

## Parallelization Summary

### Parallelized Stages
1. **Belief Extraction**: MAX_WORKERS=5 threads
2. **Canonicalization**: Parallel fuzzy matching
3. **Clustering**: EMBEDDING_WORKERS=3 for embeddings
4. **Contrarian Detection**: Parallel opposition scoring

### Rate Limiting
- API_RATE_LIMIT_RPM: 3500 requests/minute
- API_RATE_LIMIT_TPM: 90000 tokens/minute
- Token bucket algorithm
- Automatic backoff on 429 errors

---

## Error Handling Philosophy

1. **Fail fast**: Setup/config errors (exit immediately)
2. **Graceful degradation**: Processing errors (log, skip, continue)
3. **Never lose progress**: Checkpoint after each major stage
4. **Always track**: All errors logged and counted for quality score

---

## Summary

This pipeline ensures:
- **Complete source linkage**: Every belief traces to utterance
- **Parallelization**: Fast processing with rate limiting
- **Checkpointing**: Recovery from any failure point
- **Quality tracking**: Every run scored and graded
- **W&B integration**: Full experiment tracking
- **Comprehensive logging**: Debug any issue

