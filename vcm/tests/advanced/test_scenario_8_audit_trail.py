"""Scenario 8: Production Audit Trail."""

from click.testing import CliRunner

from vcm.cli.main import cli
from vcm.utils.helpers import vcm_audit


def test_scenario_8_production_audit(trained_iris_models):
    """Verify audit trail for production deployment."""
    runner = CliRunner()

    # Deploy iris_classifier_v1 to production
    res = runner.invoke(cli, ["deploy", "iris_classifier_v1.pkl", "--environment", "production"])
    assert res.exit_code == 0, f"Deploy failed: {res.output}"

    # Verify audit trail
    audit_log = vcm_audit(environment="production")

    assert audit_log["model_name"] == "iris_classifier_v1"
    assert "deployment_timestamp" in audit_log
    assert "trained_by" in audit_log
    assert "git_commit" in audit_log
