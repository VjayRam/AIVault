"""
DSPy Prompt Optimizer with Google Gemini API

A simple automatic prompt optimizer that finds flaws in prompts and improves them
iteratively using quality metrics.
"""

import os
import logging
import dspy
from dotenv import load_dotenv
from usage_tracker import UsageTracker, get_gemini_pricing, set_rate_limiter

# Configure logging for debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('config')

# Load environment variables
load_dotenv()


def configure_gemini(
    model_name: str = "gemini-2.0-flash", 
    api_key: str = None,
    track_usage: bool = True,
    rate_limit_calls: int = 10,
    rate_limit_window: float = 60.0
):
    """
    Configure DSPy to use Google Gemini API.
    
    Args:
        model_name: The Gemini model to use. Options:
            - "gemini-2.0-flash" (default, fast and efficient)
            - "gemini-2.0-flash-lite" (faster, cheaper)
            - "gemini-1.5-pro" (more capable)
            - "gemini-1.5-flash" (legacy)
        api_key: Google API key (if not provided, reads from GOOGLE_API_KEY env var)
        track_usage: Whether to track API calls and token usage (default: True)
        rate_limit_calls: Maximum API calls per time window (default: 10)
        rate_limit_window: Time window in seconds for rate limiting (default: 60.0)
        
    Returns:
        The configured LM instance
    """
    logger.info(f"\ud83d\ude80 Configuring DSPy with Gemini model: {model_name}")
    
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Set it in .env file or pass it directly."
        )
    
    logger.debug("API key loaded successfully")
    
    # Set up rate limiter
    set_rate_limiter(max_calls=rate_limit_calls, window_seconds=rate_limit_window)
    logger.info(f"\u23f1\ufe0f  Rate limiter configured: {rate_limit_calls} calls per {rate_limit_window}s")
    
    lm = dspy.LM(
        model=f"gemini/{model_name}",
        api_key=api_key,
        max_tokens=1024
    )
    logger.debug(f"LM instance created with max_tokens=1024")
    
    # Start usage tracking if requested
    if track_usage:
        # Start tracking with Gemini pricing
        input_cost, output_cost = get_gemini_pricing(model_name)
        UsageTracker.start(cost_per_1k_input=input_cost, cost_per_1k_output=output_cost)
        # Store the LM reference for history-based tracking
        UsageTracker.set_lm(lm)
        logger.info(f"\ud83d\udcca Usage tracking enabled (pricing: ${input_cost}/1K input, ${output_cost}/1K output)")
    
    dspy.configure(lm=lm)
    logger.info("\u2705 DSPy configured successfully")
    return lm
