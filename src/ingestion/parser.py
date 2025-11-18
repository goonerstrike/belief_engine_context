"""
Transcript parser for diarized transcript files.
"""
from pathlib import Path
from typing import List, Tuple
from loguru import logger
from src.models import Episode, Utterance
from src.utils.validators import validate_transcript_line, validate_episode_id
from src.utils.exceptions import IngestionError
from src.utils.quality_scorer import QualityScorer
import uuid
from datetime import datetime

class TranscriptParser:
    """
    Parse diarized transcript files.
    
    Expected format: SPEAKER | HH:MM:SS | HH:MM:SS | text
    
    Usage:
        parser = TranscriptParser(quality_scorer=scorer)
        episode, utterances = parser.parse("matthew_lacroix.txt", episode_id="episode_001")
    """
    
    def __init__(self, quality_scorer: QualityScorer = None):
        """
        Initialize parser.
        
        Args:
            quality_scorer: Optional quality scorer for tracking errors
        """
        self.quality_scorer = quality_scorer
    
    def parse(
        self,
        transcript_path: str,
        episode_id: str,
        title: str = None
    ) -> Tuple[Episode, List[Utterance]]:
        """
        Parse transcript file.
        
        Args:
            transcript_path: Path to transcript file
            episode_id: Episode identifier
            title: Optional episode title
        
        Returns:
            Tuple of (Episode, List[Utterance])
        
        Raises:
            IngestionError: If parsing fails critically
        """
        logger.info(f"Starting ingestion | episode_id={episode_id} | path={transcript_path}")
        
        # Validate episode ID
        validate_episode_id(episode_id)
        
        # Check file exists
        path = Path(transcript_path)
        if not path.exists():
            raise IngestionError(f"Transcript file not found: {transcript_path}")
        
        # Parse file
        utterances = []
        line_num = 0
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line_num += 1
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    try:
                        # Parse line
                        speaker, start_time, end_time, text = validate_transcript_line(line)
                        
                        # Create utterance
                        utterance = Utterance(
                            id=str(uuid.uuid4()),
                            episode_id=episode_id,
                            speaker=speaker,
                            timestamp_start=start_time,
                            timestamp_end=end_time,
                            text=text
                        )
                        
                        utterances.append(utterance)
                        
                    except Exception as e:
                        # Log parsing error
                        error_msg = f"Line {line_num}: {str(e)}"
                        logger.warning(f"Parsing error | {error_msg}")
                        
                        if self.quality_scorer:
                            self.quality_scorer.metrics.add_parsing_error(error_msg)
                        
                        # Continue parsing (graceful degradation)
                        continue
        
        except Exception as e:
            raise IngestionError(f"Failed to read transcript file: {e}")
        
        # Create episode
        episode = Episode(
            id=episode_id,
            title=title or path.stem,
            date=datetime.now().strftime("%Y-%m-%d"),
            transcript_path=str(path)
        )
        
        logger.info(
            f"Ingestion complete | episode_id={episode_id} | "
            f"utterances={len(utterances)} | lines_parsed={line_num}"
        )
        
        return episode, utterances

