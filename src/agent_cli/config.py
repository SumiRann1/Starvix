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
    models: dict[str, str]
    statusbar: StatusbarConfig = Field(default_factory=StatusbarConfig)

    
def load_settings() -> Settings:
    load_dotenv(ROOT/".env")

    config_path = ROOT/"config.yaml"
    with config_path.open("r") as f:
        config = yaml.safe_load(f)

    settings = Settings(**config)
    settings.workspace_dir = ROOT/settings.workspace_dir
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)
    settings.data_dir = ROOT/settings.data_dir
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings

def set_current_model(key: str):
    """set the current model as <key>"""
    if key not in settings.models:
        raise ValueError(f"{key} not found")
    settings.current_model = settings.models[key]
    
settings = load_settings()

