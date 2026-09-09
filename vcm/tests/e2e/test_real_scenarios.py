import os
import git
from click.testing import CliRunner
from vcm.cli.main import cli
from vcm.db.database import Database
from vcm.trainer import ModelTracker


def test_e2e_1_real_project_scenario(tmp_path):
    """E2E-1: Complete ML workflow with VCM."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # 1. Initialize empty project & git
        repo = git.Repo.init(".")
        with open("README.md", "w") as f:
            f.write("# Real ML Project\n")
        repo.index.add(["README.md"])
        repo.index.commit("Initial project commit")

        # 2. VCM Init
        res_init = runner.invoke(cli, ["init"])
        assert res_init.exit_code == 0

        # 3. Create mock data & training script
        os.makedirs("data", exist_ok=True)
        os.makedirs("models", exist_ok=True)

        with open("data/train_v1.csv", "w") as f:
            f.write("text,label\ngood,1\nbad,0\n")
        with open("data/train_v2.csv", "w") as f:
            f.write("text,label\ngreat,1\nterrible,0\n")

        with open("train.py", "w") as f:
            f.write("""
import os, json

for name, acc, f1 in [("model_v1", 0.91, 0.90), ("model_v2", 0.94, 0.93), ("model_v3", 0.96, 0.95)]:
    os.makedirs("models", exist_ok=True)
    with open(f"models/{name}.pkl", "wb") as f_out:
        f_out.write(f"weights for {name}".encode())
    with open(f"metrics_{name}.json", "w") as f_m:
        json.dump({"accuracy": acc, "f1_score": f1}, f_m)
""")

        # 4. Train model v1 with dataset 1
        res_t1 = runner.invoke(cli, [
            "train",
            "--model-name", "model_v1",
            "--dataset", "data/train_v1.csv",
            "--script", "train.py",
            "--metrics", "metrics_model_v1.json",
            "--model-file", "models/model_v1.pkl",
            "--params", "lr=0.01",
            "--params", "epochs=20",
        ])
        assert res_t1.exit_code == 0

        # 5. Train model v2 with improved hyperparams
        res_t2 = runner.invoke(cli, [
            "train",
            "--model-name", "model_v2",
            "--dataset", "data/train_v1.csv",
            "--script", "train.py",
            "--metrics", "metrics_model_v2.json",
            "--model-file", "models/model_v2.pkl",
            "--params", "lr=0.001",
            "--params", "epochs=50",
        ])
        assert res_t2.exit_code == 0

        # 6. Train model v3 with new dataset
        res_t3 = runner.invoke(cli, [
            "train",
            "--model-name", "model_v3",
            "--dataset", "data/train_v2.csv",
            "--script", "train.py",
            "--metrics", "metrics_model_v3.json",
            "--model-file", "models/model_v3.pkl",
            "--params", "lr=0.0005",
            "--params", "epochs=100",
        ])
        assert res_t3.exit_code == 0

        # 7. Compare models
        res_cmp = runner.invoke(cli, ["compare", "models/model_v1.pkl", "models/model_v2.pkl"])
        assert res_cmp.exit_code == 0
        assert "model_v1" in res_cmp.output
        assert "model_v2" in res_cmp.output

        # 8. Query for best model
        res_best = runner.invoke(cli, ["models", "--best"])
        assert res_best.exit_code == 0

        # 9. Export results
        res_exp = runner.invoke(cli, ["export", "models/model_v2.pkl", "--output", "exported.json"])
        assert res_exp.exit_code == 0
        assert os.path.exists("exported.json")


def test_e2e_2_reproduce_exact_scenario(tmp_path):
    """E2E-2: Recover all metadata after database deletion."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(cli, ["init"])
        os.makedirs("models", exist_ok=True)

        with open("models/model_saved.pkl", "wb") as f:
            f.write(b"saved weights")

        with open("train.py", "w") as f:
            f.write("pass\n")

        with open("metrics.json", "w") as f:
            import json
            json.dump({"accuracy": 0.98}, f)

        runner.invoke(cli, [
            "train",
            "--model-name", "model_saved",
            "--script", "train.py",
            "--metrics", "metrics.json",
            "--model-file", "models/model_saved.pkl",
        ])

        assert os.path.exists("models/model_saved.pkl.vcm.json")

        # Delete database
        os.remove(".vcm/vcm.db")
        assert not os.path.exists(".vcm/vcm.db")

        # Restore
        res_repair = runner.invoke(cli, ["repair"])
        assert res_repair.exit_code == 0
        assert os.path.exists(".vcm/vcm.db")

        # Query
        res_query = runner.invoke(cli, ["models"])
        assert res_query.exit_code == 0
        assert "model_saved" in res_query.output


def test_e2e_3_multiple_users_scenario(tmp_path):
    """E2E-3: Track models from different users."""
    db_path = str(tmp_path / ".vcm" / "vcm.db")
    db = Database(db_path)
    db.init()
    os.makedirs(tmp_path / "models", exist_ok=True)

    m1_file = tmp_path / "models" / "alice_model.pkl"
    m1_file.write_bytes(b"alice weights")

    m2_file = tmp_path / "models" / "bob_model.pkl"
    m2_file.write_bytes(b"bob weights")

    tracker = ModelTracker(db_path=db_path, repo_path=str(tmp_path))
    meta_alice = tracker.log_model(
        model_path=str(m1_file),
        model_name="alice_model",
        metrics={"accuracy": 0.91},
    )

    meta_bob = tracker.log_model(
        model_path=str(m2_file),
        model_name="bob_model",
        metrics={"accuracy": 0.94},
    )

    assert meta_alice.model_name == "alice_model"
    assert meta_bob.model_name == "bob_model"

    all_models = db.get_all_models()
    assert len(all_models) == 2
    names = {m.model_name for m in all_models}
    assert names == {"alice_model", "bob_model"}
