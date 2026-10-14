from pathlib import Path

from app.factory import build_repository, create_app
from app.settings import load_settings

settings = load_settings(Path(__file__).parent.parent / "secret.toml")
app = create_app(settings, build_repository(settings))
