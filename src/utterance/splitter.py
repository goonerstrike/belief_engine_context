"""
Utterance splitter for atomic statement extraction.
"""
from typing import List
import re
import uuid
from loguru import logger
from src.models import Utterance

class UtteranceSplitter:
    """
    Split long utterances into atomic statements.
    
    Usage:
        splitter = UtteranceSplitter()
        atomic_utterances = splitter.split(utterances)
    """
    
    def split(self, utterances: List[Utterance]) -> List[Utterance]:
        """
        Split utterances into atomic statements.
        
        Args:
            utterances: List of utterances
        
        Returns:
            List of atomic utterances
        """
        logger.info(f"Splitting {len(utterances)} utterances")
        
        atomic_utterances = []
        
        for utterance in utterances:
            # Split on sentence boundaries
            sentences = self._split_sentences(utterance.text)
            
            if len(sentences) <= 1:
                # Already atomic
                atomic_utterances.append(utterance)
            else:
                # Split into multiple utterances
                for sentence in sentences:
                    if sentence.strip():
                        atomic_utt = Utterance(
                            id=str(uuid.uuid4()),
                            episode_id=utterance.episode_id,
                            speaker=utterance.speaker,
                            timestamp_start=utterance.timestamp_start,
                            timestamp_end=utterance.timestamp_end,
                            text=sentence.strip(),
                            audio_snippet_uri=utterance.audio_snippet_uri
                        )
                        atomic_utterances.append(atomic_utt)
        
        logger.info(f"Split into {len(atomic_utterances)} atomic utterances")
        
        return atomic_utterances
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on . ! ?
        # Could be enhanced with more sophisticated NLP
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s for s in sentences if s.strip()]

