"""
Belief Matrix data models.
"""
from typing import Dict, List
from pydantic import BaseModel, Field

class Weight(BaseModel):
    """
    Weight model for belief matrix cells.
    
    NOT a boolean - contains rich information about belief presence.
    """
    
    conviction_avg: float = Field(..., description="Mean confidence score [0.0, 1.0]", ge=0.0, le=1.0)
    frequency: int = Field(..., description="Count of mentions", ge=0)
    stability_score: float = Field(..., description="Consistency within episode [0.0, 1.0]", ge=0.0, le=1.0)
    presence_flag: bool = Field(..., description="Boolean indicator (present/absent)")
    
    class Config:
        schema_extra = {
            "example": {
                "conviction_avg": 0.85,
                "frequency": 3,
                "stability_score": 0.92,
                "presence_flag": True
            }
        }

class BeliefMatrix(BaseModel):
    """
    Belief Matrix model representing episodes × canonical_beliefs.
    
    Weighted matrix tracking beliefs across episodes.
    
    Example:
        matrix = BeliefMatrix(
            episodes=["episode_001", "episode_002"],
            canonical_belief_ids=["can_001", "can_002"],
            weights={
                "episode_001": {
                    "can_001": Weight(conviction_avg=0.85, frequency=3, ...)
                }
            }
        )
    """
    
    episodes: List[str] = Field(..., description="List of episode IDs (rows)")
    canonical_belief_ids: List[str] = Field(..., description="List of canonical belief IDs (columns)")
    weights: Dict[str, Dict[str, Weight]] = Field(..., description="Nested dict: episode_id → belief_id → Weight")
    
    def get_weight(self, episode_id: str, belief_id: str) -> Weight:
        """Get weight for specific cell."""
        return self.weights.get(episode_id, {}).get(belief_id)
    
    def set_weight(self, episode_id: str, belief_id: str, weight: Weight):
        """Set weight for specific cell."""
        if episode_id not in self.weights:
            self.weights[episode_id] = {}
        self.weights[episode_id][belief_id] = weight
    
    class Config:
        schema_extra = {
            "example": {
                "episodes": ["episode_001", "episode_002"],
                "canonical_belief_ids": ["can_001", "can_002"],
                "weights": {
                    "episode_001": {
                        "can_001": {
                            "conviction_avg": 0.85,
                            "frequency": 3,
                            "stability_score": 0.92,
                            "presence_flag": True
                        }
                    }
                }
            }
        }

