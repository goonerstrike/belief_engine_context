"""
Custom exception classes for Belief Engine.
"""

class BeliefEngineError(Exception):
    """Base exception for all Belief Engine errors."""
    pass

class IngestionError(BeliefEngineError):
    """Error during transcript ingestion."""
    pass

class BeliefExtractionError(BeliefEngineError):
    """Error during belief extraction."""
    pass

class CanonicalizationError(BeliefEngineError):
    """Error during canonicalization."""
    pass

class ClusteringError(BeliefEngineError):
    """Error during clustering."""
    pass

class CheckpointError(BeliefEngineError):
    """Error with checkpoint save/load."""
    pass

class RateLimitError(BeliefEngineError):
    """Rate limit exceeded."""
    pass

class ValidationError(BeliefEngineError):
    """Validation error."""
    pass

class RegistryError(BeliefEngineError):
    """Error with belief registry."""
    pass

class OntologyError(BeliefEngineError):
    """Error during ontology building."""
    pass

class MatrixError(BeliefEngineError):
    """Error during matrix building."""
    pass

class TimelineError(BeliefEngineError):
    """Error during timeline analysis."""
    pass

class ContrarianError(BeliefEngineError):
    """Error during contrarian detection."""
    pass

__all__ = [
    "BeliefEngineError",
    "IngestionError",
    "BeliefExtractionError",
    "CanonicalizationError",
    "ClusteringError",
    "CheckpointError",
    "RateLimitError",
    "ValidationError",
    "RegistryError",
    "OntologyError",
    "MatrixError",
    "TimelineError",
    "ContrarianError",
]

