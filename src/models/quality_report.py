"""
Quality Report data model.
"""
from typing import List
from pydantic import BaseModel, Field, validator

class QualityReport(BaseModel):
    """
    Quality Report model for episode processing run.
    
    Example:
        report = QualityReport(
            episode_id="episode_001",
            quality_score=92.5,
            quality_grade="A",
            errors_count=2,
            retries_count=3,
            execution_time_seconds=145.5
        )
    """
    
    episode_id: str = Field(..., description="Episode identifier")
    quality_score: float = Field(..., description="Overall score [0-100]", ge=0.0, le=100.0)
    quality_grade: str = Field(..., description="A, B, C, D, F")
    errors_count: int = Field(..., description="Total errors", ge=0)
    retries_count: int = Field(..., description="Total retries", ge=0)
    malformed_beliefs_count: int = Field(..., description="Malformed beliefs", ge=0)
    registry_mismatches_count: int = Field(..., description="Registry mismatches", ge=0)
    parsing_errors: List[str] = Field(default_factory=list, description="List of parsing errors")
    api_errors: List[str] = Field(default_factory=list, description="List of API errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    execution_time_seconds: float = Field(..., description="Execution time", ge=0.0)
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    
    @validator("quality_grade")
    def validate_quality_grade(cls, v):
        """Validate quality grade."""
        if v not in ["A", "B", "C", "D", "F"]:
            raise ValueError(f"quality_grade must be A, B, C, D, or F, got {v}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "episode_id": "episode_001",
                "quality_score": 92.5,
                "quality_grade": "A",
                "errors_count": 2,
                "retries_count": 3,
                "malformed_beliefs_count": 1,
                "registry_mismatches_count": 0,
                "parsing_errors": ["Line 45: Invalid timestamp"],
                "api_errors": ["Timeout on request 12"],
                "warnings": ["Low confidence belief skipped"],
                "execution_time_seconds": 145.5,
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }

