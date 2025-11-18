"""
Belief data model.
"""
from typing import Optional, Dict
from pydantic import BaseModel, Field, validator

class Belief(BaseModel):
    """
    Belief model representing an atomic, declarative statement.
    
    CRITICAL: Every belief MUST link to utterance_id for source traceability.
    
    Example:
        belief = Belief(
            id="bel_001",
            utterance_id="utt_001",
            belief_text="Science is the objective search for truth",
            confidence=0.95,
            original_quote="Science is the objective search for truth.",
            extraction_flags={"q16_first_principles": True}
        )
    """
    
    id: str = Field(..., description="Unique belief identifier")
    utterance_id: str = Field(..., description="REQUIRED: Foreign key to Utterance (source linkage)")
    belief_text: str = Field(..., description="The extracted belief statement")
    confidence: float = Field(..., description="Extraction confidence [0.0, 1.0]", ge=0.0, le=1.0)
    original_quote: str = Field(..., description="Original quote from utterance")
    context: Optional[str] = Field(None, description="Additional context")
    extraction_flags: Dict[str, bool] = Field(..., description="Extraction flags (q16-q26)")
    
    @validator("belief_text", "original_quote")
    def validate_not_empty(cls, v):
        """Validate text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Text field cannot be empty")
        return v.strip()
    
    @validator("extraction_flags")
    def validate_extraction_flags(cls, v):
        """Validate at least one extraction flag is set."""
        if not any(v.values()):
            raise ValueError("At least one extraction flag must be True")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "id": "bel_001",
                "utterance_id": "utt_001",
                "belief_text": "Science is the objective search for truth",
                "confidence": 0.95,
                "original_quote": "Science is the objective search for truth.",
                "context": "Discussion about academic methodology",
                "extraction_flags": {
                    "q16_first_principles": True,
                    "q19_epistemology": True
                }
            }
        }

