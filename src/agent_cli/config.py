from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent.parent


class StatusbarConfig(BaseModel):
    theme: str = "tokyo_night"
    bg: str | None = None
    fg: str | None = None
    model_color: str | None = None
    thread_color: str | None = None
    memory_color: str | None = None
    help_color: str | None = None


class Settings(BaseModel):
    current_model: str
    temperature: float = Field(ge=0, le=2)
    workspace_dir: Path
    data_dir: Path
    export_dir: Path
    models: dict[str, str]
    statusbar: StatusbarConfig = Field(default_factory=StatusbarConfig)


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")

    config_path = ROOT / "config.yaml"
    with config_path.open("r") as f:
        config = yaml.safe_load(f)

    settings = Settings(**config)
    settings.workspace_dir = (
        Path(__file__).home() / ".forge/" / Path(settings.workspace_dir)
    )
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir = Path(__file__).home() / ".forge/" / Path(settings.data_dir)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.export_dir = Path(__file__).home() / ".forge/" / Path(settings.export_dir)
    settings.export_dir.mkdir(parents=True, exist_ok=True)

    return settings


def set_current_model(key: str):
    """set the current model as <key>"""
    if key not in settings.models:
        raise ValueError(f"{key} not found")
    settings.current_model = settings.models[key]


def set_theme(theme_name: str) -> bool:
    """Set the statusbar theme dynamically and persist to config.yaml."""
    from agent_cli.ui.statusline import THEMES

    if theme_name not in THEMES:
        raise ValueError(f"Theme '{theme_name}' not found. Available: {', '.join(THEMES.keys())}")
    settings.statusbar.theme = theme_name

    try:
        config_path = ROOT / "config.yaml"
        if config_path.exists():
            with config_path.open("r") as f:
                data = yaml.safe_load(f) or {}
            data.setdefault("statusbar", {})["theme"] = theme_name
            with config_path.open("w") as f:
                yaml.safe_dump(data, f, sort_keys=False)
    except Exception:  # noqa: BLE001
        pass
    return True


settings = load_settings()

