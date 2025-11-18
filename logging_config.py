"""
Centralized logging configuration for Belief Engine.
"""
import sys
from pathlib import Path
from loguru import logger
import config

# Remove default logger
logger.remove()

# ============================================================================
# FORMATTERS
# ============================================================================

# Detailed format for file logging
FILE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Simpler format for console
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{message}</level>"
)

# Structured format for W&B (optional)
STRUCTURED_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}"

# ============================================================================
# CONSOLE HANDLER
# ============================================================================

if config.LOG_TO_CONSOLE:
    logger.add(
        sys.stdout,
        format=CONSOLE_FORMAT,
        level=config.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )

# ============================================================================
# FILE HANDLERS
# ============================================================================

if config.LOG_TO_FILE:
    # Master log (all logs combined)
    logger.add(
        config.LOGS_DIR / "master.log",
        format=FILE_FORMAT,
        level="DEBUG",  # Capture everything in master log
        rotation=config.LOG_ROTATION,
        retention=config.LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Error log (errors and critical only)
    logger.add(
        config.LOGS_DIR / "errors.log",
        format=FILE_FORMAT,
        level="ERROR",
        rotation=config.LOG_ROTATION,
        retention=config.LOG_RETENTION,
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Per-module logs (created dynamically as needed)
    # These will be added by individual modules using add_module_logger()

# ============================================================================
# MODULE-SPECIFIC LOGGERS
# ============================================================================

def add_module_logger(module_name: str, level: str = None):
    """
    Add a module-specific log file.
    
    Args:
        module_name: Name of the module (e.g., "ingestion", "beliefs")
        level: Log level for this module (defaults to config.LOG_LEVEL)
    """
    if not config.LOG_TO_FILE:
        return
    
    log_level = level or config.LOG_LEVEL
    log_file = config.LOGS_DIR / f"{module_name}.log"
    
    logger.add(
        log_file,
        format=FILE_FORMAT,
        level=log_level,
        rotation=config.LOG_ROTATION,
        retention=config.LOG_RETENTION,
        compression="zip",
        filter=lambda record: module_name in record["name"],  # Only log from this module
        backtrace=True,
        diagnose=True
    )

# ============================================================================
# CONTEXT MANAGER FOR EPISODE LOGGING
# ============================================================================

class EpisodeLogContext:
    """
    Context manager to add episode_id to all log messages.
    
    Usage:
        with EpisodeLogContext(episode_id="episode_001"):
            logger.info("Processing episode")
            # Output: ... | episode_id=episode_001 | Processing episode
    """
    def __init__(self, episode_id: str):
        self.episode_id = episode_id
        self.token = None
    
    def __enter__(self):
        self.token = logger.contextualize(episode_id=self.episode_id)
        self.token.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            self.token.__exit__(exc_type, exc_val, exc_tb)

# ============================================================================
# PERFORMANCE LOGGING
# ============================================================================

def log_performance(func):
    """
    Decorator to log function execution time.
    
    Usage:
        @log_performance
        def my_function():
            ...
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger.debug(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {e}")
            raise
    
    return wrapper

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_api_call(endpoint: str, tokens: int, cost: float, latency: float, success: bool = True):
    """
    Log API call details.
    
    Args:
        endpoint: API endpoint called
        tokens: Number of tokens used
        cost: Cost in USD
        latency: Response time in seconds
        success: Whether call succeeded
    """
    status = "SUCCESS" if success else "FAILED"
    logger.info(
        f"API Call [{status}] | endpoint={endpoint} | "
        f"tokens={tokens} | cost=${cost:.4f} | latency={latency:.2f}s"
    )

def log_checkpoint(phase: str, episode_id: str, count: int, path: Path):
    """
    Log checkpoint save.
    
    Args:
        phase: Pipeline phase (e.g., "beliefs_raw")
        episode_id: Episode identifier
        count: Number of items saved
        path: Checkpoint file path
    """
    logger.info(
        f"Checkpoint saved | phase={phase} | episode_id={episode_id} | "
        f"count={count} | path={path}"
    )

def log_error_with_context(error: Exception, context: dict):
    """
    Log error with additional context.
    
    Args:
        error: Exception that occurred
        context: Dictionary with contextual information
    """
    context_str = " | ".join(f"{k}={v}" for k, v in context.items())
    logger.error(f"Error: {type(error).__name__}: {error} | {context_str}")

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_logging():
    """Initialize logging system."""
    logger.info("=" * 80)
    logger.info("Belief Engine - Logging System Initialized")
    logger.info(f"Log Level: {config.LOG_LEVEL}")
    logger.info(f"Log Directory: {config.LOGS_DIR}")
    logger.info(f"Console Logging: {config.LOG_TO_CONSOLE}")
    logger.info(f"File Logging: {config.LOG_TO_FILE}")
    logger.info("=" * 80)

# Initialize on import
initialize_logging()

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "logger",
    "add_module_logger",
    "EpisodeLogContext",
    "log_performance",
    "log_api_call",
    "log_checkpoint",
    "log_error_with_context",
    "initialize_logging"
]

