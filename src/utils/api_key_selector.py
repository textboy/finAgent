"""
API Key Selector - Selects the correct API key based on the URL prefix.

URL Prefix Mapping:
- https://zenmux* → FINAGENT_ZENMUX_API_KEY (fallback: ZENMUX_API_KEY)
- https://apihub.agnes-ai* → AGNES_API_KEY
- https://integrate.api.nvidia* → NVIDIA_API_KEY
- https://api.deepseek* → DEEPSEEK_API_KEY
- https://open.bigmodel* → BIGMODEL_API_KEY
- https://api.minimax* → MINIMAX_API_KEY
"""

import os


def get_api_key_for_url(url: str) -> str:
    """
    Get the appropriate API key based on the URL prefix.

    Args:
        url: The API base URL

    Returns:
        The API key for the given URL, or None if not found
    """
    if not url:
        return None

    url_lower = url.lower()

    if url_lower.startswith("https://zenmux"):
        return os.getenv("FINAGENT_ZENMUX_API_KEY") or os.getenv("ZENMUX_API_KEY")
    elif url_lower.startswith("https://apihub.agnes-ai"):
        return os.getenv("AGNES_API_KEY")
    elif url_lower.startswith("https://integrate.api.nvidia"):
        return os.getenv("NVIDIA_API_KEY")
    elif url_lower.startswith("https://api.deepseek"):
        return os.getenv("DEEPSEEK_API_KEY")
    elif url_lower.startswith("https://open.bigmodel"):
        return os.getenv("BIGMODEL_API_KEY")
    elif url_lower.startswith("https://api.minimax"):
        return os.getenv("MINIMAX_API_KEY")
    else:
        # Fallback to FINAGENT_ZENMUX_API_KEY for unknown URLs
        return os.getenv("FINAGENT_ZENMUX_API_KEY") or os.getenv("ZENMUX_API_KEY")


def get_api_key_for_url_with_fallback(url: str) -> tuple:
    """
    Get the appropriate API key with fallback information.

    Args:
        url: The API base URL

    Returns:
        Tuple of (api_key, provider_name)
    """
    if not url:
        return None, "unknown"

    url_lower = url.lower()

    if url_lower.startswith("https://zenmux"):
        return os.getenv("FINAGENT_ZENMUX_API_KEY") or os.getenv("ZENMUX_API_KEY"), "ZenMux"
    elif url_lower.startswith("https://apihub.agnes-ai"):
        return os.getenv("AGNES_API_KEY"), "Agnes AI"
    elif url_lower.startswith("https://integrate.api.nvidia"):
        return os.getenv("NVIDIA_API_KEY"), "NVIDIA"
    else:
        # Fallback to FINAGENT_ZENMUX_API_KEY for unknown URLs
        return os.getenv("FINAGENT_ZENMUX_API_KEY") or os.getenv("ZENMUX_API_KEY"), "ZenMux (fallback)"
