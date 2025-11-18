"""
Belief Drift data model.
"""
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator

class DriftType(str, Enum):
    """Drift type enumeration."""
    NEW = "new"
    DROPPED = "dropped"
    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    REVERSAL = "reversal"

class BeliefDrift(BaseModel):
    """
    Belief Drift model tracking how beliefs change over time.
    
    Example:
        drift = BeliefDrift(
            id="drift_001",
            canonical_belief_id="can_001",
            drift_type=DriftType.STRENGTHENING,
            magnitude=0.25,
            episode_range=["episode_001", "episode_003"]
        )
    """
    
    id: str = Field(..., description="Unique drift identifier")
    canonical_belief_id: str = Field(..., description="Foreign key to CanonicalBelief")
    drift_type: DriftType = Field(..., description="new | dropped | strengthening | weakening | reversal")
    magnitude: float = Field(..., description="Magnitude of change [0.0, 1.0]", ge=0.0, le=1.0)
    episode_range: List[str] = Field(..., description="[start_episode_id, end_episode_id]")
    conviction_before: Optional[float] = Field(None, description="Conviction before change")
    conviction_after: Optional[float] = Field(None, description="Conviction after change")
    frequency_before: Optional[int] = Field(None, description="Frequency before change")
    frequency_after: Optional[int] = Field(None, description="Frequency after change")
    
    @validator("episode_range")
    def validate_episode_range(cls, v):
        """Validate episode_range has exactly 2 elements."""
        if len(v) != 2:
            raise ValueError(f"episode_range must have exactly 2 elements, got {len(v)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "drift_001",
                "canonical_belief_id": "can_001",
                "drift_type": "strengthening",
                "magnitude": 0.25,
                "episode_range": ["episode_001", "episode_003"],
                "conviction_before": 0.75,
                "conviction_after": 0.90,
                "frequency_before": 2,
                "frequency_after": 5
            }
        }

