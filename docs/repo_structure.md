# Repository Structure

## Overview
Complete directory and module organization for the Belief Engine project.

```
belief_engine_context/
├── README.md                          # Main project README
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variable template
├── .gitignore                         # Git ignore rules
├── config.py                          # Configuration settings
├── logging_config.py                  # Logging configuration
├── wandb_config.py                    # W&B initialization
├── main.py                            # CLI entry point
│
├── docs/                              # Documentation
│   ├── README_belief_engine.md        # Comprehensive user guide
│   ├── schema.md                      # Data model specifications
│   ├── pipeline.md                    # Pipeline description
│   ├── canonicalization_rules.md      # Canonicalization specifications
│   ├── clustering_spec.md             # Clustering algorithm details
│   ├── belief_registry_design.md      # Registry design document
│   ├── matrix_format.md               # Matrix format specification
│   ├── ontology_spec.md               # Ontology tier assignment rules
│   ├── checkpoint_recovery.md         # Checkpoint and recovery guide
│   ├── parallelization_spec.md        # Parallelization strategy
│   ├── timeline_analysis.md           # Timeline drift detection
│   ├── contrarian_detection.md        # Contradiction detection algorithm
│   ├── quality_metrics.md             # Quality scoring methodology
│   ├── wandb_integration.md           # W&B best practices
│   ├── audio_linking.md               # Audio snippet URI format
│   └── graph_integration.md           # GraphRAG compatibility
│
├── src/                               # Source code
│   │
│   ├── ingestion/                     # Stage 1: Transcript ingestion
│   │   ├── __init__.py
│   │   ├── parser.py                  # Parse diarized transcripts
│   │   └── transcript_loader.py       # Load transcript files
│   │
│   ├── utterance/                     # Stage 2: Utterance processing
│   │   ├── __init__.py
│   │   ├── splitter.py                # Split into atomic utterances
│   │   └── audio_linker.py            # Generate audio snippet URIs
│   │
│   ├── beliefs/                       # Stage 3: Belief extraction
│   │   ├── __init__.py
│   │   ├── extractor.py               # Extract beliefs via OpenAI
│   │   ├── registry.py                # Global belief registry
│   │   └── prompts.py                 # Extraction prompt templates
│   │
│   ├── canonicalization/              # Stage 5: Canonicalization
│   │   ├── __init__.py
│   │   ├── normalizer.py              # Linguistic normalization
│   │   ├── matcher.py                 # Fuzzy matching
│   │   └── llm_fallback.py            # LLM canonicalization
│   │
│   ├── clustering/                    # Stage 6: Clustering
│   │   ├── __init__.py
│   │   ├── global_store.py            # Global cluster store
│   │   ├── embedder.py                # Generate embeddings
│   │   ├── clusterer.py               # Clustering algorithm
│   │   └── filter.py                  # Filter micro-clusters
│   │
│   ├── matrix/                        # Stage 8: Matrix building
│   │   ├── __init__.py
│   │   ├── builder.py                 # Build episode×belief matrix
│   │   ├── weights.py                 # Calculate weights
│   │   └── exporter.py                # Export to CSV/JSON
│   │
│   ├── ontology/                      # Stage 7: Ontology
│   │   ├── __init__.py
│   │   ├── tier_assignment.py         # Assign tiers from flags
│   │   └── hierarchy.py               # Build hierarchical structure
│   │
│   ├── timeline/                      # Stage 9A: Timeline analysis
│   │   ├── __init__.py
│   │   ├── reporter.py                # Generate timeline reports
│   │   └── drift_detector.py          # Detect drift types
│   │
│   ├── contrarian/                    # Stage 9B: Contrarian detection
│   │   ├── __init__.py
│   │   ├── detector.py                # Detect contradictions
│   │   ├── opposition_scorer.py       # Calculate opposition scores
│   │   └── reversal_tracker.py        # Track belief reversals
│   │
│   ├── models/                        # Data models (Pydantic)
│   │   ├── __init__.py
│   │   ├── episode.py                 # Episode model
│   │   ├── utterance.py               # Utterance model
│   │   ├── belief.py                  # Belief model
│   │   ├── canonical_belief.py        # CanonicalBelief model
│   │   ├── cluster.py                 # Cluster model
│   │   ├── matrix.py                  # BeliefMatrix model
│   │   ├── contradiction.py           # Contradiction model
│   │   ├── drift.py                   # BeliefDrift model
│   │   ├── registry.py                # BeliefRegistry model
│   │   └── quality_report.py          # QualityReport model
│   │
│   └── utils/                         # Utilities
│       ├── __init__.py
│       ├── logger.py                  # Logging utilities
│       ├── retry.py                   # Retry decorators with backoff
│       ├── validators.py              # Input validation
│       ├── exceptions.py              # Custom exception classes
│       ├── checkpoint.py              # Checkpoint save/load/recovery
│       ├── quality_scorer.py          # Episode quality scoring
│       ├── parallel.py                # Parallel processing + rate limiting
│       └── wandb_logger.py            # W&B integration utilities
│
├── tests/                             # Tests
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_ingestion.py
│   ├── test_utterance.py
│   ├── test_beliefs.py
│   ├── test_canonicalization.py
│   ├── test_clustering.py
│   ├── test_matrix.py
│   ├── test_ontology.py
│   ├── test_timeline.py
│   ├── test_contrarian.py
│   ├── test_checkpoint.py
│   ├── test_quality_scorer.py
│   ├── test_parallel.py
│   └── test_wandb.py
│
├── examples/                          # Example files
│   ├── matthew_lacroix.txt            # Example diarized transcript
│   ├── example_output/                # Example outputs
│   │   ├── belief_matrix.csv
│   │   ├── ontology.json
│   │   ├── timeline_report.json
│   │   └── contradictions.json
│   └── notebooks/                     # Jupyter notebooks
│       ├── analysis.ipynb
│       └── visualization.ipynb
│
├── data/                              # Data directory (gitignored except examples)
│   ├── input/                         # Input transcripts
│   │   └── .gitkeep
│   │
│   ├── output/                        # Pipeline outputs
│   │   ├── belief_matrix.csv
│   │   ├── belief_matrix.json
│   │   ├── ontology.json
│   │   ├── timeline_report.json
│   │   └── contradictions.json
│   │
│   ├── registry/                      # Persistent registries
│   │   ├── belief_registry.json
│   │   └── embeddings_cache.pkl
│   │
│   ├── clusters/                      # Global cluster store
│   │   └── global_clusters.json
│   │
│   └── checkpoints/                   # Per-episode checkpoints
│       ├── episode_001/
│       │   ├── utterances.json
│       │   ├── beliefs_raw.json
│       │   ├── canonical_beliefs.json
│       │   ├── clusters_updated.json
│       │   └── quality_report.json
│       └── episode_002/
│           └── ...
│
├── logs/                              # Log files (gitignored)
│   ├── master.log
│   ├── ingestion.log
│   ├── beliefs.log
│   ├── clustering.log
│   └── ...
│
└── wandb/                             # W&B run data (gitignored)
    └── ...
```

---

## Module Responsibilities

### src/ingestion/
**Purpose**: Parse diarized transcript files and create Episode + Utterance objects.

**Key Files**:
- `parser.py`: Parse transcript format `SPEAKER | timestamp | text`
- `transcript_loader.py`: Load files, handle encoding, validate format

**Error Handling**: Malformed lines, missing timestamps, invalid format

---

### src/utterance/
**Purpose**: Split utterances into atomic statements.

**Key Files**:
- `splitter.py`: Split on sentence boundaries
- `audio_linker.py`: Generate audio snippet URIs (`file.mp3#t=734`)

**Output**: List of atomic Utterance objects with audio links

---

### src/beliefs/
**Purpose**: Extract beliefs using OpenAI, maintain global registry.

**Key Files**:
- `extractor.py`: Parallel extraction with retry logic, rate limiting
- `registry.py`: Global registry for deduplication
- `prompts.py`: Extraction prompt templates

**Critical**: Every Belief MUST link to utterance_id

---

### src/canonicalization/
**Purpose**: Standardize belief phrasing, create canonical beliefs.

**Key Files**:
- `normalizer.py`: Linguistic normalization (lowercase, punctuation, synonyms)
- `matcher.py`: Fuzzy matching (Levenshtein, semantic similarity)
- `llm_fallback.py`: OpenAI canonicalization when fuzzy insufficient

**Output**: CanonicalBelief objects with source linkage

---

### src/clustering/
**Purpose**: Global semantic clustering across all episodes.

**Key Files**:
- `global_store.py`: Persist and load global cluster state
- `embedder.py`: Generate embeddings (parallel)
- `clusterer.py`: Incremental clustering algorithm
- `filter.py`: Filter micro-clusters (size < MIN_CLUSTER_SIZE)

**Critical**: Global, incremental, prevents fragmentation

---

### src/matrix/
**Purpose**: Build weighted episode × belief matrix.

**Key Files**:
- `builder.py`: Construct matrix structure
- `weights.py`: Calculate conviction, frequency, stability
- `exporter.py`: Export to CSV and JSON

**Output**: BeliefMatrix with rich weights (NOT boolean)

---

### src/ontology/
**Purpose**: Build hierarchical belief ontology with tier assignment.

**Key Files**:
- `tier_assignment.py`: Rules-based tier assignment from extraction_flags (q16-q26)
- `hierarchy.py`: Build tree structure, identify parent-child relationships

**Critical**: NOT GPT-based, uses extraction flags

---

### src/timeline/
**Purpose**: Detect belief drift over time.

**Key Files**:
- `reporter.py`: Generate timeline reports
- `drift_detector.py`: Detect drift types (new, dropped, strengthening, weakening, reversal)

**Output**: BeliefDrift objects, timeline reports

---

### src/contrarian/
**Purpose**: Detect contradictions and opposing beliefs.

**Key Files**:
- `detector.py`: Identify contradictory belief pairs
- `opposition_scorer.py`: Calculate semantic opposition scores (parallel)
- `reversal_tracker.py`: Track belief reversals for same speaker

**Output**: Contradiction objects, contradiction reports

---

### src/models/
**Purpose**: Pydantic data models with validation.

**Key Files**:
- One file per model (episode.py, utterance.py, etc.)
- Strict validation rules
- Source linkage enforcement

**Critical**: All foreign keys validated, lists cannot be empty where required

---

### src/utils/
**Purpose**: Shared utilities for entire pipeline.

**Key Files**:
- `logger.py`: Structured logging with W&B integration
- `retry.py`: Exponential backoff retry decorators
- `validators.py`: Input validation functions
- `exceptions.py`: Custom exception classes
- `checkpoint.py`: Checkpoint save/load/recovery
- `quality_scorer.py`: Calculate episode quality scores
- `parallel.py`: ThreadPoolExecutor, rate limiting, token bucket
- `wandb_logger.py`: W&B metric logging, artifact upload

**Critical**: Used by all modules

---

## Configuration Files

### config.py
Central configuration for:
- Clustering (MIN_CLUSTER_SIZE)
- Checkpointing (enabled, directories, cleanup)
- Quality scoring (thresholds)
- Retry logic (max retries, backoff)
- API settings (timeouts, max tokens)
- Parallelization (workers, batch size, rate limits)
- W&B (project, entity, log frequency)

### logging_config.py
Logging configuration:
- Log levels per module
- File handlers (rotation, retention)
- Console handlers
- Log format (structured or plain)

### wandb_config.py
W&B initialization:
- Project and entity setup
- Run naming convention
- Metric definitions
- Artifact types

### .env.example
Environment variable template:
```
OPENAI_API_KEY=your_key_here
WANDB_API_KEY=your_key_here
WANDB_PROJECT=belief-engine
WANDB_ENTITY=your_username
```

---

## Data Directories

### data/input/
Store diarized transcript files here.

### data/output/
Pipeline outputs (matrices, ontologies, reports).

### data/registry/
Persistent global registries:
- `belief_registry.json`: Canonical beliefs, aliases, history
- `embeddings_cache.pkl`: Cached embeddings

### data/clusters/
Global cluster store:
- `global_clusters.json`: All clusters across episodes

### data/checkpoints/
Per-episode, per-phase checkpoints for recovery.

---

## Log Directory

### logs/
- `master.log`: All logs combined
- `ingestion.log`: Ingestion module logs
- `beliefs.log`: Belief extraction logs
- `clustering.log`: Clustering logs
- Per-module logs for debugging

**Rotation**: Daily rotation, 30-day retention

---

## Test Directory

### tests/
- Unit tests for each module
- Integration tests for full pipeline
- Fixtures in `conftest.py`
- Mock OpenAI API calls
- W&B offline mode for testing

**Run**: `pytest tests/`

---

## Examples Directory

### examples/
- `matthew_lacroix.txt`: Example transcript (3.5 hour podcast)
- `example_output/`: Expected outputs for testing
- `notebooks/`: Jupyter notebooks for analysis and visualization

---

## Entry Point

### main.py
CLI entry point:
```bash
python main.py --episode transcript.txt [options]
```

**Orchestrates**:
1. Initialize logging and W&B
2. Load configuration
3. Check for existing checkpoints
4. Run pipeline stages
5. Generate quality report
6. Upload W&B artifacts
7. Clean up and close

---

## Dependencies

### requirements.txt
```
openai>=1.0.0
pydantic>=2.0.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
sentence-transformers>=2.2.0
python-dotenv>=1.0.0
tenacity>=8.2.0
loguru>=0.7.0
wandb>=0.15.0
python-Levenshtein>=0.21.0
```

---

## Git Ignore

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Environment
.env

# Data (except examples)
data/*
!data/input/.gitkeep
!data/output/.gitkeep

# Logs
logs/
*.log

# Checkpoints
data/checkpoints/

# W&B
wandb/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

---

## Summary

This structure ensures:
1. **Clear separation of concerns**: Each module has a single responsibility
2. **Comprehensive documentation**: Full specs in `docs/`
3. **Production-ready**: Error handling, logging, checkpointing, testing
4. **Scalability**: Parallelization, rate limiting, caching
5. **Observability**: W&B integration, quality metrics, comprehensive logs
6. **Maintainability**: Modular design, type hints, Pydantic validation

