"""
Shared LLM Client - Caches LLM instances across steps for better performance.

Features:
- Lazy initialization
- Client caching across steps
- No test calls (fails naturally on first use)
- Automatic fallback to backup LLM
- Temperature parameter optional (some models don't support it)
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from .api_key_selector import get_api_key_for_url

load_dotenv(os.path.join('config', '.env'))

DEFAULT_MODEL_NAME = 'x-ai/grok-beta'

# Global cache for LLM clients
_llm_cache = {}


def get_llm_client(model_env_var: str, url_env_var: str, step_name: str, temperature: float = None) -> ChatOpenAI:
    """
    Get or create a cached LLM client for the specified step.

    Args:
        model_env_var: Environment variable name for the model
        url_env_var: Environment variable name for the URL
        step_name: Name of the step (for logging)
        temperature: Temperature parameter (None = don't pass, some models don't support it)

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
    backup_model = os.getenv('LLM_BACKUP_MODEL', DEFAULT_MODEL_NAME)
    backup_url = os.getenv('LLM_BACKUP_URL')
    backup_key = os.getenv("ZENMUX_API_KEY")  # Backup always uses ZenMux

    # Build kwargs for ChatOpenAI
    def _build_kwargs(model_name, api_key, url, temp):
        kwargs = {
            "model": model_name,
            "api_key": api_key,
            "base_url": url,
        }
        # Only add temperature if explicitly provided
        if temp is not None:
            kwargs["temperature"] = temp
        return kwargs

    # Try primary LLM
    try:
        primary_key = get_api_key_for_url(base_url)
        print(f"DEBUG: {step_name} - Creating LLM client: {model} @ {base_url}")
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


def clear_llm_cache():
    """Clear the LLM client cache."""
    global _llm_cache
    _llm_cache.clear()
    print("DEBUG: LLM cache cleared")
