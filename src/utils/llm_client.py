"""
Shared LLM Client - Caches LLM instances across steps for better performance.

Features:
- Lazy initialization
- Client caching across steps
- No test calls (fails naturally on first use)
- Automatic fallback to backup LLM
- Temperature parameter optional (some models don't support it)
- Provider support for API key selection
- Retry mechanism for connection errors
"""

import os
import time
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from .api_key_selector import get_api_key_for_url
from .cost_tracker import cost_tracker

load_dotenv(os.path.join('config', '.env'))

# Get logger for this module
logger = logging.getLogger('finagent')

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'

# Global cache for LLM clients
_llm_cache = {}

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds


def get_llm_client(model_env_var: str, url_env_var: str, step_name: str, temperature: float = None, top_p: float = None, top_k: int = None, provider_env_var: str = None) -> ChatOpenAI:
    """
    Get or create a cached LLM client for the specified step.

    Args:
        model_env_var: Environment variable name for the model
        url_env_var: Environment variable name for the URL
        step_name: Name of the step (for logging)
        temperature: Temperature parameter (None = don't pass, some models don't support it)
        top_p: Top-p (nucleus) sampling parameter (None = don't pass)
        top_k: Top-k sampling parameter (None = don't pass)
        provider_env_var: Environment variable name for the provider (optional)

    Returns:
        ChatOpenAI instance
    """
    cache_key = f"{model_env_var}:{url_env_var}"

    # Return cached client if available
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    # Get configuration
    model = os.getenv(model_env_var, DEFAULT_MODEL_NAME)
    base_url = os.getenv(url_env_var)
    provider = os.getenv(provider_env_var) if provider_env_var else None
    backup_model = os.getenv('LLM_BACKUP_MODEL', DEFAULT_MODEL_NAME)
    backup_url = os.getenv('LLM_BACKUP_URL')
    backup_key = os.getenv("FINAGENT_ZENMUX_API_KEY") or os.getenv("ZENMUX_API_KEY")  # Backup always uses ZenMux

    # Build kwargs for ChatOpenAI
    def _build_kwargs(model_name, api_key, url, temp, tp_p=None, tp_k=None):
        kwargs = {
            "model": model_name,
            "api_key": api_key,
            "base_url": url,
            "timeout": 120.0,
            "max_retries": 2,
        }
        # Only add temperature if explicitly provided
        if temp is not None:
            kwargs["temperature"] = temp
        if tp_p is not None:
            kwargs["top_p"] = tp_p
        if tp_k is not None:
            kwargs["top_k"] = tp_k
        return kwargs

    # Try primary LLM
    try:
        primary_key = get_api_key_for_url(base_url)
        provider_info = f" (provider: {provider})" if provider else ""
        print(f"DEBUG: {step_name} - Creating LLM client: {model} @ {base_url}{provider_info}")
        llm = ChatOpenAI(**_build_kwargs(model, primary_key, base_url, temperature, top_p, top_k))
        # Cache and return (no test call - fails naturally on first use)
        _llm_cache[cache_key] = llm
        print(f"DEBUG: {step_name} - Primary LLM client created")
        return llm
    except Exception as e:
        print(f"DEBUG: {step_name} - Primary LLM creation failed: {e}")

        # Try backup LLM
        try:
            print(f"DEBUG: {step_name} - Trying backup LLM: {backup_model} @ {backup_url}")
            llm = ChatOpenAI(**_build_kwargs(backup_model, backup_key, backup_url, temperature, top_p, top_k))
            # Cache and return (no test call)
            _llm_cache[cache_key] = llm
            print(f"DEBUG: {step_name} - Backup LLM client created")
            return llm
        except Exception as e2:
            print(f"DEBUG: {step_name} - Backup LLM also failed: {e2}")
            raise Exception(f"Both LLM providers failed for {step_name}. Primary: {e}, Backup: {e2}")


def invoke_llm_with_retry(llm, messages, step_name: str, max_retries: int = MAX_RETRIES) -> str:
    """
    Invoke LLM with retry logic for connection errors.
    Tracks token usage for cost calculation.

    Args:
        llm: ChatOpenAI instance
        messages: List of messages to send
        step_name: Name of the step (for logging)
        max_retries: Maximum number of retries

    Returns:
        Response content string
    """
    for attempt in range(max_retries + 1):
        try:
            response = llm.invoke(messages)

            # Track token usage from response metadata
            try:
                usage = getattr(response, 'usage_metadata', None)
                if usage:
                    model = getattr(llm, 'model', 'unknown')
                    cost_tracker.track(
                        model=model,
                        input_tokens=usage.get('input_tokens', 0),
                        output_tokens=usage.get('output_tokens', 0),
                    )
                else:
                    # Fallback: check response_metadata for usage info
                    meta = getattr(response, 'response_metadata', {})
                    if 'token_usage' in meta:
                        tu = meta['token_usage']
                        model = getattr(llm, 'model', 'unknown')
                        cost_tracker.track(
                            model=model,
                            input_tokens=tu.get('prompt_tokens', 0),
                            output_tokens=tu.get('completion_tokens', 0),
                        )
            except Exception as tracking_error:
                # Don't fail the request if tracking fails
                logger.debug(f"Cost tracking failed for {step_name}: {tracking_error}")

            return response.content
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's a retryable error (connection issues)
            if any(err in error_msg for err in ['broken pipe', 'connection reset', 'connection aborted', 'timeout']):
                if attempt < max_retries:
                    logger.warning(f" [{step_name}] Connection error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
            # Non-retryable error or max retries exceeded
            raise


def clear_llm_cache():
    """Clear the LLM client cache."""
    global _llm_cache
    _llm_cache.clear()
    cost_tracker.reset()
    print("DEBUG: LLM cache and cost tracker cleared")
