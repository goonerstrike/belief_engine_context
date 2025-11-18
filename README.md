# Belief Engine Context

A production-ready Python system for extracting, canonicalizing, clustering, and tracking beliefs from diarized transcripts over time.

## Features

✅ **Belief Extraction** - Extract atomic, declarative beliefs using OpenAI GPT-4  
✅ **Parallelization** - Multi-threaded processing with intelligent rate limiting  
✅ **Checkpointing** - Resume from any failure point  
✅ **Quality Scoring** - Automatic A-F grading for every episode  
✅ **W&B Integration** - Full experiment tracking and metrics  
✅ **Error Handling** - Comprehensive error recovery and logging  
✅ **Source Linkage** - Complete traceability from beliefs → utterances → episodes  

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Run the Pipeline

```bash
# Process the example transcript
python main.py --episode matthew_lacroix.txt

# With verbose logging
python main.py --episode matthew_lacroix.txt --verbose

# Disable W&B
python main.py --episode matthew_lacroix.txt --no-wandb

# Custom parallelization
python main.py --episode matthew_lacroix.txt --workers 10 --batch-size 20
```

### Expected Output

```
================================================================================
BELIEF ENGINE - Starting Pipeline
Episode ID: matthew_lacroix
Transcript: matthew_lacroix.txt
================================================================================
STAGE 1: Ingestion
INFO: Ingestion complete | utterances=1107
STAGE 2: Utterance Splitting
INFO: Split into 1107 atomic utterances
STAGE 3: Belief Extraction
INFO: Extracted 45 beliefs total
STAGE 4: Canonicalization
INFO: Created 45 canonical beliefs
================================================================================
PIPELINE COMPLETE
Episode: matthew_lacroix
Utterances: 1107
Beliefs Extracted: 45
Canonical Beliefs: 45
Quality Score: 95.0
Quality Grade: A
Execution Time: 124.5s
================================================================================
```

## Input Format

Diarized transcripts should follow this format:

```
SPEAKER_A | 00:00:10 | 00:00:25 | Science is the objective search for truth.
SPEAKER_B | 00:00:26 | 00:00:45 | Ancient civilizations had advanced knowledge.
```

## Output Files

```
data/
├── checkpoints/matthew_lacroix/
│   ├── utterances.json           # Checkpoint after utterance split
│   ├── beliefs_raw.json          # Checkpoint after extraction
│   ├── canonical_beliefs.json    # Checkpoint after canonicalization
│   └── quality_report.json       # Quality metrics
├── registry/
│   └── belief_registry.json      # Global belief registry
└── output/
    └── (future: matrices, ontologies, reports)
```

## Configuration

Edit `config.py` to customize:

```python
# API Settings
OPENAI_MODEL = "gpt-4"
OPENAI_MAX_TOKENS = 4000

# Parallelization
MAX_WORKERS = 5
BATCH_SIZE = 10
API_RATE_LIMIT_RPM = 3500

# Quality Scoring
QUALITY_THRESHOLDS = {"A": 90, "B": 80, "C": 70, "D": 60}

# Clustering (for future expansion)
MIN_CLUSTER_SIZE = 3
```

## Project Structure

```
belief_engine_context/
├── main.py                  # CLI entry point
├── config.py                # Configuration
├── logging_config.py        # Logging setup
├── wandb_config.py          # W&B integration
├── requirements.txt         # Dependencies
├── src/
│   ├── ingestion/           # Transcript parsing
│   ├── utterance/           # Utterance splitting
│   ├── beliefs/             # Belief extraction & registry
│   ├── models/              # Pydantic data models
│   └── utils/               # Utilities (logging, retry, checkpoints, etc.)
├── docs/                    # Comprehensive documentation
├── data/                    # Data directories
└── logs/                    # Log files
```

## Documentation

Comprehensive documentation available in `docs/`:

- **schema.md** - Complete data model specifications
- **pipeline.md** - Pipeline architecture and stages
- **README_belief_engine.md** - Full user guide
- **repo_structure.md** - Code organization

## Architecture Highlights

### Robust Error Handling
- Graceful degradation on errors
- Automatic retries with exponential backoff
- Detailed error logging and tracking
- Quality scoring based on error counts

### Checkpointing System
- Save progress after each major stage
- Resume from last successful checkpoint
- Atomic writes prevent corruption
- Automatic cleanup of old checkpoints

### Parallelization & Rate Limiting
- Multi-threaded belief extraction
- Token bucket rate limiter for API calls
- Respects RPM and TPM limits
- Worker utilization tracking

### Quality Metrics
- Automatic quality scoring (0-100)
- Grade assignment (A-F)
- Tracks errors, retries, malformed data
- Helps identify problematic transcripts

### W&B Integration
- Comprehensive metric tracking
- Artifact versioning (checkpoints, reports)
- Custom dashboards
- Alert system for errors

## Development Status

### ✅ Completed
- Core infrastructure (logging, error handling, checkpointing)
- Data models with validation
- Ingestion and parsing
- Utterance splitting
- Belief extraction with OpenAI
- Canonicalization and registry
- Quality scoring
- W&B integration
- CLI interface

### 🚧 Future Enhancements
- Full clustering implementation
- Ontology hierarchy building
- Belief matrix generation
- Timeline drift detection
- Contrarian belief detection
- Comprehensive test suite
- Advanced canonicalization (fuzzy matching, LLM fallback)

## Example Usage

```python
# Programmatic usage
from src.ingestion import TranscriptParser
from src.beliefs import BeliefExtractor

# Parse transcript
parser = TranscriptParser()
episode, utterances = parser.parse("transcript.txt", "episode_001")

# Extract beliefs
extractor = BeliefExtractor()
beliefs = extractor.extract(utterances)

print(f"Extracted {len(beliefs)} beliefs")
```

## Troubleshooting

### API Rate Limits
Reduce `MAX_WORKERS` and `BATCH_SIZE` in `config.py`

### Low Quality Score
Check `data/checkpoints/EPISODE_ID/quality_report.json` for error breakdown

### Checkpoint Issues
Delete corrupted checkpoint: `rm data/checkpoints/EPISODE_ID/[phase].json`

## License

MIT License - See LICENSE file

## Support

- Documentation: `docs/` directory
- Issues: GitHub Issues
- Example: `matthew_lacroix.txt`

---

**Built with:** OpenAI API, Pydantic, W&B, Loguru, scikit-learn

**Version:** 1.0.0
