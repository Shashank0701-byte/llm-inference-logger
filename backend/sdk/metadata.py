"""
Metadata extraction helpers for inference logs.
"""


# Model-to-provider mapping for common models
MODEL_PROVIDER_MAP = {
    "gpt": "openai",
    "o1": "openai",
    "o3": "openai",
    "o4": "openai",
    "claude": "anthropic",
    "gemini": "google",
    "deepseek": "deepseek",
    "grok": "xai",
    "llama": "meta",
    "mistral": "mistral",
}


def extract_provider(model: str) -> str:
    """
    Extract the provider name from a model identifier.

    Args:
        model: Model string like 'gpt-4.1', 'claude-sonnet-4-20250514', etc.

    Returns:
        Provider name string.
    """
    model_lower = model.lower()

    # Check for explicit provider prefix (e.g., "openai/gpt-4.1")
    if "/" in model_lower:
        return model_lower.split("/")[0]

    # Match against known model prefixes
    for prefix, provider in MODEL_PROVIDER_MAP.items():
        if model_lower.startswith(prefix):
            return provider

    return "unknown"
