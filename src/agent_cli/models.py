import os
from langchain.chat_models import init_chat_model

from .config import settings

PROVIDERS = {
    "groq": {
        "api_key_env": "GROQ_API_KEY",
        "lc_provider": "groq",
        "extra": {},
    },
    "google": {
        "api_key_env": "GOOGLE_API_KEY",
        "lc_provider": "google_genai",
        "extra": {},
    },
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "lc_provider": "openrouter",
        "extra": {},
    },
}

def get_model(model_name: str | None = None):
    """Select a Particular model to use it"""
    model_str = model_name or settings.current_model
    if model_str in settings.models:
        model_str = settings.models[model_str]

    provider_name, model_id = model_str.split(":", 1)
    if provider_name not in PROVIDERS:
        raise ValueError(f"Provider '{provider_name}' not supported. Supported providers: {list(PROVIDERS.keys())}")

    config = PROVIDERS[provider_name]
    api_key = os.getenv(config["api_key_env"])
    if not api_key:
        raise ValueError(f"{config['api_key_env']} not found")
    return init_chat_model(
        model=model_id,
        api_key=api_key,
        model_provider=config["lc_provider"],
        temperature=settings.temperature,
        **config["extra"],
    )

def list_models():
    return list(settings.models.keys())
