"""
W&B logging helper utilities for Belief Engine.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import wandb
from loguru import logger
import config
from wandb_config import MetricNames, ArtifactTypes, log_metrics, log_table, log_artifact, update_summary

# ============================================================================
# WANDB LOGGER
# ============================================================================

class WandBLogger:
    """
    Centralized W&B logging for pipeline.
    
    Usage:
        wb_logger = WandBLogger()
        wb_logger.log_utterances_parsed(count=150)
        wb_logger.log_api_call(tokens=200, cost=0.01, latency=1.5)
    """
    
    def __init__(self):
        """Initialize W&B logger."""
        self.enabled = config.WANDB_ENABLED and wandb.run is not None
        self.log_counter = 0
        
        if not self.enabled:
            logger.info("W&B logging disabled or run not initialized")
    
    def _should_log(self) -> bool:
        """Check if should log (based on frequency)."""
        self.log_counter += 1
        return self.log_counter % config.WANDB_LOG_FREQUENCY == 0
    
    # ========================================================================
    # PIPELINE PROGRESS
    # ========================================================================
    
    def log_utterances_parsed(self, count: int):
        """Log utterances parsed count."""
        if self.enabled:
            log_metrics({MetricNames.UTTERANCES_PARSED: count})
    
    def log_beliefs_extracted(self, count: int, incremental: bool = False):
        """Log beliefs extracted count."""
        if self.enabled and (incremental is False or self._should_log()):
            log_metrics({MetricNames.BELIEFS_EXTRACTED: count})
    
    def log_canonical_beliefs_created(self, count: int):
        """Log canonical beliefs created count."""
        if self.enabled:
            log_metrics({MetricNames.CANONICAL_BELIEFS_CREATED: count})
    
    def log_clusters_created(self, count: int):
        """Log clusters created count."""
        if self.enabled:
            log_metrics({MetricNames.CLUSTERS_CREATED: count})
    
    def log_contradictions_detected(self, count: int):
        """Log contradictions detected count."""
        if self.enabled:
            log_metrics({MetricNames.CONTRADICTIONS_DETECTED: count})
    
    # ========================================================================
    # API METRICS
    # ========================================================================
    
    def log_api_call(
        self,
        tokens: int = 0,
        cost: float = 0.0,
        latency: float = 0.0,
        success: bool = True
    ):
        """
        Log API call metrics.
        
        Args:
            tokens: Tokens used
            cost: Cost in USD
            latency: Response time in seconds
            success: Whether call succeeded
        """
        if not self.enabled:
            return
        
        metrics = {
            MetricNames.API_CALLS_TOTAL: 1,
            MetricNames.API_TOKENS_USED: tokens,
            MetricNames.API_COST_USD: cost,
            MetricNames.API_LATENCY_AVG: latency
        }
        
        if not success:
            metrics[MetricNames.API_ERRORS] = 1
        
        log_metrics(metrics)
    
    def log_api_retry(self):
        """Log API retry."""
        if self.enabled:
            log_metrics({MetricNames.API_RETRIES: 1})
    
    def log_rate_limit_hit(self):
        """Log rate limit hit."""
        if self.enabled:
            log_metrics({MetricNames.RATE_LIMIT_HITS: 1})
            logger.warning("Rate limit hit logged to W&B")
    
    # ========================================================================
    # QUALITY METRICS
    # ========================================================================
    
    def log_quality_metrics(
        self,
        score: float,
        grade: str,
        errors_count: int,
        malformed_beliefs: int,
        registry_mismatches: int
    ):
        """Log quality metrics."""
        if self.enabled:
            log_metrics({
                MetricNames.QUALITY_SCORE: score,
                MetricNames.QUALITY_GRADE: grade,
                MetricNames.ERRORS_COUNT: errors_count,
                MetricNames.MALFORMED_BELIEFS: malformed_beliefs,
                MetricNames.REGISTRY_MISMATCHES: registry_mismatches
            })
            
            # Also update summary
            update_summary("quality_score", score)
            update_summary("quality_grade", grade)
    
    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================
    
    def log_phase_duration(self, phase: str, duration: float):
        """Log phase duration."""
        if self.enabled:
            log_metrics({f"{MetricNames.PHASE_DURATION}_{phase}": duration})
    
    def log_throughput(self, beliefs_per_minute: float):
        """Log throughput."""
        if self.enabled:
            log_metrics({MetricNames.THROUGHPUT: beliefs_per_minute})
    
    def log_worker_utilization(self, utilization: float):
        """Log worker utilization."""
        if self.enabled:
            log_metrics({MetricNames.WORKER_UTILIZATION: utilization})
    
    # ========================================================================
    # CLUSTERING METRICS
    # ========================================================================
    
    def log_clustering_metrics(
        self,
        clusters_total: int,
        avg_cluster_size: float,
        micro_clusters_filtered: int
    ):
        """Log clustering metrics."""
        if self.enabled:
            log_metrics({
                MetricNames.CLUSTERS_TOTAL: clusters_total,
                MetricNames.AVG_CLUSTER_SIZE: avg_cluster_size,
                MetricNames.MICRO_CLUSTERS_FILTERED: micro_clusters_filtered
            })
    
    def log_ontology_tiers(self, tier_counts: Dict[str, int]):
        """
        Log ontology tier distribution.
        
        Args:
            tier_counts: Dictionary of tier -> count
        """
        if self.enabled:
            # Log as individual metrics
            for tier, count in tier_counts.items():
                log_metrics({f"ontology_tier_{tier}": count})
    
    # ========================================================================
    # TIMELINE METRICS
    # ========================================================================
    
    def log_drift_metrics(
        self,
        new: int = 0,
        dropped: int = 0,
        strengthening: int = 0,
        weakening: int = 0,
        reversal: int = 0
    ):
        """Log drift detection metrics."""
        if self.enabled:
            log_metrics({
                MetricNames.DRIFT_NEW: new,
                MetricNames.DRIFT_DROPPED: dropped,
                MetricNames.DRIFT_STRENGTHENING: strengthening,
                MetricNames.DRIFT_WEAKENING: weakening,
                MetricNames.DRIFT_REVERSAL: reversal
            })
    
    # ========================================================================
    # TABLES
    # ========================================================================
    
    def log_beliefs_table(self, beliefs: List[Dict[str, Any]]):
        """
        Log beliefs as W&B table.
        
        Args:
            beliefs: List of belief dictionaries
        """
        if not self.enabled or not beliefs:
            return
        
        columns = ["id", "belief_text", "confidence", "speaker", "episode_id"]
        data = [
            [
                b.get("id", ""),
                b.get("belief_text", ""),
                b.get("confidence", 0.0),
                b.get("speaker", ""),
                b.get("episode_id", "")
            ]
            for b in beliefs[:100]  # Limit to 100 for performance
        ]
        
        log_table("beliefs", columns, data)
    
    def log_contradictions_table(self, contradictions: List[Dict[str, Any]]):
        """
        Log contradictions as W&B table.
        
        Args:
            contradictions: List of contradiction dictionaries
        """
        if not self.enabled or not contradictions:
            return
        
        columns = ["belief_a", "belief_b", "opposition_score", "type", "is_reversal"]
        data = [
            [
                c.get("belief_a_text", ""),
                c.get("belief_b_text", ""),
                c.get("opposition_score", 0.0),
                c.get("type", ""),
                c.get("is_reversal", False)
            ]
            for c in contradictions[:50]  # Limit for performance
        ]
        
        log_table("contradictions", columns, data)
    
    # ========================================================================
    # ARTIFACTS
    # ========================================================================
    
    def upload_checkpoint(self, episode_id: str, phase: str):
        """
        Upload checkpoint as artifact.
        
        Args:
            episode_id: Episode identifier
            phase: Pipeline phase
        """
        if not self.enabled:
            return
        
        checkpoint_file = config.CHECKPOINTS_DIR / episode_id / f"{phase}.json"
        if checkpoint_file.exists():
            log_artifact(
                name=f"checkpoint_{episode_id}_{phase}",
                artifact_type=ArtifactTypes.CHECKPOINT,
                path=checkpoint_file,
                description=f"Checkpoint for {episode_id} at phase {phase}"
            )
    
    def upload_matrix(self, matrix_path: Path):
        """Upload belief matrix as artifact."""
        if self.enabled and matrix_path.exists():
            log_artifact(
                name="belief_matrix",
                artifact_type=ArtifactTypes.MATRIX,
                path=matrix_path,
                description="Weighted episode × belief matrix"
            )
    
    def upload_ontology(self, ontology_path: Path):
        """Upload ontology as artifact."""
        if self.enabled and ontology_path.exists():
            log_artifact(
                name="ontology",
                artifact_type=ArtifactTypes.ONTOLOGY,
                path=ontology_path,
                description="Hierarchical belief ontology"
            )
    
    def upload_quality_report(self, report_path: Path):
        """Upload quality report as artifact."""
        if self.enabled and report_path.exists():
            log_artifact(
                name="quality_report",
                artifact_type=ArtifactTypes.REPORT,
                path=report_path,
                description="Episode quality report"
            )
    
    def upload_logs(self, log_dir: Path):
        """Upload logs as artifact."""
        if self.enabled and log_dir.exists():
            log_artifact(
                name="logs",
                artifact_type=ArtifactTypes.LOG,
                path=log_dir,
                description="Pipeline execution logs"
            )

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "WandBLogger",
]

