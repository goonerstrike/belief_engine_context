"""
Canonical Belief data model.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class CanonicalBelief(BaseModel):
    """
    Canonical belief model representing a standardized, deduplicated belief.
    
    CRITICAL: Must maintain source linkage with source_utterance_ids and example_quotes.
    
    Example:
        canonical = CanonicalBelief(
            id="can_001",
            canonical_text="Science requires objective evidence",
            belief_ids=["bel_001", "bel_002", "bel_003"],
            source_utterance_ids=["utt_001", "utt_002"],
            example_quotes=["Science is objective", "Evidence is required"]
        )
    """
    
    id: str = Field(..., description="Unique canonical belief identifier")
    canonical_text: str = Field(..., description="Standardized belief text")
    belief_ids: List[str] = Field(..., description="List of raw Belief IDs mapped to this canonical belief")
    source_utterance_ids: List[str] = Field(..., description="CRITICAL: All source utterances")
    example_quotes: List[str] = Field(..., description="Example quotes from source utterances")
    cluster_id: Optional[str] = Field(None, description="Foreign key to Cluster")
    first_seen_episode: Optional[str] = Field(None, description="Episode ID where first appeared")
    last_seen_episode: Optional[str] = Field(None, description="Episode ID where last appeared")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding (cached)")
    
    @validator("belief_ids")
    def validate_belief_ids(cls, v):
        """Validate belief_ids is not empty."""
        if not v:
            raise ValueError("belief_ids cannot be empty")
        return v
    
    @validator("source_utterance_ids")
    def validate_source_utterance_ids(cls, v):
        """CRITICAL: Validate source_utterance_ids is not empty."""
        if not v:
            raise ValueError("source_utterance_ids cannot be empty (source linkage required)")
        return v
    
    @validator("example_quotes")
    def validate_example_quotes(cls, v):
        """Validate example_quotes is not empty."""
        if not v:
            raise ValueError("example_quotes cannot be empty")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "can_001",
                "canonical_text": "Science requires objective evidence",
                "belief_ids": ["bel_001", "bel_002", "bel_003"],
                "source_utterance_ids": ["utt_001", "utt_002"],
                "example_quotes": [
                    "Science is the objective search for truth",
                    "Evidence is required for scientific claims"
                ],
                "cluster_id": "clus_001",
                "first_seen_episode": "episode_001",
                "last_seen_episode": "episode_003"
            }
        }

