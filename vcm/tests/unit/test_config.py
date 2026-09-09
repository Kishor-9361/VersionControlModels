import os
from vcm.config import VCMConfig


def test_vcm_config_defaults(tmp_path):
    """Test default config creation and paths."""
    config_path = str(tmp_path / ".vcmconfig.yaml")
    config = VCMConfig(config_path=config_path)

    assert not config.is_initialized()
    assert config.database_path == ".vcm/vcm.db"
    assert config.models_dir == "models"
    assert "git" in config.get_enabled_integrations()
    assert "dvc" in config.get_enabled_integrations()


def test_vcm_config_save_and_load(tmp_path):
    """Test saving config to YAML and loading it back."""
    config_path = str(tmp_path / ".vcmconfig.yaml")
    config = VCMConfig(
        config_path=config_path,
        database_path=".custom/custom.db",
        models_dir="checkpoints",
        git_enabled=True,
        dvc_enabled=False,
    )
    config.save()
    assert os.path.exists(config_path)
    assert config.is_initialized()

    loaded = VCMConfig.load(config_path=config_path)
    assert loaded.database_path == ".custom/custom.db"
    assert loaded.models_dir == "checkpoints"
    assert loaded.dvc_enabled is False
    assert loaded.get_enabled_integrations() == ["git"]


def test_vcm_config_missing_or_invalid_file(tmp_path):
    """Test graceful handling of missing or corrupted config file."""
    non_existent = str(tmp_path / "non_existent.yaml")
    config = VCMConfig.load(config_path=non_existent)
    assert config.database_path == ".vcm/vcm.db"

    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("invalid: yaml: content: [}")
    loaded_bad = VCMConfig.load(config_path=str(bad_config))
    assert loaded_bad.database_path == ".vcm/vcm.db"
