"""
Central configuration for Belief Engine pipeline.
"""
import os
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
REGISTRY_DIR = DATA_DIR / "registry"
CLUSTERS_DIR = DATA_DIR / "clusters"
CHECKPOINTS_DIR = DATA_DIR / "checkpoints"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for dir_path in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, REGISTRY_DIR, CLUSTERS_DIR, CHECKPOINTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============================================================================
# API CONFIGURATION
# ============================================================================

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", None)
OPENAI_MODEL = "gpt-4"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_MAX_TOKENS = 4000
OPENAI_TIMEOUT = 30
OPENAI_TEMPERATURE = 0.1  # Low temperature for consistent extractions

# ============================================================================
# CLUSTERING CONFIGURATION
# ============================================================================

MIN_CLUSTER_SIZE = 3  # Minimum beliefs per cluster to prevent micro-clusters
CLUSTERING_DISTANCE_THRESHOLD = 0.3  # Cosine distance threshold for clustering
CLUSTERING_METHOD = "hierarchical"  # "hierarchical" or "hdbscan"
SIMILARITY_THRESHOLD_CANONICAL = 0.85  # Threshold for matching to existing canonical belief

# ============================================================================
# CHECKPOINTING CONFIGURATION
# ============================================================================

CHECKPOINT_ENABLED = True
CHECKPOINT_CLEANUP_DAYS = 30  # Clean checkpoints older than N days

# Checkpoint phases
CHECKPOINT_PHASES = [
    "utterances",
    "beliefs_raw",
    "canonical_beliefs",
    "clusters_updated"
]

# ============================================================================
# QUALITY SCORING CONFIGURATION
# ============================================================================

QUALITY_THRESHOLDS: Dict[str, int] = {
    "A": 90,  # Excellent
    "B": 80,  # Good
    "C": 70,  # Acceptable
    "D": 60,  # Poor
    # < 60 = F (Failing)
}

# Quality score penalties
QUALITY_PENALTY_ERROR = 2.0          # Points deducted per error
QUALITY_PENALTY_RETRY = 0.5          # Points deducted per retry
QUALITY_PENALTY_MALFORMED = 1.0      # Points deducted per malformed belief
QUALITY_PENALTY_MISMATCH = 0.5       # Points deducted per registry mismatch

# ============================================================================
# RETRY CONFIGURATION
# ============================================================================

MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # Exponential backoff: wait = RETRY_BACKOFF_FACTOR ** attempt
RETRY_MAX_WAIT = 60       # Maximum wait time in seconds

# ============================================================================
# PARALLELIZATION CONFIGURATION
# ============================================================================

ENABLE_PARALLEL = os.getenv("ENABLE_PARALLEL", "True").lower() == "true"
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "5"))          # Parallel workers for belief extraction
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))           # Utterances per batch for API calls
EMBEDDING_WORKERS = 3                                      # Parallel workers for embeddings
MULTI_EPISODE_WORKERS = 2                                  # Process multiple episodes in parallel

# Rate limiting (OpenAI API limits - adjust based on your tier)
API_RATE_LIMIT_RPM = 3500   # Requests per minute
API_RATE_LIMIT_TPM = 90000  # Tokens per minute

# ============================================================================
# WEIGHTS & BIASES CONFIGURATION
# ============================================================================

WANDB_ENABLED = os.getenv("WANDB_ENABLED", "True").lower() == "true"
WANDB_PROJECT = os.getenv("WANDB_PROJECT", "belief-engine")
WANDB_ENTITY = os.getenv("WANDB_ENTITY", None)  # Your username or team
WANDB_LOG_FREQUENCY = 10  # Log metrics every N beliefs

# W&B run naming
def get_wandb_run_name(episode_id: str) -> str:
    """Generate W&B run name."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"episode_{episode_id}_{timestamp}"

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
LOG_ROTATION = "1 day"  # Rotate logs daily
LOG_RETENTION = "30 days"  # Keep logs for 30 days

# ============================================================================
# EXTRACTION FLAGS (q16-q26)
# ============================================================================

EXTRACTION_FLAGS = {
    "q16_first_principles": "Core belief (first principles)",
    "q17_worldview": "Worldview belief",
    "q18_moral_framework": "Moral/ethical framework",
    "q19_epistemology": "How knowledge is acquired",
    "q20_ontology": "Nature of reality",
    "q21_reasoning_pattern": "Reasoning/logic pattern",
    "q22_assumption": "Underlying assumption",
    "q23_surface_opinion": "Surface-level opinion",
    "q24_factual_claim": "Factual claim",
    "q25_prediction": "Future prediction",
    "q26_value_judgment": "Value judgment"
}

# Tier assignment rules (based on extraction flags)
TIER_ASSIGNMENT_RULES = {
    "core": ["q16_first_principles", "q20_ontology"],
    "worldview": ["q17_worldview", "q18_moral_framework", "q19_epistemology"],
    "reasoning": ["q21_reasoning_pattern", "q22_assumption"],
    "surface": ["q23_surface_opinion", "q24_factual_claim", "q25_prediction", "q26_value_judgment"]
}

# ============================================================================
# DRIFT DETECTION CONFIGURATION
# ============================================================================

DRIFT_CONVICTION_THRESHOLD = 0.15  # Minimum change in conviction to detect strengthening/weakening
DRIFT_FREQUENCY_THRESHOLD = 2      # Minimum change in frequency to detect strengthening/weakening

# ============================================================================
# CONTRARIAN DETECTION CONFIGURATION
# ============================================================================

OPPOSITION_SCORE_THRESHOLD = 0.7   # Minimum opposition score to classify as contradiction
CONTRARIAN_USE_LLM_VERIFICATION = True  # Use LLM to verify ambiguous cases

# ============================================================================
# AUDIO LINKING CONFIGURATION
# ============================================================================

AUDIO_URI_FORMAT = "{filename}#t={timestamp}"  # Format: file.mp3#t=734
AUDIO_BASE_URL = None  # Optional: Base URL for audio files (e.g., "s3://bucket/")

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Validate configuration settings."""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not set in environment variables")
    
    if WANDB_ENABLED and not os.getenv("WANDB_API_KEY"):
        errors.append("WANDB_ENABLED is True but WANDB_API_KEY is not set")
    
    if MIN_CLUSTER_SIZE < 1:
        errors.append("MIN_CLUSTER_SIZE must be >= 1")
    
    if MAX_WORKERS < 1:
        errors.append("MAX_WORKERS must be >= 1")
    
    if BATCH_SIZE < 1:
        errors.append("BATCH_SIZE must be >= 1")
    
    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Paths
    "PROJECT_ROOT", "DATA_DIR", "INPUT_DIR", "OUTPUT_DIR", "REGISTRY_DIR",
    "CLUSTERS_DIR", "CHECKPOINTS_DIR", "LOGS_DIR",
    
    # API
    "OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_EMBEDDING_MODEL",
    "OPENAI_MAX_TOKENS", "OPENAI_TIMEOUT", "OPENAI_TEMPERATURE",
    
    # Clustering
    "MIN_CLUSTER_SIZE", "CLUSTERING_DISTANCE_THRESHOLD",
    "SIMILARITY_THRESHOLD_CANONICAL",
    
    # Checkpointing
    "CHECKPOINT_ENABLED", "CHECKPOINT_PHASES", "CHECKPOINT_CLEANUP_DAYS",
    
    # Quality
    "QUALITY_THRESHOLDS", "QUALITY_PENALTY_ERROR", "QUALITY_PENALTY_RETRY",
    "QUALITY_PENALTY_MALFORMED", "QUALITY_PENALTY_MISMATCH",
    
    # Retry
    "MAX_RETRIES", "RETRY_BACKOFF_FACTOR", "RETRY_MAX_WAIT",
    
    # Parallelization
    "ENABLE_PARALLEL", "MAX_WORKERS", "BATCH_SIZE", "EMBEDDING_WORKERS",
    "MULTI_EPISODE_WORKERS", "API_RATE_LIMIT_RPM", "API_RATE_LIMIT_TPM",
    
    # W&B
    "WANDB_ENABLED", "WANDB_PROJECT", "WANDB_ENTITY",
    "WANDB_LOG_FREQUENCY", "get_wandb_run_name",
    
    # Logging
    "LOG_LEVEL", "LOG_TO_FILE", "LOG_TO_CONSOLE",
    "LOG_ROTATION", "LOG_RETENTION",
    
    # Extraction
    "EXTRACTION_FLAGS", "TIER_ASSIGNMENT_RULES",
    
    # Drift
    "DRIFT_CONVICTION_THRESHOLD", "DRIFT_FREQUENCY_THRESHOLD",
    
    # Contrarian
    "OPPOSITION_SCORE_THRESHOLD", "CONTRARIAN_USE_LLM_VERIFICATION",
    
    # Audio
    "AUDIO_URI_FORMAT", "AUDIO_BASE_URL",
    
    # Validation
    "validate_config"
]

