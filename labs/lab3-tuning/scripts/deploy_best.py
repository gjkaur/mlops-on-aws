"""
Deploy the best training job artifact from an HPO run to a realtime endpoint.
"""

import os
import time
from pathlib import Path

import boto3
import numpy as np
import sagemaker
from sagemaker.sklearn import SKLearnModel

from sklearn.datasets import load_diabetes

SCRIPT_DIR = Path(__file__).resolve().parent


def get_best_model_artifact(tuning_job_name):
    sm = boto3.client("sagemaker", region_name="us-east-1")
    resp = sm.describe_hyper_parameter_tuning_job(
        HyperParameterTuningJobName=tuning_job_name
    )

    best_job = resp.get("BestTrainingJob") or {}
    best_job_name = best_job.get("TrainingJobName")

    if not best_job_name:
        print("No best training job recorded yet.")
        return None, None

    detail = sm.describe_training_job(TrainingJobName=best_job_name)
    artifact = detail["ModelArtifacts"]["S3ModelArtifacts"]

    print(f"Best training job: {best_job_name}")
    print(f"Model artifact: {artifact}")

    return artifact, best_job_name


def deploy_best_model(model_artifact, role_arn):
    boto_session = boto3.Session(region_name="us-east-1")
    session = sagemaker.Session(boto_session=boto_session)

    suffix = int(time.time())
    endpoint_name = f"tuning-best-{suffix}"
    endpoint_name = endpoint_name[:63]

    print("\nDeploying best model...")
    model = SKLearnModel(
        model_data=model_artifact,
        role=role_arn,
        entry_point="predict.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )

    predictor = model.deploy(
        initial_instance_count=1,
        instance_type="ml.t2.medium",
        endpoint_name=endpoint_name,
    )

    print(f"Model deployed to endpoint: {predictor.endpoint_name}")
    return predictor


def test_endpoint(predictor):
    X, _ = load_diabetes(return_X_y=True)
    sample = X[0].reshape(1, -1)

    preds = predictor.predict(sample)
    print("\nSample prediction (first diabetes row from sklearn):")
    print(f"   Features shape: {sample.shape}")
    print(f"   Prediction: {preds}")


if __name__ == "__main__":
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")

    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN environment variables")
        raise SystemExit(1)

    if not os.path.exists(SCRIPT_DIR / "tuning_job_name.txt"):
        print("No tuning job found. Run tuning_config.py first.")
        raise SystemExit(1)

    with open(SCRIPT_DIR / "tuning_job_name.txt", encoding="utf-8") as f:
        tuning_job_name = f.read().strip()

    print("=" * 60)
    print("DEPLOYING BEST MODEL FROM TUNING")
    print("=" * 60)

    artifact, _ = get_best_model_artifact(tuning_job_name)
    if not artifact:
        raise SystemExit(1)

    predictor = deploy_best_model(artifact, role_arn)
    test_endpoint(predictor)

    with open(SCRIPT_DIR / "endpoint_name.txt", "w", encoding="utf-8") as f:
        f.write(predictor.endpoint_name)

    print("\nEndpoint name saved to endpoint_name.txt")
