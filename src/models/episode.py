"""
Episode data model.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Episode(BaseModel):
    """
    Episode model representing a transcript processing run.
    
    Example:
        episode = Episode(
            id="episode_001",
            title="Matthew Lacroix Interview",
            date="2025-01-15",
            transcript_path="matthew_lacroix.txt"
        )
    """
    
    id: str = Field(..., description="Unique episode identifier")
    title: str = Field(..., description="Episode title")
    date: str = Field(..., description="ISO 8601 date (YYYY-MM-DD)")
    transcript_path: str = Field(..., description="Path to diarized transcript file")
    audio_uri: Optional[str] = Field(None, description="URI to audio file")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    quality_score: Optional[float] = Field(None, description="Quality score 0-100")
    quality_grade: Optional[str] = Field(None, description="Quality grade A-F")
    wandb_run_id: Optional[str] = Field(None, description="W&B run identifier")
    
    @validator("date")
    def validate_date(cls, v):
        """Validate ISO 8601 date format."""
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Invalid ISO date format: {v}")
        return v
    
    @validator("quality_score")
    def validate_quality_score(cls, v):
        """Validate quality score range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError(f"Quality score must be between 0 and 100, got {v}")
        return v
    
    @validator("quality_grade")
    def validate_quality_grade(cls, v):
        """Validate quality grade."""
        if v is not None and v not in ["A", "B", "C", "D", "F"]:
            raise ValueError(f"Quality grade must be A, B, C, D, or F, got {v}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "episode_001",
                "title": "Matthew Lacroix Interview",
                "date": "2025-01-15",
                "transcript_path": "matthew_lacroix.txt",
                "audio_uri": "s3://bucket/matthew_lacroix.mp3",
                "quality_score": 92.5,
                "quality_grade": "A"
            }
        }

