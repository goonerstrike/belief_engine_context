# Data Schema

## Overview
Complete data models for the Belief Engine pipeline with strict source linkage enforcement.

## Core Entities

### Episode
Represents a single episode or transcript processing run.

```python
{
  "id": str,                    # Unique identifier (e.g., "episode_001")
  "title": str,                 # Episode title
  "date": str,                  # ISO 8601 date (YYYY-MM-DD)
  "transcript_path": str,       # Path to diarized transcript
  "audio_uri": Optional[str],   # URI to audio file (e.g., "s3://bucket/episode.mp3")
  "metadata": dict,             # Additional metadata
  "quality_score": float,       # Quality score 0-100
  "quality_grade": str,         # Grade: A, B, C, D, F
  "wandb_run_id": Optional[str] # W&B run identifier
}
```

**Constraints:**
- `id` must be unique
- `date` must be valid ISO 8601
- `quality_score` in range [0, 100]
- `quality_grade` in {A, B, C, D, F}

---

### Utterance
Atomic unit of speech from a single speaker.

```python
{
  "id": str,                    # Unique identifier (UUID)
  "episode_id": str,            # REQUIRED: Foreign key to Episode
  "speaker": str,               # Speaker identifier (e.g., "SPEAKER_A")
  "timestamp_start": str,       # Start timestamp (HH:MM:SS)
  "timestamp_end": str,         # End timestamp (HH:MM:SS)
  "text": str,                  # Utterance text
  "audio_snippet_uri": Optional[str]  # URI with fragment (e.g., "episode.mp3#t=734")
}
```

**Constraints:**
- `episode_id` must reference valid Episode
- `timestamp_start` < `timestamp_end`
- `text` must not be empty
- Audio URI format: `{file}#t={seconds}` or `{file}#t={start},{end}`

---

### Belief
Atomic, declarative statement extracted from an utterance.

```python
{
  "id": str,                    # Unique identifier (UUID)
  "utterance_id": str,          # REQUIRED: Foreign key to Utterance (source linkage)
  "belief_text": str,           # The extracted belief statement
  "confidence": float,          # Extraction confidence [0.0, 1.0]
  "original_quote": str,        # Original quote from utterance
  "context": Optional[str],     # Additional context
  "extraction_flags": dict      # Flags q16-q26 for tier assignment
}
```

**Extraction Flags (q16-q26):**
```python
{
  "q16_first_principles": bool,       # Core belief (first principles)
  "q17_worldview": bool,              # Worldview belief
  "q18_moral_framework": bool,        # Moral/ethical framework
  "q19_epistemology": bool,           # How knowledge is acquired
  "q20_ontology": bool,               # Nature of reality
  "q21_reasoning_pattern": bool,      # Reasoning/logic pattern
  "q22_assumption": bool,             # Underlying assumption
  "q23_surface_opinion": bool,        # Surface-level opinion
  "q24_factual_claim": bool,          # Factual claim
  "q25_prediction": bool,             # Future prediction
  "q26_value_judgment": bool          # Value judgment
}
```

**Constraints:**
- `utterance_id` must reference valid Utterance (CRITICAL)
- `confidence` in range [0.0, 1.0]
- `belief_text` must be declarative, atomic statement
- At least one extraction flag must be true

---

### CanonicalBelief
Standardized, deduplicated belief representation.

```python
{
  "id": str,                    # Unique identifier (UUID)
  "canonical_text": str,        # Standardized belief text
  "belief_ids": List[str],      # List of raw Belief IDs mapped to this canonical belief
  "source_utterance_ids": List[str],  # CRITICAL: All source utterances
  "example_quotes": List[str],  # Example quotes from source utterances
  "cluster_id": Optional[str],  # Foreign key to Cluster
  "first_seen_episode": str,    # Episode ID where first appeared
  "last_seen_episode": str,     # Episode ID where last appeared
  "embedding": Optional[List[float]]  # Vector embedding (cached)
}
```

**Constraints:**
- `belief_ids` must not be empty
- `source_utterance_ids` must not be empty (CRITICAL for auditability)
- `example_quotes` must contain at least one quote
- `canonical_text` must be normalized

---

### Cluster
Group of semantically similar canonical beliefs.

```python
{
  "id": str,                    # Unique identifier (UUID)
  "name": str,                  # Cluster name/description
  "canonical_belief_ids": List[str],  # List of CanonicalBelief IDs in cluster
  "source_utterance_ids": List[str],  # CRITICAL: All source utterances
  "example_quotes": List[str],  # Representative quotes
  "ontology_level": str,        # Tier: "core" | "worldview" | "reasoning" | "surface"
  "parent_cluster_id": Optional[str],  # For hierarchical clustering
  "size": int,                  # Number of canonical beliefs
  "created_episode": str,       # Episode where cluster was created
  "last_updated_episode": str   # Episode where cluster was last updated
}
```

**Constraints:**
- `size` >= MIN_CLUSTER_SIZE (default: 3)
- `ontology_level` in {"core", "worldview", "reasoning", "surface"}
- `canonical_belief_ids` must match `size`
- Clusters below min_cluster_size are marked as outliers

---

### BeliefMatrix
Weighted matrix tracking beliefs across episodes.

**Structure:** `episodes × canonical_beliefs`

```python
{
  "episodes": List[str],        # List of episode IDs (rows)
  "canonical_belief_ids": List[str],  # List of canonical belief IDs (columns)
  "weights": Dict[str, Dict[str, Weight]]  # Nested dict: episode_id → belief_id → Weight
}
```

**Weight Schema:**
```python
{
  "conviction_avg": float,      # Mean confidence score [0.0, 1.0]
  "frequency": int,             # Count of mentions
  "stability_score": float,     # Consistency across episode [0.0, 1.0]
  "presence_flag": bool         # Boolean indicator (present/absent)
}
```

**NOT** a boolean matrix - weights contain rich information.

---

### Contradiction
Pair of contradictory or opposing beliefs.

```python
{
  "id": str,                    # Unique identifier (UUID)
  "belief_a_id": str,           # First belief ID (CanonicalBelief)
  "belief_b_id": str,           # Second belief ID (CanonicalBelief)
  "opposition_score": float,    # Semantic opposition score [0.0, 1.0]
  "type": str,                  # "within_speaker" | "cross_speaker"
  "episode_ids": List[str],     # Episodes where contradiction appears
  "is_reversal": bool,          # True if same speaker reversed position
  "speaker_a": Optional[str],   # Speaker for belief_a
  "speaker_b": Optional[str],   # Speaker for belief_b
  "detected_at": str            # ISO 8601 timestamp
}
```

**Constraints:**
- `opposition_score` in range [0.0, 1.0]
- `type` in {"within_speaker", "cross_speaker"}
- If `is_reversal` is true, `type` must be "within_speaker"

---

### BeliefDrift
Tracks how a belief changes over time.

```python
{
  "id": str,                    # Unique identifier (UUID)
  "canonical_belief_id": str,   # Foreign key to CanonicalBelief
  "drift_type": str,            # "new" | "dropped" | "strengthening" | "weakening" | "reversal"
  "magnitude": float,           # Magnitude of change [0.0, 1.0]
  "episode_range": List[str],   # [start_episode_id, end_episode_id]
  "conviction_before": Optional[float],  # Conviction before change
  "conviction_after": Optional[float],   # Conviction after change
  "frequency_before": Optional[int],
  "frequency_after": Optional[int]
}
```

**Drift Types:**
- **new**: First appearance in current episode
- **dropped**: Present in previous episodes, absent now
- **strengthening**: Conviction or frequency increased
- **weakening**: Conviction or frequency decreased
- **reversal**: Speaker contradicts their own previous belief

---

### BeliefRegistry
Global registry for deduplication and tracking.

```python
{
  "canonical_beliefs": Dict[str, CanonicalBeliefEntry],  # belief_id → entry
  "embeddings_cache": Dict[str, List[float]],           # belief_id → embedding
  "aliases": Dict[str, str],                            # raw_belief_text → canonical_id
  "episode_history": Dict[str, List[str]]               # belief_id → episode_ids
}
```

**CanonicalBeliefEntry:**
```python
{
  "canonical_belief": CanonicalBelief,
  "raw_belief_ids": List[str],
  "similarity_threshold": float
}
```

---

### QualityReport
Quality metrics for an episode processing run.

```python
{
  "episode_id": str,
  "quality_score": float,       # Overall score [0-100]
  "quality_grade": str,         # A, B, C, D, F
  "errors_count": int,
  "retries_count": int,
  "malformed_beliefs_count": int,
  "registry_mismatches_count": int,
  "parsing_errors": List[str],
  "api_errors": List[str],
  "warnings": List[str],
  "execution_time_seconds": float,
  "timestamp": str              # ISO 8601 timestamp
}
```

**Quality Grading:**
- A: 90-100 (Excellent)
- B: 80-89 (Good)
- C: 70-79 (Acceptable)
- D: 60-69 (Poor)
- F: 0-59 (Failing)

---

## Source Linkage Requirements (CRITICAL)

### Traceability Chain
Every entity must be traceable back to source utterances:

```
Ontology Node → Cluster → CanonicalBelief → Belief → Utterance → Episode
```

### Mandatory Fields
- Every `Belief` MUST have `utterance_id`
- Every `CanonicalBelief` MUST have `source_utterance_ids` and `example_quotes`
- Every `Cluster` MUST have `source_utterance_ids` and `example_quotes`
- Every `Contradiction` MUST reference source beliefs

### Validation
All entities must pass Pydantic validation:
- Foreign keys must reference existing entities
- Lists must not be empty where required
- Timestamps must be valid ISO 8601
- Scores must be within valid ranges

---

## File Formats

### Checkpoint Format
JSON files with metadata:
```json
{
  "metadata": {
    "episode_id": "episode_001",
    "phase": "beliefs_raw",
    "timestamp": "2025-01-15T10:30:00Z",
    "stats": {
      "count": 150,
      "processing_time_seconds": 45.2
    }
  },
  "data": [...]
}
```

### Matrix Export Format
**CSV:**
```
episode_id,belief_001,belief_002,...
episode_001,0.85,0.0,...
episode_002,0.90,0.45,...
```

**JSON:**
```json
{
  "episodes": ["episode_001", "episode_002"],
  "canonical_beliefs": ["belief_001", "belief_002"],
  "weights": {
    "episode_001": {
      "belief_001": {
        "conviction_avg": 0.85,
        "frequency": 3,
        "stability_score": 0.92,
        "presence_flag": true
      }
    }
  }
}
```

---

## Summary

This schema ensures:
1. **Complete source linkage** for auditability
2. **Rich metadata** for analysis
3. **Strict validation** via Pydantic
4. **Weighted tracking** (not boolean)
5. **Drift detection** capabilities
6. **Quality metrics** for every run

