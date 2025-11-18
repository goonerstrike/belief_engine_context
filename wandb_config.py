"""
Weights & Biases configuration and initialization for Belief Engine.
"""
import wandb
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger
import config

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_wandb(
    episode_id: str,
    config_dict: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
    resume: bool = False
) -> Optional[wandb.sdk.wandb_run.Run]:
    """
    Initialize Weights & Biases run.
    
    Args:
        episode_id: Episode identifier
        config_dict: Configuration dictionary to log
        tags: List of tags for the run
        notes: Optional notes for the run
        resume: Whether to resume existing run
    
    Returns:
        W&B run object or None if W&B disabled
    """
    if not config.WANDB_ENABLED:
        logger.info("W&B logging disabled")
        return None
    
    try:
        # Generate run name
        run_name = config.get_wandb_run_name(episode_id)
        
        # Default tags
        default_tags = [episode_id, "belief-engine"]
        if tags:
            default_tags.extend(tags)
        
        # Initialize run
        run = wandb.init(
            project=config.WANDB_PROJECT,
            entity=config.WANDB_ENTITY,
            name=run_name,
            tags=default_tags,
            notes=notes,
            config=config_dict or get_default_config(),
            resume="allow" if resume else False
        )
        
        logger.info(f"W&B run initialized: {run_name}")
        logger.info(f"W&B dashboard: {run.get_url()}")
        
        return run
        
    except Exception as e:
        logger.error(f"Failed to initialize W&B: {e}")
        logger.warning("Continuing without W&B logging")
        return None

# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

def get_default_config() -> Dict[str, Any]:
    """Get default configuration to log to W&B."""
    return {
        # API
        "openai_model": config.OPENAI_MODEL,
        "openai_embedding_model": config.OPENAI_EMBEDDING_MODEL,
        "openai_max_tokens": config.OPENAI_MAX_TOKENS,
        "openai_temperature": config.OPENAI_TEMPERATURE,
        
        # Clustering
        "min_cluster_size": config.MIN_CLUSTER_SIZE,
        "clustering_distance_threshold": config.CLUSTERING_DISTANCE_THRESHOLD,
        "similarity_threshold_canonical": config.SIMILARITY_THRESHOLD_CANONICAL,
        
        # Parallelization
        "enable_parallel": config.ENABLE_PARALLEL,
        "max_workers": config.MAX_WORKERS,
        "batch_size": config.BATCH_SIZE,
        "embedding_workers": config.EMBEDDING_WORKERS,
        "api_rate_limit_rpm": config.API_RATE_LIMIT_RPM,
        "api_rate_limit_tpm": config.API_RATE_LIMIT_TPM,
        
        # Quality
        "quality_penalty_error": config.QUALITY_PENALTY_ERROR,
        "quality_penalty_retry": config.QUALITY_PENALTY_RETRY,
        "quality_penalty_malformed": config.QUALITY_PENALTY_MALFORMED,
        
        # Retry
        "max_retries": config.MAX_RETRIES,
        "retry_backoff_factor": config.RETRY_BACKOFF_FACTOR,
        
        # Drift
        "drift_conviction_threshold": config.DRIFT_CONVICTION_THRESHOLD,
        "drift_frequency_threshold": config.DRIFT_FREQUENCY_THRESHOLD,
        
        # Contrarian
        "opposition_score_threshold": config.OPPOSITION_SCORE_THRESHOLD,
    }

# ============================================================================
# METRIC DEFINITIONS
# ============================================================================

class MetricNames:
    """Centralized metric names for W&B logging."""
    
    # Pipeline Progress
    UTTERANCES_PARSED = "utterances_parsed"
    BELIEFS_EXTRACTED = "beliefs_extracted"
    CANONICAL_BELIEFS_CREATED = "canonical_beliefs_created"
    CLUSTERS_CREATED = "clusters_created"
    CONTRADICTIONS_DETECTED = "contradictions_detected"
    
    # API Metrics
    API_CALLS_TOTAL = "api_calls_total"
    API_TOKENS_USED = "api_tokens_used"
    API_COST_USD = "api_cost_usd"
    API_LATENCY_AVG = "api_latency_avg"
    API_ERRORS = "api_errors"
    API_RETRIES = "api_retries"
    RATE_LIMIT_HITS = "rate_limit_hits"
    
    # Quality Metrics
    QUALITY_SCORE = "quality_score"
    QUALITY_GRADE = "quality_grade"
    ERRORS_COUNT = "errors_count"
    MALFORMED_BELIEFS = "malformed_beliefs"
    REGISTRY_MISMATCHES = "registry_mismatches"
    
    # Performance Metrics
    PHASE_DURATION = "phase_duration_seconds"
    TOTAL_DURATION = "total_duration_seconds"
    THROUGHPUT = "throughput_beliefs_per_minute"
    WORKER_UTILIZATION = "parallel_worker_utilization"
    
    # Clustering Metrics
    CLUSTERS_TOTAL = "clusters_total"
    AVG_CLUSTER_SIZE = "avg_cluster_size"
    MICRO_CLUSTERS_FILTERED = "micro_clusters_filtered"
    
    # Timeline Metrics
    DRIFT_NEW = "drift_new"
    DRIFT_DROPPED = "drift_dropped"
    DRIFT_STRENGTHENING = "drift_strengthening"
    DRIFT_WEAKENING = "drift_weakening"
    DRIFT_REVERSAL = "drift_reversal"

# ============================================================================
# ARTIFACT TYPES
# ============================================================================

class ArtifactTypes:
    """Artifact type definitions for W&B."""
    
    CHECKPOINT = "checkpoint"
    MATRIX = "matrix"
    ONTOLOGY = "ontology"
    TIMELINE = "timeline"
    REPORT = "report"
    LOG = "log"
    VISUALIZATION = "visualization"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_metrics(metrics: Dict[str, Any], step: Optional[int] = None):
    """
    Log metrics to W&B.
    
    Args:
        metrics: Dictionary of metrics to log
        step: Optional step number
    """
    if not config.WANDB_ENABLED or not wandb.run:
        return
    
    try:
        wandb.log(metrics, step=step)
    except Exception as e:
        logger.error(f"Failed to log metrics to W&B: {e}")

def log_table(name: str, columns: List[str], data: List[List[Any]]):
    """
    Log a table to W&B.
    
    Args:
        name: Table name
        columns: Column names
        data: List of rows
    """
    if not config.WANDB_ENABLED or not wandb.run:
        return
    
    try:
        table = wandb.Table(columns=columns, data=data)
        wandb.log({name: table})
    except Exception as e:
        logger.error(f"Failed to log table to W&B: {e}")

def log_artifact(
    name: str,
    artifact_type: str,
    path: Path,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an artifact to W&B.
    
    Args:
        name: Artifact name
        artifact_type: Artifact type (use ArtifactTypes)
        path: Path to artifact file or directory
        description: Optional description
        metadata: Optional metadata dictionary
    """
    if not config.WANDB_ENABLED or not wandb.run:
        return
    
    try:
        artifact = wandb.Artifact(
            name=name,
            type=artifact_type,
            description=description,
            metadata=metadata
        )
        
        if path.is_dir():
            artifact.add_dir(str(path))
        else:
            artifact.add_file(str(path))
        
        wandb.log_artifact(artifact)
        logger.info(f"Uploaded artifact: {name} ({artifact_type})")
        
    except Exception as e:
        logger.error(f"Failed to log artifact to W&B: {e}")

def log_alert(title: str, text: str, level: str = "WARN"):
    """
    Log an alert to W&B.
    
    Args:
        title: Alert title
        text: Alert message
        level: Alert level (INFO, WARN, ERROR)
    """
    if not config.WANDB_ENABLED or not wandb.run:
        return
    
    try:
        wandb.alert(title=title, text=text, level=getattr(wandb.AlertLevel, level, wandb.AlertLevel.WARN))
    except Exception as e:
        logger.error(f"Failed to log alert to W&B: {e}")

def finish_wandb(exit_code: int = 0):
    """
    Finish W&B run.
    
    Args:
        exit_code: Exit code (0 for success, non-zero for failure)
    """
    if not config.WANDB_ENABLED or not wandb.run:
        return
    
    try:
        wandb.finish(exit_code=exit_code)
        logger.info("W&B run finished")
    except Exception as e:
        logger.error(f"Failed to finish W&B run: {e}")

# ============================================================================
# SUMMARY HELPERS
# ============================================================================

def update_summary(key: str, value: Any):
    """
    Update W&B run summary.
    
    Args:
        key: Summary key
        value: Summary value
    """
    if not config.WANDB_ENABLED or not wandb.run:
        return
    
    try:
        wandb.run.summary[key] = value
    except Exception as e:
        logger.error(f"Failed to update W&B summary: {e}")

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "initialize_wandb",
    "get_default_config",
    "MetricNames",
    "ArtifactTypes",
    "log_metrics",
    "log_table",
    "log_artifact",
    "log_alert",
    "finish_wandb",
    "update_summary"
]

