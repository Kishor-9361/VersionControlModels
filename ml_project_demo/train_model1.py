"""Real ML Training Script 1: Logistic Regression on Iris v1 Dataset."""

import json
import os
import pickle
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

os.makedirs("models", exist_ok=True)

# 1. Load dataset
data_path = os.environ.get("DATASET_PATH", "data/iris_v1.csv")
df = pd.read_csv(data_path)
X = df.drop(columns=["target"])
y = df["target"]

# 2. Split train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 3. Fit real model
clf = LogisticRegression(C=0.1, solver="lbfgs", max_iter=200, random_state=42)
clf.fit(X_train, y_train)

# 4. Evaluate
y_pred = clf.predict(X_test)
acc = float(accuracy_score(y_test, y_pred))
prec = float(precision_score(y_test, y_pred, zero_division=0))
rec = float(recall_score(y_test, y_pred, zero_division=0))
f1 = float(f1_score(y_test, y_pred, zero_division=0))

metrics = {
    "accuracy": acc,
    "precision": prec,
    "recall": rec,
    "f1_score": f1,
}

# 5. Save model artifact and metrics
model_output_path = "models/iris_logistic_v1.pkl"
with open(model_output_path, "wb") as f:
    pickle.dump(clf, f)

metrics_output_path = "metrics_v1.json"
with open(metrics_output_path, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

print(f"✅ LogisticRegression trained: Acc={acc:.4f}, F1={f1:.4f}")
