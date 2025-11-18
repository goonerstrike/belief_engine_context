# Belief Engine - Longitudinal Belief Extraction & Tracking System

## Overview

The Belief Engine is a production-ready Python system for extracting, canonicalizing, clustering, and tracking beliefs from diarized transcripts over time. It uses OpenAI's GPT-4 for extraction, maintains global registries for deduplication, implements parallel processing for performance, and tracks comprehensive metrics via Weights & Biases.

## Key Features

### Core Capabilities
- **Belief Extraction**: Extract atomic, declarative beliefs from diarized transcripts using GPT-4
- **Canonicalization**: Deduplicate and standardize belief phrasing
- **Global Clustering**: Group semantically similar beliefs across all episodes
- **Ontology Building**: Hierarchical belief structure with tier assignment (core → worldview → reasoning → surface)
- **Matrix Tracking**: Weighted episode × belief matrix for longitudinal analysis
- **Drift Detection**: Track belief changes (new, dropped, strengthening, weakening, reversal)
- **Contrarian Detection**: Identify contradictions within/across speakers

### Production Features
- **Checkpointing**: Resume from any pipeline stage on failure
- **Parallelization**: Multi-threaded processing with intelligent rate limiting
- **Quality Scoring**: Automated quality grading (A-F) for every episode
- **Error Handling**: Comprehensive error recovery and logging
- **W&B Integration**: Full experiment tracking, metrics, and artifact management
- **Source Linkage**: Complete traceability from ontology → clusters → beliefs → utterances

## Architecture

### Pipeline Stages
```
1. Ingestion          → Parse diarized transcripts
2. Utterance Split    → Create atomic utterances
3. Belief Extraction  → Extract beliefs (parallel, with retry)
4. Registry Lookup    → Match against existing beliefs
5. Canonicalization   → Standardize phrasing (parallel)
6. Clustering         → Global semantic clustering (parallel)
7. Ontology           → Build hierarchical structure
8. Matrix Building    → Create weighted tracking matrix
9. Timeline/Contrarian → Detect drift and contradictions
10. Quality Report    → Generate metrics and W&B artifacts
```

### Data Flow
```
Transcript → Episodes → Utterances → Beliefs → Canonical Beliefs → Clusters → Ontology
                ↓           ↓           ↓            ↓                ↓
          Source Linkage Chain (complete traceability)
```

## Installation

### Prerequisites
- Python 3.10+
- OpenAI API key
- Weights & Biases account (optional but recommended)

### Setup
```bash
# Clone repository
cd belief_engine_context

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys:
#   OPENAI_API_KEY=your_key_here
#   WANDB_API_KEY=your_key_here (optional)
```

## Quick Start

### Basic Usage
```bash
# Process a single episode
python main.py --episode matthew_lacroix.txt

# Resume from checkpoint
python main.py --episode matthew_lacroix.txt --resume

# Disable W&B logging
python main.py --episode matthew_lacroix.txt --no-wandb

# Custom parallelization
python main.py --episode matthew_lacroix.txt --workers 10 --batch-size 20

# Verbose logging
python main.py --episode matthew_lacroix.txt --verbose
```

### Input Format
Diarized transcript files should follow this format:
```
SPEAKER_A | 00:00:10 | 00:00:25 | Science is the objective search for truth.
SPEAKER_B | 00:00:26 | 00:00:45 | Ancient civilizations had advanced knowledge.
SPEAKER_A | 00:00:46 | 00:01:05 | The mainstream narrative is built on sand.
```

### Output
The pipeline generates:
- **Checkpoints**: `data/checkpoints/episode_XXX/` (per-phase JSON files)
- **Belief Matrix**: `data/output/belief_matrix.csv` and `.json`
- **Ontology**: `data/output/ontology.json` (hierarchical structure)
- **Timeline Report**: `data/output/timeline_report.json`
- **Contradiction Report**: `data/output/contradictions.json`
- **Quality Report**: `data/checkpoints/episode_XXX/quality_report.json`
- **Logs**: `logs/` (per-module logs)
- **W&B Artifacts**: Uploaded to your W&B project

## Configuration

### config.py Settings
```python
# Clustering
MIN_CLUSTER_SIZE = 3  # Minimum beliefs per cluster

# Parallelization
ENABLE_PARALLEL = True
MAX_WORKERS = 5       # Parallel workers for belief extraction
BATCH_SIZE = 10       # Utterances per batch
EMBEDDING_WORKERS = 3 # Parallel workers for embeddings

# API Rate Limiting
API_RATE_LIMIT_RPM = 3500   # Requests per minute
API_RATE_LIMIT_TPM = 90000  # Tokens per minute

# Quality Scoring
QUALITY_THRESHOLDS = {"A": 90, "B": 80, "C": 70, "D": 60}

# W&B
WANDB_ENABLED = True
WANDB_PROJECT = "belief-engine"
WANDB_LOG_FREQUENCY = 10  # Log every N beliefs
```

## Key Concepts

### Beliefs
**Atomic, declarative statements** extracted from utterances.

Example:
- Raw utterance: "I think Bitcoin protects savings from government monetary abuse."
- Extracted belief: "Bitcoin protects savings from inflation."

### Canonical Beliefs
**Standardized, deduplicated** belief representations.

Example:
- "Bitcoin protects savings from inflation."
- "BTC prevents inflation from eroding value."
- "Bitcoin stops governments from stealing via inflation."

→ Canonical: "Bitcoin protects against government monetary abuse"

### Clusters
**Groups of semantically similar** canonical beliefs.

Example cluster:
```
Cluster 12: "Government Monetary Control"
- Bitcoin protects against government monetary abuse
- Central banks control money supply
- Fiat currency loses value through inflation
- Governments use inflation as hidden tax
```

### Ontology Tiers (Rules-Based)
Beliefs are assigned to tiers based on extraction flags (q16-q26):
- **Core**: First principles, ontology (q16, q20)
- **Worldview**: Worldview, moral framework (q17, q18)
- **Reasoning**: Reasoning patterns, assumptions (q21, q22)
- **Surface**: Opinions, factual claims (q23, q24)

### Belief Matrix (Weighted)
Episode × Canonical Belief matrix tracking:
- **conviction_avg**: Mean confidence [0.0, 1.0]
- **frequency**: Count of mentions
- **stability_score**: Consistency [0.0, 1.0]
- **presence_flag**: Boolean (present/absent)

### Drift Types
- **new**: First appearance in episode
- **dropped**: Previously present, now absent
- **strengthening**: Conviction/frequency increased
- **weakening**: Conviction/frequency decreased
- **reversal**: Speaker contradicts previous belief

## Weights & Biases Integration

### Metrics Tracked
- **Pipeline Progress**: utterances_parsed, beliefs_extracted, clusters_created
- **API Metrics**: api_calls, api_tokens_used, api_cost_usd, api_latency
- **Quality Metrics**: quality_score, errors_count, malformed_beliefs
- **Performance**: throughput_beliefs_per_minute, parallel_worker_utilization
- **Clustering**: clusters_total, avg_cluster_size, micro_clusters_filtered
- **Timeline**: drift_new, drift_dropped, drift_strengthening, drift_weakening, drift_reversal
- **Contradictions**: contradictions_detected

### Artifacts
- Checkpoints (versioned)
- Belief Matrix (CSV/JSON)
- Ontology (JSON)
- Quality Report (JSON)
- Logs
- Visualizations

### Dashboard
Access your W&B dashboard to:
- Compare runs across episodes
- Track API costs over time
- Monitor quality trends
- Visualize belief networks
- Analyze drift patterns

## Error Handling & Recovery

### Automatic Recovery
The pipeline implements comprehensive error handling:
- **API timeouts**: Retry with exponential backoff (3 attempts)
- **Rate limits**: Automatic backoff and retry
- **Malformed data**: Skip and continue with logging
- **Pipeline failure**: Resume from last checkpoint

### Quality Scoring
Every episode receives a quality score (0-100) and grade (A-F):
- **A (90-100)**: Excellent - minimal errors
- **B (80-89)**: Good - few errors
- **C (70-79)**: Acceptable - some issues
- **D (60-69)**: Poor - many issues
- **F (0-59)**: Failing - critical issues

Quality factors:
- Parsing errors
- API failures and retries
- Malformed beliefs
- Registry mismatches

### Checkpointing
Checkpoints are saved after each major stage:
1. `utterances.json` (after utterance split)
2. `beliefs_raw.json` (after belief extraction)
3. `canonical_beliefs.json` (after canonicalization)
4. `clusters_updated.json` (after clustering)

To resume: `python main.py --episode XXX --resume`

## Performance Optimization

### Parallelization
The pipeline uses multi-threading for I/O-bound tasks:
- **Belief Extraction**: Process batches in parallel (MAX_WORKERS=5)
- **Embeddings**: Generate embeddings in parallel (EMBEDDING_WORKERS=3)
- **Canonicalization**: Parallel fuzzy matching
- **Contrarian Detection**: Parallel opposition scoring

### Rate Limiting
Intelligent rate limiting prevents API errors:
- Token bucket algorithm
- Tracks RPM (requests/minute) and TPM (tokens/minute)
- Automatic backoff when approaching limits
- Graceful handling of 429 errors

### Caching
- **Embeddings**: Cached to avoid redundant API calls
- **Registry**: Persisted to disk for fast lookup

## Use Cases

### 1. Podcast Analysis
Track how a podcast host's beliefs evolve across episodes.

### 2. Interview Series
Compare beliefs across multiple guests on similar topics.

### 3. Debate Analysis
Identify contradictions and opposing viewpoints between speakers.

### 4. Longitudinal Studies
Analyze belief drift over months/years of content.

### 5. Worldview Mapping
Build comprehensive belief hierarchies for individuals or groups.

## Advanced Features

### Multi-Episode Processing
Process multiple episodes in parallel:
```bash
python main.py --episodes episode_001.txt episode_002.txt --multi-episode-workers 2
```

### Custom Extraction Flags
Define custom extraction flags for your domain:
```python
# In config.py
CUSTOM_EXTRACTION_FLAGS = {
    "q27_political_stance": "Political orientation",
    "q28_economic_model": "Economic model preference"
}
```

### Export Options
```bash
# Export matrix to different formats
python export_matrix.py --format csv --output belief_matrix.csv
python export_matrix.py --format json --output belief_matrix.json

# Export ontology visualization
python visualize_ontology.py --output ontology.html
```

## Troubleshooting

### Common Issues

**API Rate Limits**
- Reduce `MAX_WORKERS` and `BATCH_SIZE`
- Increase `API_RATE_LIMIT_RPM` if you have higher quota
- Check W&B metrics for `rate_limit_hits`

**Low Quality Score**
- Check `quality_report.json` for error breakdown
- Review logs in `logs/` directory
- Inspect malformed input data
- Verify transcript format

**Checkpoint Corruption**
- Delete corrupted checkpoint: `rm data/checkpoints/episode_XXX/[phase].json`
- Re-run pipeline (will rebuild from previous checkpoint)

**Memory Issues**
- Reduce `MAX_WORKERS`
- Process episodes one at a time
- Clear old checkpoints: `python cleanup_checkpoints.py --days 30`

### Logging Levels
```bash
# Debug mode (verbose)
python main.py --verbose

# Custom log file
python main.py --log-file custom_log.txt

# Disable console logging
python main.py --quiet
```

## Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_extraction.py

# Test with W&B offline mode
WANDB_MODE=offline pytest tests/
```

### Project Structure
```
belief_engine_context/
├── src/
│   ├── ingestion/
│   ├── utterance/
│   ├── beliefs/
│   ├── canonicalization/
│   ├── clustering/
│   ├── matrix/
│   ├── ontology/
│   ├── timeline/
│   ├── contrarian/
│   ├── models/
│   └── utils/
├── tests/
├── docs/
├── data/
├── logs/
├── examples/
└── main.py
```

## Contributing

### Code Style
- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Write unit tests for new features

### Pull Request Process
1. Create feature branch
2. Add tests
3. Update documentation
4. Ensure all tests pass
5. Submit PR with description

## License

MIT License - see LICENSE file

## Citation

If you use this system in your research, please cite:
```bibtex
@software{belief_engine_2025,
  title={Belief Engine: Longitudinal Belief Extraction and Tracking},
  author={Your Name},
  year={2025},
  url={https://github.com/yourusername/belief_engine_context}
}
```

## Support

- **Issues**: GitHub Issues
- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory

## Acknowledgments

Built with:
- OpenAI API (GPT-4, Embeddings)
- Weights & Biases (Experiment tracking)
- Pydantic (Data validation)
- scikit-learn (Clustering)

---

**Version**: 1.0.0
**Last Updated**: 2025-01-15

