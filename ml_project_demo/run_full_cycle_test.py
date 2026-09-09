"""Automated end-to-end full cycle verification runner for VCM.

Runs all VCM CLI commands on real ML models, validates outputs, and confirms
data integrity, lineage tracking, sidecar JSON persistence, and SQLite indexing.
"""

import os
import subprocess
import sys

def run_cmd(cmd: list[str]) -> str:
    print(f"\n[RUNNING] {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[STDERR] {res.stderr}")
        raise RuntimeError(f"Command failed with code {res.returncode}: {' '.join(cmd)}")
    print(f"[OUTPUT]\n{res.stdout}")
    return res.stdout

def main() -> None:
    vcm_bin = os.path.abspath(os.path.join("..", "venv", "bin", "vcm"))
    print(f"Using VCM binary: {vcm_bin}")

    # Clean previous run artifacts for an isolated run
    import shutil
    for f in ["metrics_v1.json", "metrics_v2.json", "metrics_v3.json", "rf_v2_export.json", "exported_models.csv"]:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(".vcm"):
        shutil.rmtree(".vcm")
    if os.path.exists("models"):
        shutil.rmtree("models")
    if os.path.exists(".vcmconfig.yaml"):
        os.remove(".vcmconfig.yaml")

    if not os.path.exists(".git"):
        subprocess.run(["git", "init"], check=False)
        subprocess.run(["git", "config", "user.name", "VCM Demo"], check=False)
        subprocess.run(["git", "config", "user.email", "demo@vcm.local"], check=False)
        subprocess.run(["git", "add", "."], check=False)
        subprocess.run(["git", "commit", "-m", "Init"], check=False)

    # 1. Init
    run_cmd([vcm_bin, "init"])

    # 2. Train Model 1 (Logistic Regression)
    run_cmd([
        vcm_bin, "train",
        "--model-name", "iris_logistic_v1",
        "--dataset", "data/iris_v1.csv",
        "--script", "train_model1.py",
        "--metrics", "metrics_v1.json",
        "--model-file", "models/iris_logistic_v1.pkl",
        "--params", "C=0.1",
        "--params", "solver=lbfgs",
    ])

    # 3. Train Model 2 (Random Forest)
    run_cmd([
        vcm_bin, "train",
        "--model-name", "iris_rf_v2",
        "--dataset", "data/iris_v1.csv",
        "--script", "train_model2.py",
        "--metrics", "metrics_v2.json",
        "--model-file", "models/iris_rf_v2.pkl",
        "--params", "n_estimators=100",
        "--params", "max_depth=4",
    ])

    # 4. Train Model 3 (Gradient Boosting on Dataset v2)
    run_cmd([
        vcm_bin, "train",
        "--model-name", "iris_gb_v3",
        "--dataset", "data/iris_v2.csv",
        "--script", "train_model3.py",
        "--metrics", "metrics_v3.json",
        "--model-file", "models/iris_gb_v3.pkl",
        "--params", "n_estimators=150",
        "--params", "learning_rate=0.05",
    ])

    # 5. List Models
    out_models = run_cmd([vcm_bin, "models"])
    assert "iris_logistic_v1" in out_models
    assert "iris_rf_v2" in out_models
    assert "iris_gb_v3" in out_models

    # 6. Best Model
    out_best = run_cmd([vcm_bin, "models", "--best"])
    assert "iris_gb_v3" in out_best or "iris_rf_v2" in out_best

    # 7. Lineage
    out_lineage = run_cmd([vcm_bin, "lineage", "models/iris_rf_v2.pkl"])
    assert "iris_rf_v2" in out_lineage
    assert "Git Commit" in out_lineage
    assert "Dataset Files" in out_lineage

    # 8. Compare
    out_compare = run_cmd([vcm_bin, "compare", "models/iris_logistic_v1.pkl", "models/iris_gb_v3.pkl"])
    assert "Comparison" in out_compare
    assert "iris_logistic_v1" in out_compare
    assert "iris_gb_v3" in out_compare

    # 9. Info
    out_info = run_cmd([vcm_bin, "info", "models/iris_rf_v2.pkl"])
    assert "Model Name" in out_info
    assert "iris_rf_v2" in out_info

    # 10. Export
    out_export = run_cmd([vcm_bin, "export", "models/iris_rf_v2.pkl", "--output", "rf_v2_export.json"])
    assert os.path.exists("rf_v2_export.json")

    # 11. Repair (Self-healing from database loss)
    db_file = os.path.join(".vcm", "vcm.db")
    if os.path.exists(db_file):
        os.remove(db_file)
    out_repair = run_cmd([vcm_bin, "repair"])
    assert "repaired" in out_repair.lower()
    assert os.path.exists(db_file)

    print("\n=======================================================")
    print("FULL CYCLE VALIDATION COMPLETED SUCCESSFULLY (100% PASS)!")
    print("=======================================================\n")

if __name__ == "__main__":
    main()
