import json
import git
import pytest
import yaml

from vcm.db.database import Database
from vcm.integrations.dvc_client import DVCClient
from vcm.integrations.git_client import GitClient
from vcm.models.metadata import (
    MetadataModel,
    TrainingInfo,
    EnvironmentInfo,
)
from vcm.utils.environment import EnvironmentCapture
from vcm.utils.hashing import compute_file_hash


@pytest.fixture
def integrated_project(tmp_path):
    """Setup a full test project with Git, DVC mock, and models dir."""
    repo = git.Repo.init(tmp_path)
    (tmp_path / "README.md").write_text("# ML Integrated Project")
    repo.index.add(["README.md"])
    repo.index.commit("Initial repo commit")
    repo.create_remote("origin", "https://github.com/team/integrated-ml.git")

    # DVC setup
    dvc_dir = tmp_path / ".dvc"
    dvc_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    data_csv = data_dir / "train.csv"
    data_csv.write_text("feature1,feature2,target\n1.0,2.0,1\n3.0,4.0,0\n")

    dvc_data = {
        "outs": [
            {
                "path": "train.csv",
                "md5": "dvc_data_hash_9876543210",
                "size": len(data_csv.read_text()),
            }
        ]
    }
    (data_dir / "train.csv.dvc").write_text(yaml.safe_dump(dvc_data))

    # Models directory
    models_dir = tmp_path / "models"
    models_dir.mkdir()

    # DB setup
    db_path = tmp_path / ".vcm" / "vcm.db"
    db = Database(str(db_path))
    db.init()

    return {
        "root": tmp_path,
        "repo": repo,
        "db": db,
        "db_path": str(db_path),
        "data_csv": str(data_csv),
        "models_dir": models_dir,
    }


def test_integration_1_git_metadata(integrated_project):
    """Test 1: Git info is correctly captured in metadata."""
    root = str(integrated_project["root"])
    git_client = GitClient(repo_path=root)
    code_info = git_client.get_safe_code_info()

    assert code_info.git_commit is not None
    assert len(code_info.git_commit) == 40
    assert code_info.git_branch in ("main", "master")
    assert code_info.git_url == "https://github.com/team/integrated-ml.git"

    meta = MetadataModel(
        model_name="model_git_test",
        model_hash="sha256:git_test",
        code=code_info,
        metrics={"accuracy": 0.91},
    )
    assert meta.code.git_commit == code_info.git_commit


def test_integration_2_dvc_metadata(integrated_project):
    """Test 2: DVC file hashes are correctly captured in metadata."""
    root = str(integrated_project["root"])
    dvc_client = DVCClient(repo_path=root)
    data_info = dvc_client.get_data_info()

    assert len(data_info.dvc_files) == 1
    assert data_info.dvc_files[0].dvc_hash == "dvc_data_hash_9876543210"

    meta = MetadataModel(
        model_name="model_dvc_test",
        model_hash="sha256:dvc_test",
        data=data_info,
        metrics={"accuracy": 0.92},
    )
    assert meta.data.dvc_files[0].dvc_hash == "dvc_data_hash_9876543210"


def test_integration_3_database_metadata(integrated_project):
    """Test 3: Metadata is stored and retrieved from database accurately."""
    db = integrated_project["db"]
    meta = MetadataModel(
        model_name="model_db_test",
        model_hash="sha256:db_test_hash",
        metrics={"accuracy": 0.95, "f1_score": 0.94},
        hyperparameters={"lr": 0.001, "epochs": 20},
    )

    row_id = db.insert_model(meta)
    assert row_id > 0

    retrieved = db.get_model_by_hash("sha256:db_test_hash")
    assert retrieved is not None
    assert retrieved.model_name == "model_db_test"
    assert retrieved.metrics["accuracy"] == 0.95
    assert retrieved.hyperparameters["lr"] == 0.001


def test_integration_4_filesystem_and_database(integrated_project):
    """Test 4: .vcm.json files are created on disk and indexed in database."""
    models_dir = integrated_project["models_dir"]
    db = integrated_project["db"]

    model_file = models_dir / "classifier.pkl"
    model_file.write_bytes(b"mock model binary content")
    model_hash = compute_file_hash(str(model_file))

    meta_file = models_dir / "classifier.pkl.vcm.json"
    meta = MetadataModel(
        model_name="classifier",
        model_hash=model_hash,
        model_file="models/classifier.pkl",
        metrics={"accuracy": 0.96},
    )
    meta_file.write_text(meta.to_json())

    # Save into DB
    db.insert_model(meta)

    # Verify disk file
    assert meta_file.exists()
    disk_data = json.loads(meta_file.read_text())
    assert disk_data["model_hash"] == model_hash

    # Verify query from DB
    queried = db.get_model_by_name("classifier")
    assert queried is not None
    assert queried.model_hash == disk_data["model_hash"]


def test_integration_5_all_components_together(integrated_project):
    """Test 5: Git + DVC + DB + Metrics + Environment work together in simulated training."""
    root = str(integrated_project["root"])
    models_dir = integrated_project["models_dir"]
    db = integrated_project["db"]

    # 1. Capture Git
    git_client = GitClient(repo_path=root)
    code_info = git_client.get_safe_code_info()

    # 2. Capture DVC
    dvc_client = DVCClient(repo_path=root)
    data_info = dvc_client.get_data_info("data/train.csv")

    # 3. Capture Environment
    env_info = EnvironmentInfo(
        python_version=EnvironmentCapture.get_python_version(),
        libraries=EnvironmentCapture.get_libraries(["GitPython", "click", "pyyaml"]),
    )

    # 4. Simulate Model Output & Metrics
    model_file = models_dir / "final_model.pkl"
    model_file.write_bytes(b"full integrated trained weights")
    model_hash = compute_file_hash(str(model_file))

    metrics = {"accuracy": 0.975, "f1_score": 0.968, "loss": 0.025}
    hyperparameters = {"lr": 0.0005, "batch_size": 64, "optimizer": "adamw"}

    metadata = MetadataModel(
        model_name="final_model",
        model_hash=model_hash,
        model_file="models/final_model.pkl",
        code=code_info,
        data=data_info,
        training=TrainingInfo(
            timestamp="2024-01-15T12:00:00Z",
            duration_seconds=12.5,
            user="integration_agent",
            hostname="test_host",
        ),
        hyperparameters=hyperparameters,
        metrics=metrics,
        environment=env_info,
    )

    # 5. Write .vcm.json
    vcm_json_path = models_dir / "final_model.pkl.vcm.json"
    vcm_json_path.write_text(metadata.to_json())

    # 6. Store in Database
    db_id = db.insert_model(metadata)
    assert db_id > 0

    # 7. Query and verify completeness
    best = db.get_best_model(metric="accuracy")
    assert best is not None
    assert best.model_name == "final_model"
    assert best.metrics["accuracy"] == 0.975
    assert best.code.git_commit == code_info.git_commit
    assert len(best.data.dvc_files) >= 1
