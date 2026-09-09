"""CLI Test 1: vcm init command."""

import os
from click.testing import CliRunner
from vcm.cli.main import cli


def test_cli_1_vcm_init(tmp_path):
    """CLI-1: vcm init initializes project correctly."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        assert "VCM initialized successfully" in result.output
        assert os.path.exists(".vcmconfig.yaml")
        assert os.path.isdir(".vcm")
        assert os.path.exists(".vcm/vcm.db")
