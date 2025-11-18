"""
Contradiction data model.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class Contradiction(BaseModel):
    """
    Contradiction model representing opposing beliefs.
    
    Example:
        contradiction = Contradiction(
            id="cont_001",
            belief_a_id="can_001",
            belief_b_id="can_002",
            opposition_score=0.85,
            type="within_speaker",
            episode_ids=["episode_001", "episode_002"],
            is_reversal=True
        )
    """
    
    id: str = Field(..., description="Unique contradiction identifier")
    belief_a_id: str = Field(..., description="First belief ID (CanonicalBelief)")
    belief_b_id: str = Field(..., description="Second belief ID (CanonicalBelief)")
    opposition_score: float = Field(..., description="Semantic opposition score [0.0, 1.0]", ge=0.0, le=1.0)
    type: str = Field(..., description="within_speaker | cross_speaker")
    episode_ids: List[str] = Field(..., description="Episodes where contradiction appears")
    is_reversal: bool = Field(..., description="True if same speaker reversed position")
    speaker_a: Optional[str] = Field(None, description="Speaker for belief_a")
    speaker_b: Optional[str] = Field(None, description="Speaker for belief_b")
    detected_at: Optional[str] = Field(None, description="ISO 8601 timestamp")
    
    @validator("type")
    def validate_type(cls, v):
        """Validate contradiction type."""
        if v not in ["within_speaker", "cross_speaker"]:
            raise ValueError(f"type must be 'within_speaker' or 'cross_speaker', got {v}")
        return v
    
    @validator("is_reversal")
    def validate_reversal(cls, v, values):
        """Validate reversal logic."""
        if v and values.get("type") != "within_speaker":
            raise ValueError("is_reversal can only be True for within_speaker contradictions")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "cont_001",
                "belief_a_id": "can_001",
                "belief_b_id": "can_002",
                "opposition_score": 0.85,
                "type": "within_speaker",
                "episode_ids": ["episode_001", "episode_002"],
                "is_reversal": True,
                "speaker_a": "SPEAKER_A",
                "speaker_b": "SPEAKER_A",
                "detected_at": "2025-01-15T10:30:00Z"
            }
        }

