"""
Belief registry manager for deduplication.
"""
from typing import List
import json
from pathlib import Path
from loguru import logger
import config
from src.models import Belief, CanonicalBelief, BeliefRegistry
import uuid

class BeliefRegistryManager:
    """
    Manage global belief registry.
    
    Usage:
        manager = BeliefRegistryManager()
        manager.load()
        canonical_beliefs = manager.canonicalize(beliefs, episode_id)
        manager.save()
    """
    
    def __init__(self):
        """Initialize registry manager."""
        self.registry = BeliefRegistry()
        self.registry_path = config.REGISTRY_DIR / "belief_registry.json"
    
    def load(self):
        """Load registry from disk."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r") as f:
                    data = json.load(f)
                    self.registry = BeliefRegistry(**data)
                logger.info(f"Registry loaded | beliefs={len(self.registry.canonical_beliefs)}")
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}. Starting fresh.")
        else:
            logger.info("No existing registry found. Starting fresh.")
    
    def save(self):
        """Save registry to disk."""
        try:
            with open(self.registry_path, "w") as f:
                json.dump(self.registry.dict(), f, indent=2)
            logger.info("Registry saved")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def canonicalize(
        self,
        beliefs: List[Belief],
        episode_id: str
    ) -> List[CanonicalBelief]:
        """
        Canonicalize beliefs (simplified version).
        
        Args:
            beliefs: List of beliefs
            episode_id: Episode identifier
        
        Returns:
            List of canonical beliefs
        """
        logger.info(f"Canonicalizing {len(beliefs)} beliefs")
        
        canonical_beliefs = []
        
        for belief in beliefs:
            # Simplified: create one canonical belief per belief
            # In full version, this would do similarity matching
            canonical_id = str(uuid.uuid4())
            
            canonical = CanonicalBelief(
                id=canonical_id,
                canonical_text=belief.belief_text,
                belief_ids=[belief.id],
                source_utterance_ids=[belief.utterance_id],
                example_quotes=[belief.original_quote],
                first_seen_episode=episode_id,
                last_seen_episode=episode_id
            )
            
            canonical_beliefs.append(canonical)
            
            # Add to registry
            self.registry.add_canonical_belief(
                belief_id=canonical_id,
                canonical_text=belief.belief_text,
                raw_belief_ids=[belief.id],
                episode_id=episode_id
            )
        
        logger.info(f"Created {len(canonical_beliefs)} canonical beliefs")
        
        return canonical_beliefs

