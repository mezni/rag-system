"""Configuration loading and validation."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class FilesystemConfig(BaseModel):
    input_dir: Path
    processed_dir: Path
    archive: bool


class SourcesConfig(BaseModel):
    filesystem: FilesystemConfig


class AppConfig(BaseModel):
    sources: SourcesConfig

    @classmethod
    def from_yaml(cls, path: str | Path = "config/app.yaml") -> "AppConfig":
        with Path(path).open() as fh:
            raw = yaml.safe_load(fh)
        return cls.model_validate(raw)

    @property
    def filesystem(self) -> FilesystemConfig:
        return self.sources.filesystem