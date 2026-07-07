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

load_dotenv(os.path.join('config', '.env'))

# Get logger for this module
logger = logging.getLogger('finagent')

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'

# Global cache for LLM clients
_llm_cache = {}

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds


def get_llm_client(model_env_var: str, url_env_var: str, step_name: str, temperature: float = None, provider_env_var: str = None) -> ChatOpenAI:
    """
    Get or create a cached LLM client for the specified step.

    Args:
        model_env_var: Environment variable name for the model
        url_env_var: Environment variable name for the URL
        step_name: Name of the step (for logging)
        temperature: Temperature parameter (None = don't pass, some models don't support it)
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
    backup_key = os.getenv("ZENMUX_API_KEY")  # Backup always uses ZenMux

    # Build kwargs for ChatOpenAI
    def _build_kwargs(model_name, api_key, url, temp):
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
        return kwargs

    # Try primary LLM
    try:
        primary_key = get_api_key_for_url(base_url)
        provider_info = f" (provider: {provider})" if provider else ""
        print(f"DEBUG: {step_name} - Creating LLM client: {model} @ {base_url}{provider_info}")
        llm = ChatOpenAI(**_build_kwargs(model, primary_key, base_url, temperature))
        # Cache and return (no test call - fails naturally on first use)
        _llm_cache[cache_key] = llm
        print(f"DEBUG: {step_name} - Primary LLM client created")
        return llm
    except Exception as e:
        print(f"DEBUG: {step_name} - Primary LLM creation failed: {e}")

        # Try backup LLM
        try:
            print(f"DEBUG: {step_name} - Trying backup LLM: {backup_model} @ {backup_url}")
            llm = ChatOpenAI(**_build_kwargs(backup_model, backup_key, backup_url, temperature))
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
    print("DEBUG: LLM cache cleared")
