import yaml
import pytest

from vcm.integrations.dvc_client import DVCClient
from vcm.models.metadata import DVCFileInfo


@pytest.fixture
def temp_dvc_repo(tmp_path):
    """Fixture creating a mock DVC repository layout."""
    dvc_dir = tmp_path / ".dvc"
    dvc_dir.mkdir()
    (dvc_dir / "config").write_text("[core]\n")

    # Create a tracked data file
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_file = data_dir / "train.csv"
    data_file.write_text("id,feature,label\n1,0.5,1\n2,0.8,0\n")

    # Create corresponding data/train.csv.dvc file
    dvc_meta = {
        "outs": [
            {
                "md5": "a1b2c3d4e5f678901234567890123456",
                "size": 33,
                "path": "train.csv",
            }
        ]
    }
    (data_dir / "train.csv.dvc").write_text(yaml.safe_dump(dvc_meta))

    return tmp_path


def test_ut_3_1_dvc_client_get_tracked_files(temp_dvc_repo):
    """UT-3.1: DVCClient.get_tracked_files() returns all DVC-tracked files."""
    client = DVCClient(repo_path=str(temp_dvc_repo))
    files = client.get_tracked_files()

    assert len(files) == 1
    dvc_file = files[0]
    assert isinstance(dvc_file, DVCFileInfo)
    assert dvc_file.dvc_hash == "a1b2c3d4e5f678901234567890123456"
    assert dvc_file.size_bytes == 33
    assert "train.csv" in dvc_file.path


def test_ut_3_2_dvc_client_get_file_hash(temp_dvc_repo):
    """UT-3.2: DVCClient.get_file_hash(filepath) returns DVC hash."""
    client = DVCClient(repo_path=str(temp_dvc_repo))
    data_path = str(temp_dvc_repo / "data" / "train.csv")

    h1 = client.get_file_hash(data_path)
    h2 = client.get_file_hash(data_path)
    assert h1 is not None
    assert h1 == h2
    assert h1 == "a1b2c3d4e5f678901234567890123456"


def test_ut_3_3_dvc_client_detect_initialization(temp_dvc_repo, tmp_path):
    """UT-3.3: DVCClient.is_initialized() correctly detects DVC setup."""
    client_dvc = DVCClient(repo_path=str(temp_dvc_repo))
    assert client_dvc.is_initialized() is True

    non_dvc = tmp_path / "plain_dir"
    non_dvc.mkdir()
    client_plain = DVCClient(repo_path=str(non_dvc))
    assert client_plain.is_initialized() is False


def test_ut_3_4_dvc_client_handle_missing_dvc(tmp_path):
    """UT-3.4: DVCClient gracefully handles when DVC not installed or uninitialized."""
    client = DVCClient(repo_path=str(tmp_path))
    files = client.get_tracked_files()
    assert files == []

    data_info = client.get_data_info()
    assert data_info.dvc_files == []

    # Non-existent file hash returns None
    assert client.get_file_hash("nonexistent.csv") is None


def test_dvc_client_lock_file_and_dataset_path(tmp_path):
    """Test dvc.lock parsing and get_data_info with specific dataset_path."""
    dvc_dir = tmp_path / ".dvc"
    dvc_dir.mkdir()

    # Create a raw dataset file
    raw_data = tmp_path / "raw.csv"
    raw_data.write_text("a,b\n1,2\n")

    # Create dvc.lock
    lock_data = {
        "stages": {
            "train": {
                "outs": [
                    {
                        "path": "data/processed.csv",
                        "md5": "locked_md5_hash_12345",
                        "size": 50,
                    }
                ]
            }
        }
    }
    (tmp_path / "dvc.lock").write_text(yaml.safe_dump(lock_data))

    client = DVCClient(repo_path=str(tmp_path))
    files = client.get_tracked_files()
    assert len(files) == 1
    assert files[0].dvc_hash == "locked_md5_hash_12345"

    data_info = client.get_data_info(dataset_path="raw.csv")
    assert len(data_info.dvc_files) == 2
    paths = [f.path for f in data_info.dvc_files]
    assert "raw.csv" in paths
