"""
Quality scoring system for episode processing runs.
"""
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger
import config

# ============================================================================
# QUALITY METRICS
# ============================================================================

@dataclass
class QualityMetrics:
    """Track quality metrics during pipeline execution."""
    
    episode_id: str
    
    # Error counts
    errors_count: int = 0
    parsing_errors: List[str] = field(default_factory=list)
    api_errors: List[str] = field(default_factory=list)
    
    # Retry counts
    retries_count: int = 0
    
    # Malformed data counts
    malformed_beliefs_count: int = 0
    
    # Registry issues
    registry_mismatches_count: int = 0
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    # Timing
    execution_time_seconds: float = 0.0
    
    # Timestamp
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_parsing_error(self, error: str):
        """Add a parsing error."""
        self.parsing_errors.append(error)
        self.errors_count += 1
        logger.warning(f"Parsing error recorded: {error}")
    
    def add_api_error(self, error: str):
        """Add an API error."""
        self.api_errors.append(error)
        self.errors_count += 1
        logger.warning(f"API error recorded: {error}")
    
    def add_retry(self):
        """Increment retry count."""
        self.retries_count += 1
    
    def add_malformed_belief(self):
        """Increment malformed belief count."""
        self.malformed_beliefs_count += 1
    
    def add_registry_mismatch(self):
        """Increment registry mismatch count."""
        self.registry_mismatches_count += 1
    
    def add_warning(self, warning: str):
        """Add a warning."""
        self.warnings.append(warning)
        logger.info(f"Warning recorded: {warning}")

# ============================================================================
# QUALITY SCORER
# ============================================================================

class QualityScorer:
    """
    Calculate quality score for an episode.
    
    Usage:
        scorer = QualityScorer(episode_id="episode_001")
        scorer.metrics.add_parsing_error("Invalid timestamp")
        scorer.metrics.add_retry()
        report = scorer.generate_report()
        print(f"Quality: {report['quality_grade']}")
    """
    
    def __init__(self, episode_id: str):
        """
        Initialize quality scorer.
        
        Args:
            episode_id: Episode identifier
        """
        self.metrics = QualityMetrics(episode_id=episode_id)
    
    def calculate_score(self) -> float:
        """
        Calculate quality score (0-100).
        
        Score calculation:
        - Start with 100
        - Deduct points for errors, retries, malformed data, mismatches
        - Minimum score is 0
        
        Returns:
            Quality score (0-100)
        """
        score = 100.0
        
        # Deduct for errors
        score -= self.metrics.errors_count * config.QUALITY_PENALTY_ERROR
        
        # Deduct for retries
        score -= self.metrics.retries_count * config.QUALITY_PENALTY_RETRY
        
        # Deduct for malformed beliefs
        score -= self.metrics.malformed_beliefs_count * config.QUALITY_PENALTY_MALFORMED
        
        # Deduct for registry mismatches
        score -= self.metrics.registry_mismatches_count * config.QUALITY_PENALTY_MISMATCH
        
        # Ensure score is not negative
        score = max(0.0, score)
        
        logger.info(
            f"Quality score calculated | episode_id={self.metrics.episode_id} | "
            f"score={score:.1f} | errors={self.metrics.errors_count} | "
            f"retries={self.metrics.retries_count}"
        )
        
        return score
    
    def calculate_grade(self, score: float) -> str:
        """
        Calculate quality grade from score.
        
        Args:
            score: Quality score (0-100)
        
        Returns:
            Quality grade (A, B, C, D, F)
        """
        if score >= config.QUALITY_THRESHOLDS["A"]:
            return "A"
        elif score >= config.QUALITY_THRESHOLDS["B"]:
            return "B"
        elif score >= config.QUALITY_THRESHOLDS["C"]:
            return "C"
        elif score >= config.QUALITY_THRESHOLDS["D"]:
            return "D"
        else:
            return "F"
    
    def generate_report(self) -> Dict:
        """
        Generate quality report.
        
        Returns:
            Quality report dictionary
        """
        score = self.calculate_score()
        grade = self.calculate_grade(score)
        
        report = {
            "episode_id": self.metrics.episode_id,
            "quality_score": score,
            "quality_grade": grade,
            "errors_count": self.metrics.errors_count,
            "retries_count": self.metrics.retries_count,
            "malformed_beliefs_count": self.metrics.malformed_beliefs_count,
            "registry_mismatches_count": self.metrics.registry_mismatches_count,
            "parsing_errors": self.metrics.parsing_errors,
            "api_errors": self.metrics.api_errors,
            "warnings": self.metrics.warnings,
            "execution_time_seconds": self.metrics.execution_time_seconds,
            "timestamp": self.metrics.timestamp
        }
        
        logger.info(
            f"Quality report generated | episode_id={self.metrics.episode_id} | "
            f"grade={grade} | score={score:.1f}"
        )
        
        return report
    
    def save_report(self, output_path: str = None):
        """
        Save quality report to JSON file.
        
        Args:
            output_path: Optional custom output path
        """
        import json
        from pathlib import Path
        
        if output_path is None:
            checkpoint_dir = config.CHECKPOINTS_DIR / self.metrics.episode_id
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            output_path = checkpoint_dir / "quality_report.json"
        
        report = self.generate_report()
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Quality report saved | path={output_path}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_quality_report(episode_id: str) -> Dict:
    """
    Load quality report for an episode.
    
    Args:
        episode_id: Episode identifier
    
    Returns:
        Quality report dictionary or None if not found
    """
    import json
    
    report_path = config.CHECKPOINTS_DIR / episode_id / "quality_report.json"
    
    if not report_path.exists():
        logger.warning(f"Quality report not found for episode: {episode_id}")
        return None
    
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_quality_summary(episode_ids: List[str]) -> Dict:
    """
    Get quality summary across multiple episodes.
    
    Args:
        episode_ids: List of episode identifiers
    
    Returns:
        Summary statistics
    """
    reports = [load_quality_report(ep_id) for ep_id in episode_ids]
    reports = [r for r in reports if r is not None]
    
    if not reports:
        return {}
    
    total_episodes = len(reports)
    avg_score = sum(r["quality_score"] for r in reports) / total_episodes
    
    grade_counts = {}
    for report in reports:
        grade = report["quality_grade"]
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
    
    return {
        "total_episodes": total_episodes,
        "average_score": avg_score,
        "grade_distribution": grade_counts,
        "total_errors": sum(r["errors_count"] for r in reports),
        "total_retries": sum(r["retries_count"] for r in reports),
    }

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "QualityMetrics",
    "QualityScorer",
    "load_quality_report",
    "get_quality_summary",
]

