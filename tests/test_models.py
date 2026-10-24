from unittest.mock import Mock, patch

import pytest

from agent_cli.models import get_model, list_models


def test_list_models():
    with patch(
        "agent_cli.models.settings.models",
        {"gpt": "groq:gpt", "gemini": "google:gemini"},
    ):
        result = list_models()
        assert result == ["gpt", "gemini"]


def test_get_model_default_fallback():
    mock_init = Mock(return_value="mock_chat_model")
    with (
        patch("agent_cli.models.settings.current_model", "groq:default-model"),
        patch.dict("os.environ", {"GROQ_API_KEY": "fake-groq-key"}),
        patch("agent_cli.models.init_chat_model", mock_init),
    ):
        model = get_model()
        assert model == "mock_chat_model"
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["model"] == "default-model"
        assert call_kwargs["model_provider"] == "groq"
        assert call_kwargs["api_key"] == "fake-groq-key"


def test_get_model_by_alias():
    mock_init = Mock(return_value="mock_chat_model")
    fake_models = {"my_gemini": "google:gemini-pro"}
    with (
        patch("agent_cli.models.settings.models", fake_models),
        patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-google-key"}),
        patch("agent_cli.models.init_chat_model", mock_init),
    ):
        model = get_model("my_gemini")
        assert model == "mock_chat_model"
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["model"] == "gemini-pro"
        assert call_kwargs["model_provider"] == "google_genai"


def test_get_model_unsupported_provider():
    with pytest.raises(ValueError, match="Provider 'unsupported' not supported"):
        get_model("unsupported:some-model")


def test_get_model_missing_api_key():
    with (
        patch.dict("os.environ", {}, clear=True),
        pytest.raises(ValueError, match="GOOGLE_API_KEY not found"),
    ):
        get_model("google:gemini-pro")


@pytest.mark.parametrize(
    "provider,expected_lc_provider,api_key_env",
    [
        ("groq", "groq", "GROQ_API_KEY"),
        ("google", "google_genai", "GOOGLE_API_KEY"),
        ("openrouter", "openrouter", "OPENROUTER_API_KEY"),
    ],
)
def test_get_model_supported_providers(provider, expected_lc_provider, api_key_env):
    mock_init = Mock(return_value="mock_model")
    with (
        patch.dict("os.environ", {api_key_env: "test-key"}),
        patch("agent_cli.models.init_chat_model", mock_init),
    ):
        model = get_model(f"{provider}:test-model-id")
        assert model == "mock_model"
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["model"] == "test-model-id"
        assert call_kwargs["model_provider"] == expected_lc_provider
        assert call_kwargs["api_key"] == "test-key"
