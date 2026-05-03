"""
Train sklearn RandomForest variants and upload model.tar.gz to S3 (Lab 9).

Each tarball contains model.joblib at the root — required by SageMaker sklearn.
"""

from __future__ import annotations

import os
import tempfile
import tarfile
from pathlib import Path

import boto3
import joblib
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

SCRIPT_DIR = Path(__file__).resolve().parent


def train_model(n_estimators: int, model_name: str, bucket_name: str) -> str:
    """Train a model and upload tarball to s3://bucket/models/{model_name}/model.tar.gz."""

    print(f"Training {model_name} (n_estimators={n_estimators})...")

    X, y = make_classification(
        n_samples=2000,
        n_features=10,
        n_informative=8,
        n_redundant=2,
        random_state=42,
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    print(f"   Accuracy: {accuracy:.4f}")

    with tempfile.TemporaryDirectory(dir=str(SCRIPT_DIR)) as td:
        tdir = Path(td)
        model_path = tdir / "model.joblib"
        joblib.dump(model, model_path)
        tarball = SCRIPT_DIR / f"{model_name}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tar:
            tar.add(model_path, arcname="model.joblib")

        s3 = boto3.client("s3")
        s3_key = f"models/{model_name}/model.tar.gz"
        s3.upload_file(str(tarball), bucket_name, s3_key)
        tarball.unlink(missing_ok=True)

    uri = f"s3://{bucket_name}/models/{model_name}/model.tar.gz"
    print(f"   Uploaded {uri}")
    return uri


def main():
    bucket = os.environ.get("BUCKET_NAME", "").strip()
    if not bucket:
        raise SystemExit("ERROR: export BUCKET_NAME from Terraform.")

    print("=" * 60)
    print("TRAINING MODELS FOR ADVANCED INFERENCE")
    print("=" * 60)

    models = {
        "model-v1": 50,
        "model-v2": 100,
        "model-v3": 150,
    }

    entries = []
    for name, n_est in models.items():
        uri = train_model(n_est, name, bucket)
        entries.append((name, uri))

    txt = SCRIPT_DIR / "model_uris.txt"
    with txt.open("w", encoding="utf-8") as f:
        for name, uri in entries:
            f.write(f"{name}={uri}\n")

    print("\n✅ All models trained and uploaded!")
    print(f"   State file: {txt}")


if __name__ == "__main__":
    main()
