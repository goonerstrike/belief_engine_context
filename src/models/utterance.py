"""
Utterance data model.
"""
from typing import Optional
from pydantic import BaseModel, Field, validator

class Utterance(BaseModel):
    """
    Utterance model representing an atomic unit of speech.
    
    Example:
        utterance = Utterance(
            id="utt_001",
            episode_id="episode_001",
            speaker="SPEAKER_A",
            timestamp_start="00:05:23",
            timestamp_end="00:05:45",
            text="Science is the objective search for truth."
        )
    """
    
    id: str = Field(..., description="Unique utterance identifier")
    episode_id: str = Field(..., description="Foreign key to Episode")
    speaker: str = Field(..., description="Speaker identifier")
    timestamp_start: str = Field(..., description="Start timestamp (HH:MM:SS)")
    timestamp_end: str = Field(..., description="End timestamp (HH:MM:SS)")
    text: str = Field(..., description="Utterance text")
    audio_snippet_uri: Optional[str] = Field(None, description="Audio snippet URI with fragment")
    
    @validator("timestamp_start", "timestamp_end")
    def validate_timestamp(cls, v):
        """Validate timestamp format HH:MM:SS."""
        import re
        if not re.match(r"^\d{2}:\d{2}:\d{2}$", v):
            raise ValueError(f"Invalid timestamp format: {v}. Expected HH:MM:SS")
        return v
    
    @validator("text")
    def validate_text(cls, v):
        """Validate text is not empty."""
        if not v or not v.strip():
            raise ValueError("Utterance text cannot be empty")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "id": "utt_001",
                "episode_id": "episode_001",
                "speaker": "SPEAKER_A",
                "timestamp_start": "00:05:23",
                "timestamp_end": "00:05:45",
                "text": "Science is the objective search for truth.",
                "audio_snippet_uri": "episode_001.mp3#t=323"
            }
        }

