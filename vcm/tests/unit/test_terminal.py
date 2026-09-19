"""Unit tests for TerminalLogger and privacy masking."""

import subprocess
from vcm.utils.terminal_logger import TerminalLogger


def test_terminal_capture_print():
    """TerminalLogger captures standard python print statements."""
    logger = TerminalLogger()
    logger.start_capture()
    print("Testing stdout output capture")
    print("Second line from print")
    logs = logger.stop_capture()

    assert "Testing stdout output capture" in logs
    assert "Second line from print" in logs


def test_terminal_capture_subprocess():
    """TerminalLogger captures subprocess output forwarded to standard streams."""
    logger = TerminalLogger()
    logger.start_capture()
    proc = subprocess.run(["echo", "Echoed by subprocess"], capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout.strip())
    logs = logger.stop_capture()

    assert "Echoed by subprocess" in logs


def test_terminal_secret_masking_api_key():
    """Secrets like API_KEY are replaced with ***MASKED***."""
    logger = TerminalLogger()
    raw = "export API_KEY=sk_live_999888777666"
    masked = logger.mask_secrets(raw)
    assert "sk_live_999888777666" not in masked
    assert "***MASKED***" in masked


def test_terminal_secret_masking_password():
    """Passwords are masked."""
    logger = TerminalLogger()
    raw = "database password: super_secret_pass_123"
    masked = logger.mask_secrets(raw)
    assert "super_secret_pass_123" not in masked
    assert "***MASKED***" in masked


def test_terminal_secret_masking_token():
    """Tokens and GitHub tokens are masked."""
    logger = TerminalLogger()
    raw = "github_token=ghp_ABC123XYZ456 and bearer eyJhbGciOi"
    masked = logger.mask_secrets(raw)
    assert "ghp_ABC123XYZ456" not in masked
    assert "eyJhbGciOi" not in masked
    assert "***MASKED***" in masked


def test_terminal_noise_exclusion():
    """Noisy lines like pip install and /bin/ are filtered out."""
    logger = TerminalLogger(include_timestamps=False)
    logger.log_line("Epoch 1/10: loss=0.54, accuracy=0.88")
    logger.log_line("pip install tensorflow torch")
    logger.log_line("npm install -g something")
    logger.log_line("Model saved to disk")

    logs = logger.get_log()
    assert "Epoch 1/10" in logs
    assert "Model saved to disk" in logs
    assert "pip install" not in logs
    assert "npm install" not in logs


def test_terminal_clear():
    """Clearing terminal buffer empties captured text."""
    logger = TerminalLogger()
    logger.log_line("Temporary message")
    assert "Temporary message" in logger.get_log()
    logger.clear()
    assert logger.get_log() == ""
