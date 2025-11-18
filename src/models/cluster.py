"""
Cluster data model.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class Cluster(BaseModel):
    """
    Cluster model representing a group of semantically similar canonical beliefs.
    
    CRITICAL: 
    - Minimum size enforced (MIN_CLUSTER_SIZE)
    - Must maintain source linkage
    
    Example:
        cluster = Cluster(
            id="clus_001",
            name="Scientific Methodology",
            canonical_belief_ids=["can_001", "can_002", "can_003"],
            source_utterance_ids=["utt_001", "utt_002", "utt_003"],
            example_quotes=["Science is objective", "Evidence matters"],
            ontology_level="core",
            size=3
        )
    """
    
    id: str = Field(..., description="Unique cluster identifier")
    name: str = Field(..., description="Cluster name/description")
    canonical_belief_ids: List[str] = Field(..., description="List of CanonicalBelief IDs in cluster")
    source_utterance_ids: List[str] = Field(..., description="CRITICAL: All source utterances")
    example_quotes: List[str] = Field(..., description="Representative quotes")
    ontology_level: str = Field(..., description="Tier: core | worldview | reasoning | surface")
    parent_cluster_id: Optional[str] = Field(None, description="For hierarchical clustering")
    size: int = Field(..., description="Number of canonical beliefs", ge=1)
    created_episode: Optional[str] = Field(None, description="Episode where cluster was created")
    last_updated_episode: Optional[str] = Field(None, description="Episode where cluster was last updated")
    
    @validator("ontology_level")
    def validate_ontology_level(cls, v):
        """Validate ontology level."""
        valid_levels = ["core", "worldview", "reasoning", "surface"]
        if v not in valid_levels:
            raise ValueError(f"ontology_level must be one of {valid_levels}, got {v}")
        return v
    
    @validator("canonical_belief_ids")
    def validate_canonical_belief_ids(cls, v):
        """Validate canonical_belief_ids is not empty."""
        if not v:
            raise ValueError("canonical_belief_ids cannot be empty")
        return v
    
    @validator("source_utterance_ids")
    def validate_source_utterance_ids(cls, v):
        """CRITICAL: Validate source linkage."""
        if not v:
            raise ValueError("source_utterance_ids cannot be empty (source linkage required)")
        return v
    
    @validator("size")
    def validate_size_matches_beliefs(cls, v, values):
        """Validate size matches canonical_belief_ids count."""
        if "canonical_belief_ids" in values and len(values["canonical_belief_ids"]) != v:
            raise ValueError(f"size {v} does not match canonical_belief_ids count {len(values['canonical_belief_ids'])}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "clus_001",
                "name": "Scientific Methodology",
                "canonical_belief_ids": ["can_001", "can_002", "can_003"],
                "source_utterance_ids": ["utt_001", "utt_002", "utt_003"],
                "example_quotes": [
                    "Science is objective",
                    "Evidence is required"
                ],
                "ontology_level": "core",
                "size": 3,
                "created_episode": "episode_001"
            }
        }

