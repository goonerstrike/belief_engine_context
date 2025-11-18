"""
Parallelization with rate limiting for Belief Engine.
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Optional
from collections import deque
from loguru import logger
import config

# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Tracks both requests per minute (RPM) and tokens per minute (TPM).
    
    Usage:
        limiter = RateLimiter(rpm=3500, tpm=90000)
        with limiter:
            limiter.wait_if_needed(tokens=150)
            # Make API call
    """
    
    def __init__(self, rpm: int = None, tpm: int = None):
        """
        Initialize rate limiter.
        
        Args:
            rpm: Requests per minute limit
            tpm: Tokens per minute limit
        """
        self.rpm = rpm or config.API_RATE_LIMIT_RPM
        self.tpm = tpm or config.API_RATE_LIMIT_TPM
        
        # Request tracking
        self.request_times = deque()
        
        # Token tracking
        self.token_counts = deque()  # (timestamp, token_count) tuples
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        logger.info(f"Rate limiter initialized | RPM={self.rpm} | TPM={self.tpm}")
    
    def _clean_old_entries(self, current_time: float):
        """Remove entries older than 60 seconds."""
        cutoff = current_time - 60
        
        # Clean request times
        while self.request_times and self.request_times[0] < cutoff:
            self.request_times.popleft()
        
        # Clean token counts
        while self.token_counts and self.token_counts[0][0] < cutoff:
            self.token_counts.popleft()
    
    def wait_if_needed(self, tokens: int = 0) -> float:
        """
        Wait if rate limits would be exceeded.
        
        Args:
            tokens: Number of tokens for this request
        
        Returns:
            Time waited in seconds
        """
        with self.lock:
            current_time = time.time()
            self._clean_old_entries(current_time)
            
            wait_time = 0.0
            
            # Check RPM limit
            if len(self.request_times) >= self.rpm:
                # Calculate wait time until oldest request expires
                oldest_request = self.request_times[0]
                rpm_wait = 60 - (current_time - oldest_request) + 0.1  # Add buffer
                wait_time = max(wait_time, rpm_wait)
            
            # Check TPM limit
            if tokens > 0:
                current_tokens = sum(count for _, count in self.token_counts)
                if current_tokens + tokens > self.tpm:
                    # Calculate wait time until enough tokens are available
                    oldest_token_time = self.token_counts[0][0] if self.token_counts else current_time
                    tpm_wait = 60 - (current_time - oldest_token_time) + 0.1  # Add buffer
                    wait_time = max(wait_time, tpm_wait)
            
            # Wait if needed
            if wait_time > 0:
                logger.warning(f"Rate limit approaching, waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                current_time = time.time()
                self._clean_old_entries(current_time)
            
            # Record this request
            self.request_times.append(current_time)
            if tokens > 0:
                self.token_counts.append((current_time, tokens))
            
            return wait_time
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# ============================================================================
# PARALLEL EXECUTOR
# ============================================================================

class ParallelExecutor:
    """
    Execute tasks in parallel with rate limiting.
    
    Usage:
        executor = ParallelExecutor(max_workers=5)
        results = executor.map(process_func, items)
    """
    
    def __init__(
        self,
        max_workers: int = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum parallel workers
            rate_limiter: Optional rate limiter
        """
        self.max_workers = max_workers or config.MAX_WORKERS
        self.rate_limiter = rate_limiter
        
        logger.info(f"Parallel executor initialized | max_workers={self.max_workers}")
    
    def map(
        self,
        func: Callable,
        items: List[Any],
        show_progress: bool = True
    ) -> List[Any]:
        """
        Map function over items in parallel.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            show_progress: Whether to show progress
        
        Returns:
            List of results
        """
        if not config.ENABLE_PARALLEL or self.max_workers == 1:
            # Sequential execution
            return [func(item) for item in items]
        
        results = [None] * len(items)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, item): i
                for i, item in enumerate(items)
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                    completed += 1
                    
                    if show_progress and completed % 10 == 0:
                        logger.info(f"Progress: {completed}/{len(items)} completed")
                        
                except Exception as e:
                    logger.error(f"Task {index} failed: {e}")
                    results[index] = None
        
        logger.info(f"Parallel execution completed | total={len(items)}")
        
        return results
    
    def map_with_rate_limit(
        self,
        func: Callable,
        items: List[Any],
        token_estimator: Optional[Callable[[Any], int]] = None,
        show_progress: bool = True
    ) -> List[Any]:
        """
        Map function over items in parallel with rate limiting.
        
        Args:
            func: Function to apply to each item
            items: List of items to process
            token_estimator: Optional function to estimate tokens for an item
            show_progress: Whether to show progress
        
        Returns:
            List of results
        """
        if self.rate_limiter is None:
            return self.map(func, items, show_progress)
        
        def wrapped_func(item):
            # Estimate tokens
            tokens = token_estimator(item) if token_estimator else 0
            
            # Wait if needed
            self.rate_limiter.wait_if_needed(tokens)
            
            # Execute function
            return func(item)
        
        return self.map(wrapped_func, items, show_progress)

# ============================================================================
# BATCH PROCESSOR
# ============================================================================

def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split items into batches.
    
    Args:
        items: List of items
        batch_size: Size of each batch
    
    Returns:
        List of batches
    """
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches

def process_in_batches(
    func: Callable,
    items: List[Any],
    batch_size: int = None,
    parallel: bool = True
) -> List[Any]:
    """
    Process items in batches.
    
    Args:
        func: Function to apply to each batch
        items: List of items
        batch_size: Size of each batch (default: config.BATCH_SIZE)
        parallel: Whether to process batches in parallel
    
    Returns:
        Flattened list of results
    """
    batch_size = batch_size or config.BATCH_SIZE
    batches = batch_items(items, batch_size)
    
    logger.info(f"Processing {len(items)} items in {len(batches)} batches")
    
    if parallel and config.ENABLE_PARALLEL:
        executor = ParallelExecutor()
        batch_results = executor.map(func, batches)
    else:
        batch_results = [func(batch) for batch in batches]
    
    # Flatten results
    results = []
    for batch_result in batch_results:
        if batch_result:
            results.extend(batch_result)
    
    return results

# ============================================================================
# WORKER UTILIZATION TRACKER
# ============================================================================

class WorkerUtilizationTracker:
    """
    Track parallel worker utilization for W&B metrics.
    
    Usage:
        tracker = WorkerUtilizationTracker(max_workers=5)
        with tracker.task():
            # Do work
        utilization = tracker.get_utilization()
    """
    
    def __init__(self, max_workers: int = None):
        """
        Initialize tracker.
        
        Args:
            max_workers: Maximum workers
        """
        self.max_workers = max_workers or config.MAX_WORKERS
        self.active_workers = 0
        self.lock = threading.Lock()
    
    def task(self):
        """Context manager for tracking a task."""
        return self._TaskContext(self)
    
    class _TaskContext:
        def __init__(self, tracker):
            self.tracker = tracker
        
        def __enter__(self):
            with self.tracker.lock:
                self.tracker.active_workers += 1
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            with self.tracker.lock:
                self.tracker.active_workers -= 1
    
    def get_utilization(self) -> float:
        """
        Get current worker utilization (0.0 to 1.0).
        
        Returns:
            Utilization ratio
        """
        with self.lock:
            return self.active_workers / self.max_workers

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "RateLimiter",
    "ParallelExecutor",
    "batch_items",
    "process_in_batches",
    "WorkerUtilizationTracker",
]

