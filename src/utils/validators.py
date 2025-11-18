"""
Input validation functions for Belief Engine.
"""
import re
from datetime import datetime
from typing import Tuple, Optional
from .exceptions import ValidationError

# ============================================================================
# TIMESTAMP VALIDATION
# ============================================================================

def validate_timestamp(timestamp: str) -> bool:
    """
    Validate timestamp format (HH:MM:SS).
    
    Args:
        timestamp: Timestamp string
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If timestamp is invalid
    """
    pattern = r"^\d{2}:\d{2}:\d{2}$"
    if not re.match(pattern, timestamp):
        raise ValidationError(f"Invalid timestamp format: {timestamp}. Expected HH:MM:SS")
    
    # Validate ranges
    parts = timestamp.split(":")
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    
    if hours < 0 or hours > 23:
        raise ValidationError(f"Invalid hours in timestamp: {hours}")
    if minutes < 0 or minutes > 59:
        raise ValidationError(f"Invalid minutes in timestamp: {minutes}")
    if seconds < 0 or seconds > 59:
        raise ValidationError(f"Invalid seconds in timestamp: {seconds}")
    
    return True

def timestamp_to_seconds(timestamp: str) -> int:
    """
    Convert HH:MM:SS timestamp to seconds.
    
    Args:
        timestamp: Timestamp string
    
    Returns:
        Total seconds
    """
    validate_timestamp(timestamp)
    parts = timestamp.split(":")
    hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
    return hours * 3600 + minutes * 60 + seconds

def seconds_to_timestamp(seconds: int) -> str:
    """
    Convert seconds to HH:MM:SS timestamp.
    
    Args:
        seconds: Total seconds
    
    Returns:
        Timestamp string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# ============================================================================
# TRANSCRIPT LINE VALIDATION
# ============================================================================

def validate_transcript_line(line: str) -> Tuple[str, str, str, str]:
    """
    Validate and parse a diarized transcript line.
    
    Expected format: SPEAKER | HH:MM:SS | HH:MM:SS | text
    
    Args:
        line: Transcript line
    
    Returns:
        Tuple of (speaker, start_time, end_time, text)
    
    Raises:
        ValidationError: If line is invalid
    """
    # Split on pipe
    parts = line.split("|")
    
    if len(parts) != 4:
        raise ValidationError(f"Invalid line format. Expected 4 parts, got {len(parts)}")
    
    speaker = parts[0].strip()
    start_time = parts[1].strip()
    end_time = parts[2].strip()
    text = parts[3].strip()
    
    # Validate speaker
    if not speaker:
        raise ValidationError("Speaker cannot be empty")
    
    # Validate timestamps
    validate_timestamp(start_time)
    validate_timestamp(end_time)
    
    # Validate start < end
    start_seconds = timestamp_to_seconds(start_time)
    end_seconds = timestamp_to_seconds(end_time)
    
    if start_seconds >= end_seconds:
        raise ValidationError(f"Start time {start_time} must be before end time {end_time}")
    
    # Validate text
    if not text:
        raise ValidationError("Utterance text cannot be empty")
    
    return speaker, start_time, end_time, text

# ============================================================================
# EPISODE ID VALIDATION
# ============================================================================

def validate_episode_id(episode_id: str) -> bool:
    """
    Validate episode ID format.
    
    Args:
        episode_id: Episode identifier
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If episode_id is invalid
    """
    if not episode_id:
        raise ValidationError("Episode ID cannot be empty")
    
    # Allow alphanumeric, underscores, hyphens
    pattern = r"^[a-zA-Z0-9_-]+$"
    if not re.match(pattern, episode_id):
        raise ValidationError(
            f"Invalid episode ID: {episode_id}. "
            "Only alphanumeric characters, underscores, and hyphens allowed"
        )
    
    return True

# ============================================================================
# SCORE VALIDATION
# ============================================================================

def validate_score(score: float, min_val: float = 0.0, max_val: float = 1.0, name: str = "score") -> bool:
    """
    Validate score is within range.
    
    Args:
        score: Score value
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the score (for error message)
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If score is out of range
    """
    if not isinstance(score, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(score)}")
    
    if score < min_val or score > max_val:
        raise ValidationError(f"{name} must be between {min_val} and {max_val}, got {score}")
    
    return True

# ============================================================================
# AUDIO URI VALIDATION
# ============================================================================

def validate_audio_uri(uri: str) -> bool:
    """
    Validate audio URI format.
    
    Expected format: filename.ext#t=timestamp or filename.ext#t=start,end
    
    Args:
        uri: Audio URI
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If URI is invalid
    """
    if not uri:
        raise ValidationError("Audio URI cannot be empty")
    
    # Check for fragment
    if "#t=" not in uri:
        raise ValidationError(f"Invalid audio URI: {uri}. Expected format: file.ext#t=timestamp")
    
    parts = uri.split("#t=")
    if len(parts) != 2:
        raise ValidationError(f"Invalid audio URI: {uri}")
    
    filename, time_part = parts
    
    # Validate filename is not empty
    if not filename:
        raise ValidationError("Audio filename cannot be empty")
    
    # Validate time part (either single number or start,end)
    time_pattern = r"^\d+$|^\d+,\d+$"
    if not re.match(time_pattern, time_part):
        raise ValidationError(
            f"Invalid audio URI time part: {time_part}. "
            "Expected single timestamp or start,end"
        )
    
    return True

# ============================================================================
# ISO DATE VALIDATION
# ============================================================================

def validate_iso_date(date_str: str) -> bool:
    """
    Validate ISO 8601 date format (YYYY-MM-DD).
    
    Args:
        date_str: Date string
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If date is invalid
    """
    try:
        datetime.fromisoformat(date_str)
        return True
    except ValueError as e:
        raise ValidationError(f"Invalid ISO date: {date_str}. Error: {e}")

# ============================================================================
# PATH VALIDATION
# ============================================================================

def validate_file_path(path: str, must_exist: bool = False) -> bool:
    """
    Validate file path.
    
    Args:
        path: File path
        must_exist: Whether file must exist
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If path is invalid
    """
    from pathlib import Path
    
    if not path:
        raise ValidationError("File path cannot be empty")
    
    path_obj = Path(path)
    
    if must_exist and not path_obj.exists():
        raise ValidationError(f"File does not exist: {path}")
    
    return True

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "validate_timestamp",
    "timestamp_to_seconds",
    "seconds_to_timestamp",
    "validate_transcript_line",
    "validate_episode_id",
    "validate_score",
    "validate_audio_uri",
    "validate_iso_date",
    "validate_file_path",
]

