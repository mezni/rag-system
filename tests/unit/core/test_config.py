from pathlib import Path

import pytest

from src.core.config import AppConfig, FilesystemConfig


def test_from_yaml_parses_fields(tmp_path: Path) -> None:
    yaml_content = """
sources:
  filesystem:
    input_dir: data/raw
    processed_dir: data/processed
    archive: true
"""
    config_path = tmp_path / "app.yaml"
    config_path.write_text(yaml_content)

    config = AppConfig.from_yaml(config_path)

    assert config.filesystem == FilesystemConfig(
        input_dir=Path("data/raw"),
        processed_dir=Path("data/processed"),
        archive=True,
    )


def test_from_yaml_false_archive(tmp_path: Path) -> None:
    yaml_content = """
sources:
  filesystem:
    input_dir: data/raw
    processed_dir: data/processed
    archive: false
"""
    config_path = tmp_path / "app.yaml"
    config_path.write_text(yaml_content)

    config = AppConfig.from_yaml(config_path)

    assert config.filesystem.archive is False


def test_from_yaml_default_path() -> None:
    config = AppConfig.from_yaml()

    assert config.filesystem.input_dir == Path("data/raw")
    assert config.filesystem.processed_dir == Path("data/processed")
    assert config.filesystem.archive is True


def test_from_yaml_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        AppConfig.from_yaml(missing_path)