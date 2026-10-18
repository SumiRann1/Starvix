from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from pydantic import ValidationError

from agent_cli.config import Settings, load_settings, set_current_model, settings


def test_settings_validation_temperature_bounds():
    valid_data = {
        "current_model": "test:model",
        "temperature": 0.5,
        "workspace_dir": "workspaces",
        "data_dir": "data",
        "models": {"test": "test:model"},
    }
    s = Settings(**valid_data)
    assert s.temperature == 0.5

    # Boundary: 0 and 2 are allowed
    assert Settings(**{**valid_data, "temperature": 0.0}).temperature == 0.0
    assert Settings(**{**valid_data, "temperature": 2.0}).temperature == 2.0

    # Outside bounds (< 0 or > 2) should raise ValidationError
    with pytest.raises(ValidationError):
        Settings(**{**valid_data, "temperature": -0.1})

    with pytest.raises(ValidationError):
        Settings(**{**valid_data, "temperature": 2.1})


def test_load_settings(tmp_path):
    dummy_yaml = """
current_model: "google:gemini-test"
temperature: 0.8
workspace_dir: "test_ws"
data_dir: "test_data"
models:
  gemini: "google:gemini-test"
"""
    with (
        patch("dotenv.load_dotenv"),
        patch.object(Path, "open", mock_open(read_data=dummy_yaml)),
        patch.object(Path, "mkdir") as mock_mkdir,
    ):
        loaded = load_settings()
        assert loaded.current_model == "google:gemini-test"
        assert loaded.temperature == 0.8
        assert "gemini" in loaded.models
        assert mock_mkdir.call_count >= 2


def test_set_current_model_success():
    with patch.object(settings, "models", {"model_a": "provider:model-a"}):
        set_current_model("model_a")
        assert settings.current_model == "provider:model-a"


def test_set_current_model_not_found():
    with (
        patch.object(settings, "models", {"model_a": "provider:model-a"}),
        pytest.raises(ValueError, match="not_existing not found"),
    ):
        set_current_model("not_existing")
