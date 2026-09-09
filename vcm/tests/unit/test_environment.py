import sys
from vcm.utils.environment import EnvironmentCapture


def test_ut_6_1_get_python_version():
    """UT-6.1: EnvironmentCapture.get_python_version() returns valid version."""
    py_ver = EnvironmentCapture.get_python_version()
    assert isinstance(py_ver, str)
    assert len(py_ver) > 0
    expected_major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert py_ver.startswith(expected_major_minor)


def test_ut_6_2_get_installed_libraries():
    """UT-6.2: EnvironmentCapture.get_libraries() returns package versions."""
    libs = EnvironmentCapture.get_libraries()
    assert isinstance(libs, dict)
    # At least pytest or click or pyyaml should be present in our venv
    assert any(pkg in libs for pkg in ["pytest", "click", "pyyaml", "GitPython"])

    # Gracefully handles missing package query
    custom_libs = EnvironmentCapture.get_libraries(["non_existent_package_xyz", "click"])
    assert "click" in custom_libs
    assert "non_existent_package_xyz" not in custom_libs


def test_ut_6_3_get_system_info():
    """UT-6.3: EnvironmentCapture.get_system_info() returns hostname, OS, user."""
    info = EnvironmentCapture.get_system_info()
    assert isinstance(info, dict)
    assert "hostname" in info
    assert "os" in info
    assert "user" in info
    assert "timestamp" in info
    assert len(info["hostname"]) > 0


def test_capture_all():
    """Test full environment capture bundle."""
    all_env = EnvironmentCapture.capture_all()
    assert "python_version" in all_env
    assert "libraries" in all_env
    assert "system" in all_env
