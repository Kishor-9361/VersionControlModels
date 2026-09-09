"""Unit tests for MetricsLoader (UT-5.1 to UT-5.4)."""

import json
import pytest
from vcm.utils.metrics_loader import MetricsLoader


def test_ut_5_1_load_metrics_from_json_file(tmp_path):
    """UT-5.1: MetricsLoader.from_json_file(path) reads metrics."""
    metrics_path = tmp_path / "metrics.json"
    metrics_data = {"accuracy": 0.942, "f1_score": 0.928, "loss": 0.05}
    metrics_path.write_text(json.dumps(metrics_data))

    loaded = MetricsLoader.from_json_file(str(metrics_path))
    assert loaded["accuracy"] == 0.942
    assert loaded["f1_score"] == 0.928
    assert loaded["loss"] == 0.05


def test_ut_5_2_load_metrics_from_dict():
    """UT-5.2: MetricsLoader.from_dict(d) accepts runtime metrics."""
    raw = {"accuracy": 0.94, "precision": 0.91, "ignored_str": "val"}
    loaded = MetricsLoader.from_dict(raw)
    assert loaded["accuracy"] == 0.94
    assert loaded["precision"] == 0.91
    # raw dictionary should not be mutated
    assert "ignored_str" in raw


def test_ut_5_3_load_metrics_file_not_found(caplog):
    """UT-5.3: MetricsLoader handles missing file."""
    loaded = MetricsLoader.from_json_file("/non/existent/path/metrics.json")
    assert loaded == {}


def test_ut_5_4_load_metrics_invalid_json(tmp_path, caplog):
    """UT-5.4: MetricsLoader handles malformed JSON."""
    bad_path = tmp_path / "bad_metrics.json"
    bad_path.write_text("{ malformed json content")

    loaded = MetricsLoader.from_json_file(str(bad_path))
    assert loaded == {}


def test_parse_cli_params():
    """Test CLI parameter parsing for key=value pairs."""
    params = ["lr=0.001", "epochs=50", "batch_size=32", "use_gpu=true", "model_type=resnet"]
    parsed = MetricsLoader.parse_cli_params(params)
    assert parsed["lr"] == 0.001
    assert parsed["epochs"] == 50
    assert parsed["batch_size"] == 32
    assert parsed["use_gpu"] is True
    assert parsed["model_type"] == "resnet"
    assert MetricsLoader.parse_cli_params([]) == {}
    assert MetricsLoader.parse_cli_params(["invalid_no_equals"]) == {}


def test_hashing_utilities(tmp_path):
    """Test file and data hashing."""
    from vcm.utils.hashing import compute_file_hash, compute_data_hash

    test_file = tmp_path / "model.bin"
    test_file.write_bytes(b"sample model weights data")

    h = compute_file_hash(str(test_file))
    assert h.startswith("sha256:")
    assert len(h) == 7 + 64

    dh = compute_data_hash(b"sample model weights data")
    assert dh == h

    with pytest.raises(FileNotFoundError):
        compute_file_hash(str(tmp_path / "non_existent.bin"))
