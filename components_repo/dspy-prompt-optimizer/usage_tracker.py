"""
Usage tracking for LLM API calls and token consumption.

This module provides utilities to track:
- Number of API calls
- Input/output token counts
- Estimated costs (optional)
"""

from dataclasses import dataclass, field
from typing import Optional
from contextlib import contextmanager
import threading
import time
import logging
from collections import deque

# Configure logging for debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('usage_tracker')


@dataclass
class UsageStats:
    """Statistics for LLM API usage."""
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Optional cost tracking (you can set rates per model)
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    
    def add_call(self, input_tokens: int = 0, output_tokens: int = 0):
        """Record an API call with token counts."""
        self.api_calls += 1
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += input_tokens + output_tokens
    
    def merge(self, other: 'UsageStats'):
        """Merge another UsageStats into this one."""
        self.api_calls += other.api_calls
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens
    
    def reset(self):
        """Reset all counters."""
        self.api_calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
    
    @property
    def estimated_cost(self) -> float:
        """Calculate estimated cost based on token rates."""
        input_cost = (self.input_tokens / 1000) * self.cost_per_1k_input_tokens
        output_cost = (self.output_tokens / 1000) * self.cost_per_1k_output_tokens
        return input_cost + output_cost
    
    def __str__(self) -> str:
        lines = [
            "=" * 50,
            "LLM API USAGE STATISTICS",
            "=" * 50,
            f"API Calls:      {self.api_calls:,}",
            f"Input Tokens:   {self.input_tokens:,}",
            f"Output Tokens:  {self.output_tokens:,}",
            f"Total Tokens:   {self.total_tokens:,}",
        ]
        if self.cost_per_1k_input_tokens > 0 or self.cost_per_1k_output_tokens > 0:
            lines.append(f"Estimated Cost: ${self.estimated_cost:.4f}")
        lines.append("=" * 50)
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "api_calls": self.api_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.estimated_cost
        }


class RateLimiter:
    """
    Rate limiter for API calls.
    
    Enforces a maximum number of API calls within a time window.
    Uses a sliding window approach for accurate rate limiting.
    
    Usage:
        limiter = RateLimiter(max_calls=10, window_seconds=60)
        limiter.wait()  # Wait if needed before making an API call
    """
    
    def __init__(self, max_calls: int = 10, window_seconds: float = 60.0):
        """
        Initialize the rate limiter.
        
        Args:
            max_calls: Maximum number of API calls allowed in the time window (default: 10)
            window_seconds: Time window in seconds (default: 60)
        """
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._call_times: deque = deque()
        self._lock = threading.Lock()
        logger.debug(f"RateLimiter initialized: {max_calls} calls per {window_seconds}s")
    
    def _clean_old_calls(self):
        """Remove call timestamps outside the current window."""
        current_time = time.time()
        cutoff = current_time - self.window_seconds
        while self._call_times and self._call_times[0] < cutoff:
            self._call_times.popleft()
    
    def wait(self):
        """
        Wait if necessary to respect the rate limit.
        
        This method should be called before making an API call.
        It will block if the rate limit has been reached.
        """
        with self._lock:
            self._clean_old_calls()
            
            if len(self._call_times) >= self.max_calls:
                # Calculate how long to wait
                oldest_call = self._call_times[0]
                wait_time = oldest_call + self.window_seconds - time.time()
                
                if wait_time > 0:
                    logger.info(f"⏳ Rate limit reached ({self.max_calls} calls/min). Waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    self._clean_old_calls()
            
            # Record this call
            self._call_times.append(time.time())
            calls_in_window = len(self._call_times)
            logger.debug(f"API call #{calls_in_window}/{self.max_calls} in current window")
    
    def get_remaining_calls(self) -> int:
        """Get the number of remaining calls in the current window."""
        with self._lock:
            self._clean_old_calls()
            return max(0, self.max_calls - len(self._call_times))
    
    def get_wait_time(self) -> float:
        """Get the time to wait before the next call is allowed (0 if no wait needed)."""
        with self._lock:
            self._clean_old_calls()
            if len(self._call_times) < self.max_calls:
                return 0.0
            oldest_call = self._call_times[0]
            return max(0.0, oldest_call + self.window_seconds - time.time())


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(max_calls: int = 10, window_seconds: float = 60.0) -> RateLimiter:
    """
    Get or create the global rate limiter.
    
    Args:
        max_calls: Maximum API calls per time window (default: 10)
        window_seconds: Time window in seconds (default: 60)
        
    Returns:
        The global RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_calls, window_seconds)
    return _rate_limiter


def set_rate_limiter(max_calls: int = 10, window_seconds: float = 60.0) -> RateLimiter:
    """
    Create and set a new global rate limiter.
    
    Args:
        max_calls: Maximum API calls per time window (default: 10)
        window_seconds: Time window in seconds (default: 60)
        
    Returns:
        The new RateLimiter instance
    """
    global _rate_limiter
    _rate_limiter = RateLimiter(max_calls, window_seconds)
    logger.info(f"📊 Rate limiter set: {max_calls} API calls per {window_seconds}s")
    return _rate_limiter


class UsageTracker:
    """
    Global usage tracker for LLM API calls.
    
    This is a singleton that tracks all API calls made through DSPy.
    
    Usage:
        # Start tracking
        UsageTracker.start()
        
        # ... run your optimization ...
        
        # Get stats
        stats = UsageTracker.get_stats()
        print(stats)
        
        # Or use context manager
        with UsageTracker.track() as stats:
            # ... run optimization ...
            pass
        print(stats)
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._stats = UsageStats()
                    cls._instance._tracking = False
                    cls._instance._original_lm = None
                    cls._instance._lm = None
                    cls._instance._initial_history_len = 0
        return cls._instance
    
    @classmethod
    def set_lm(cls, lm):
        """Set the LM instance for history-based tracking."""
        tracker = cls()
        tracker._lm = lm
        # Record initial history length
        if hasattr(lm, 'history'):
            tracker._initial_history_len = len(lm.history)
        else:
            tracker._initial_history_len = 0
    
    @classmethod
    def start(cls, cost_per_1k_input: float = 0.0, cost_per_1k_output: float = 0.0):
        """
        Start tracking API usage.
        
        Args:
            cost_per_1k_input: Cost per 1000 input tokens (optional)
            cost_per_1k_output: Cost per 1000 output tokens (optional)
        """
        tracker = cls()
        tracker._stats.reset()
        tracker._stats.cost_per_1k_input_tokens = cost_per_1k_input
        tracker._stats.cost_per_1k_output_tokens = cost_per_1k_output
        tracker._tracking = True
        # Reset initial history length
        if tracker._lm and hasattr(tracker._lm, 'history'):
            tracker._initial_history_len = len(tracker._lm.history)
        return tracker
    
    @classmethod
    def stop(cls) -> UsageStats:
        """Stop tracking and return the stats."""
        tracker = cls()
        tracker._tracking = False
        # Update stats from LM history before returning
        cls._update_stats_from_history()
        return tracker._stats
    
    @classmethod
    def _update_stats_from_history(cls):
        """Update stats from DSPy LM history."""
        tracker = cls()
        if not tracker._lm or not hasattr(tracker._lm, 'history'):
            return
        
        # Get new history entries since tracking started
        history = tracker._lm.history
        new_entries = history[tracker._initial_history_len:]
        
        for entry in new_entries:
            # Extract token counts from response if available
            input_tokens = 0
            output_tokens = 0
            
            # Try to get token counts from the response metadata
            if isinstance(entry, dict):
                response = entry.get('response', {})
                if hasattr(response, 'usage'):
                    usage = response.usage
                    input_tokens = getattr(usage, 'prompt_tokens', 0) or 0
                    output_tokens = getattr(usage, 'completion_tokens', 0) or 0
                elif isinstance(response, dict) and 'usage' in response:
                    usage = response['usage']
                    input_tokens = usage.get('prompt_tokens', 0) or 0
                    output_tokens = usage.get('completion_tokens', 0) or 0
            
            # If no token info, estimate from content
            if input_tokens == 0 and output_tokens == 0:
                if isinstance(entry, dict):
                    prompt = entry.get('prompt', '') or entry.get('messages', '')
                    response = entry.get('response', '')
                    input_tokens = len(str(prompt)) // 4
                    output_tokens = len(str(response)) // 4
            
            tracker._stats.add_call(input_tokens, output_tokens)
        
        # Update initial length to avoid double counting
        tracker._initial_history_len = len(history)
    
    @classmethod
    def get_stats(cls) -> UsageStats:
        """Get current usage stats without stopping tracking."""
        # Update from history before returning
        cls._update_stats_from_history()
        return cls()._stats
    
    @classmethod
    def reset(cls):
        """Reset the usage stats."""
        tracker = cls()
        tracker._stats.reset()
        if tracker._lm and hasattr(tracker._lm, 'history'):
            tracker._initial_history_len = len(tracker._lm.history)
    
    @classmethod
    def is_tracking(cls) -> bool:
        """Check if tracking is active."""
        return cls()._tracking
    
    @classmethod
    def record_call(cls, input_tokens: int = 0, output_tokens: int = 0):
        """Record an API call manually."""
        tracker = cls()
        if tracker._tracking:
            tracker._stats.add_call(input_tokens, output_tokens)
    
    @classmethod
    @contextmanager
    def track(cls, cost_per_1k_input: float = 0.0, cost_per_1k_output: float = 0.0):
        """
        Context manager for tracking usage.
        
        Example:
            with UsageTracker.track() as stats:
                result = optimizer.optimize(data)
            print(stats)
        """
        cls.start(cost_per_1k_input, cost_per_1k_output)
        stats = cls.get_stats()
        try:
            yield stats
        finally:
            cls.stop()
    
    @classmethod
    def print_stats(cls):
        """Print current usage stats."""
        print(cls.get_stats())


# Gemini pricing (as of 2025 - update as needed)
# See: https://ai.google.dev/pricing
GEMINI_PRICING = {
    "gemini-2.0-flash": {
        "input": 0.0001,     # $0.10 per 1M tokens = $0.0001 per 1K
        "output": 0.0004     # $0.40 per 1M tokens = $0.0004 per 1K
    },
    "gemini-2.0-flash-lite": {
        "input": 0.000075,   # $0.075 per 1M tokens
        "output": 0.0003     # $0.30 per 1M tokens
    },
    "gemini-1.5-flash": {
        "input": 0.000075,   # $0.075 per 1M tokens = $0.000075 per 1K
        "output": 0.0003     # $0.30 per 1M tokens = $0.0003 per 1K
    },
    "gemini-1.5-pro": {
        "input": 0.00125,    # $1.25 per 1M tokens
        "output": 0.005      # $5.00 per 1M tokens
    },
    "gemini-1.0-pro": {
        "input": 0.0005,
        "output": 0.0015
    }
}


def get_gemini_pricing(model_name: str) -> tuple[float, float]:
    """
    Get pricing for a Gemini model.
    
    Returns:
        Tuple of (cost_per_1k_input, cost_per_1k_output)
    """
    # Strip "gemini/" prefix if present
    model = model_name.replace("gemini/", "")
    
    if model in GEMINI_PRICING:
        pricing = GEMINI_PRICING[model]
        return pricing["input"], pricing["output"]
    
    # Default to 2.0 flash pricing
    return GEMINI_PRICING["gemini-2.0-flash"]["input"], GEMINI_PRICING["gemini-2.0-flash"]["output"]
