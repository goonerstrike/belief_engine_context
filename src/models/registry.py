"""
Belief Registry data model.
"""
from typing import Dict, List
from pydantic import BaseModel, Field

class BeliefRegistry(BaseModel):
    """
    Belief Registry model for global deduplication and tracking.
    
    Maintains:
    - All canonical beliefs
    - Embedding cache
    - Text aliases for fast lookup
    - Episode history
    
    Example:
        registry = BeliefRegistry(
            canonical_beliefs={
                "can_001": {
                    "canonical_text": "Science requires evidence",
                    "raw_belief_ids": ["bel_001", "bel_002"],
                    "episode_history": ["episode_001", "episode_002"]
                }
            }
        )
    """
    
    canonical_beliefs: Dict[str, Dict] = Field(
        default_factory=dict,
        description="belief_id → {canonical_text, raw_belief_ids, episode_history}"
    )
    embeddings_cache: Dict[str, List[float]] = Field(
        default_factory=dict,
        description="belief_id → embedding vector"
    )
    aliases: Dict[str, str] = Field(
        default_factory=dict,
        description="raw_belief_text → canonical_id for fast lookup"
    )
    episode_history: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="belief_id → list of episode_ids where it appeared"
    )
    
    def add_canonical_belief(
        self,
        belief_id: str,
        canonical_text: str,
        raw_belief_ids: List[str],
        episode_id: str,
        embedding: List[float] = None
    ):
        """Add or update a canonical belief."""
        self.canonical_beliefs[belief_id] = {
            "canonical_text": canonical_text,
            "raw_belief_ids": raw_belief_ids,
            "episode_history": [episode_id]
        }
        
        if embedding:
            self.embeddings_cache[belief_id] = embedding
        
        # Add alias for fast lookup
        self.aliases[canonical_text.lower()] = belief_id
        
        # Update episode history
        if belief_id not in self.episode_history:
            self.episode_history[belief_id] = []
        if episode_id not in self.episode_history[belief_id]:
            self.episode_history[belief_id].append(episode_id)
    
    def find_by_text(self, text: str) -> str:
        """Find canonical belief ID by text."""
        return self.aliases.get(text.lower())
    
    def get_embedding(self, belief_id: str) -> List[float]:
        """Get cached embedding for belief."""
        return self.embeddings_cache.get(belief_id)
    
    class Config:
        schema_extra = {
            "example": {
                "canonical_beliefs": {
                    "can_001": {
                        "canonical_text": "Science requires evidence",
                        "raw_belief_ids": ["bel_001", "bel_002"],
                        "episode_history": ["episode_001", "episode_002"]
                    }
                },
                "aliases": {
                    "science requires evidence": "can_001"
                },
                "episode_history": {
                    "can_001": ["episode_001", "episode_002"]
                }
            }
        }

