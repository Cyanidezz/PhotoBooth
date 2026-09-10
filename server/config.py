from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    capture_device: int | str = 0
    capture_width: int = 1920
    capture_height: int = 1080
    gphoto2: str = "gphoto2"
    camera_filename: str = "capture-%Y%m%d-%H%M%S.jpg"
    output_directory: str = "output"
    printer: str = ""

    @property
    def output_path(self) -> Path:
        path = ROOT / self.output_directory
        path.mkdir(parents=True, exist_ok=True)
        return path


def load_settings() -> Settings:
    path = ROOT / "config.json"
    if not path.exists():
        return Settings()
    raw = json.loads(path.read_text(encoding="utf-8"))
    allowed = Settings.__dataclass_fields__.keys()
    return Settings(**{key: value for key, value in raw.items() if key in allowed})

