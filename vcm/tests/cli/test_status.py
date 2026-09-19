"""CLI Test: vcm status command."""

from click.testing import CliRunner
from vcm.cli.main import cli


def test_vcm_status_uninitialized(tmp_path):
    """Test vcm status returns error when workspace not initialized."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["status"])
        assert result.exit_code != 0
        assert "not initialized" in result.output


def test_vcm_status_initialized(tmp_path):
    """Test vcm status runs successfully on an initialized workspace."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "VCM Workspace Status" in result.output
        assert "Database:" in result.output
        assert "Active Session:" in result.output
        assert "Model Catalog:" in result.output
        assert "Integrations:" in result.output
        assert "Untracked Model Artifacts:" in result.output
