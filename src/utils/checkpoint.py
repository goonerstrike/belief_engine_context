"""
Checkpoint save/load/recovery system for Belief Engine.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger
import config
from .exceptions import CheckpointError

# ============================================================================
# CHECKPOINT MANAGEMENT
# ============================================================================

class CheckpointManager:
    """
    Manage checkpoints for an episode.
    
    Usage:
        manager = CheckpointManager(episode_id="episode_001")
        manager.save("beliefs_raw", beliefs, stats={"count": 150})
        beliefs = manager.load("beliefs_raw")
    """
    
    def __init__(self, episode_id: str):
        """
        Initialize checkpoint manager.
        
        Args:
            episode_id: Episode identifier
        """
        self.episode_id = episode_id
        self.checkpoint_dir = config.CHECKPOINTS_DIR / episode_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save(
        self,
        phase: str,
        data: List[Any],
        stats: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save checkpoint for a pipeline phase.
        
        Args:
            phase: Pipeline phase name (e.g., "beliefs_raw")
            data: Data to checkpoint (must be JSON-serializable)
            stats: Optional statistics dictionary
        
        Returns:
            Path to checkpoint file
        
        Raises:
            CheckpointError: If save fails
        """
        if not config.CHECKPOINT_ENABLED:
            logger.debug(f"Checkpointing disabled, skipping save for {phase}")
            return None
        
        try:
            checkpoint_file = self.checkpoint_dir / f"{phase}.json"
            
            # Create checkpoint structure
            checkpoint = {
                "metadata": {
                    "episode_id": self.episode_id,
                    "phase": phase,
                    "timestamp": datetime.now().isoformat(),
                    "stats": stats or {}
                },
                "data": data
            }
            
            # Write to temporary file first (atomic write)
            temp_file = checkpoint_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
            
            # Rename to final location (atomic operation)
            temp_file.rename(checkpoint_file)
            
            logger.info(
                f"Checkpoint saved | phase={phase} | episode_id={self.episode_id} | "
                f"count={len(data)} | path={checkpoint_file}"
            )
            
            return checkpoint_file
            
        except Exception as e:
            raise CheckpointError(f"Failed to save checkpoint for {phase}: {e}")
    
    def load(self, phase: str) -> Optional[List[Any]]:
        """
        Load checkpoint for a pipeline phase.
        
        Args:
            phase: Pipeline phase name
        
        Returns:
            Checkpoint data or None if not found
        
        Raises:
            CheckpointError: If load fails
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{phase}.json"
            
            if not checkpoint_file.exists():
                logger.debug(f"No checkpoint found for {phase}")
                return None
            
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
            
            # Validate checkpoint structure
            if "metadata" not in checkpoint or "data" not in checkpoint:
                raise CheckpointError(f"Invalid checkpoint structure in {checkpoint_file}")
            
            metadata = checkpoint["metadata"]
            data = checkpoint["data"]
            
            logger.info(
                f"Checkpoint loaded | phase={phase} | episode_id={metadata['episode_id']} | "
                f"count={len(data)} | timestamp={metadata['timestamp']}"
            )
            
            return data
            
        except CheckpointError:
            raise
        except Exception as e:
            raise CheckpointError(f"Failed to load checkpoint for {phase}: {e}")
    
    def exists(self, phase: str) -> bool:
        """
        Check if checkpoint exists for a phase.
        
        Args:
            phase: Pipeline phase name
        
        Returns:
            True if checkpoint exists
        """
        checkpoint_file = self.checkpoint_dir / f"{phase}.json"
        return checkpoint_file.exists()
    
    def get_last_checkpoint(self) -> Optional[str]:
        """
        Get the last completed checkpoint phase.
        
        Returns:
            Phase name or None if no checkpoints exist
        """
        for phase in reversed(config.CHECKPOINT_PHASES):
            if self.exists(phase):
                return phase
        return None
    
    def delete(self, phase: str):
        """
        Delete checkpoint for a phase.
        
        Args:
            phase: Pipeline phase name
        """
        checkpoint_file = self.checkpoint_dir / f"{phase}.json"
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            logger.info(f"Checkpoint deleted | phase={phase} | episode_id={self.episode_id}")
    
    def delete_all(self):
        """Delete all checkpoints for this episode."""
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            checkpoint_file.unlink()
        logger.info(f"All checkpoints deleted | episode_id={self.episode_id}")

# ============================================================================
# CHECKPOINT RECOVERY
# ============================================================================

def get_resume_point(episode_id: str) -> Optional[str]:
    """
    Determine the pipeline phase to resume from.
    
    Args:
        episode_id: Episode identifier
    
    Returns:
        Phase name to resume from, or None to start from beginning
    """
    manager = CheckpointManager(episode_id)
    last_checkpoint = manager.get_last_checkpoint()
    
    if last_checkpoint:
        # Find the next phase after the last checkpoint
        try:
            last_index = config.CHECKPOINT_PHASES.index(last_checkpoint)
            if last_index < len(config.CHECKPOINT_PHASES) - 1:
                next_phase = config.CHECKPOINT_PHASES[last_index + 1]
                logger.info(
                    f"Resume point determined | episode_id={episode_id} | "
                    f"last_checkpoint={last_checkpoint} | next_phase={next_phase}"
                )
                return last_checkpoint  # Return last completed phase
            else:
                logger.info(f"All phases completed | episode_id={episode_id}")
                return last_checkpoint
        except ValueError:
            logger.warning(f"Unknown checkpoint phase: {last_checkpoint}")
            return None
    
    logger.info(f"No checkpoints found | episode_id={episode_id}")
    return None

# ============================================================================
# CLEANUP
# ============================================================================

def cleanup_old_checkpoints(days: int = None):
    """
    Clean up checkpoints older than specified days.
    
    Args:
        days: Number of days to keep (default: config.CHECKPOINT_CLEANUP_DAYS)
    """
    days = days if days is not None else config.CHECKPOINT_CLEANUP_DAYS
    
    if days <= 0:
        logger.info("Checkpoint cleanup disabled (days <= 0)")
        return
    
    from datetime import timedelta
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    
    for episode_dir in config.CHECKPOINTS_DIR.iterdir():
        if not episode_dir.is_dir():
            continue
        
        # Check the modification time of the directory
        mtime = datetime.fromtimestamp(episode_dir.stat().st_mtime)
        
        if mtime < cutoff_date:
            # Delete all checkpoints in this directory
            for checkpoint_file in episode_dir.glob("*.json"):
                checkpoint_file.unlink()
                deleted_count += 1
            
            # Remove the directory if empty
            if not list(episode_dir.iterdir()):
                episode_dir.rmdir()
                logger.info(f"Deleted old checkpoint directory: {episode_dir.name}")
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old checkpoint(s)")

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "CheckpointManager",
    "get_resume_point",
    "cleanup_old_checkpoints",
]

