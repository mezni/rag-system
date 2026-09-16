from src.config.settings import get_settings


def test_settings_load():
    settings = get_settings()

    assert settings.application_name == "rag-system"
    assert settings.environment_name == "dev"
    assert settings.database_url