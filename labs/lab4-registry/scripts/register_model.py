"""
Create model package group and register a sklearn training artifact.
Reads training_job_name.txt and model_data_uri.txt written by train_model.py.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from sagemaker import image_uris

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def fetch_job_metrics(training_job_name: str) -> dict:
    sm = _sm()
    resp = sm.describe_training_job(TrainingJobName=training_job_name)
    metrics: dict[str, float] = {}
    for m in resp.get("FinalMetricDataList") or []:
        metrics[m["MetricName"]] = float(m["Value"])
    if not metrics:
        # Fallback if CloudWatch metric emission lags
        metrics = {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
        }
    p = metrics.get("precision", 0)
    r = metrics.get("recall", 0)
    if p + r > 0:
        metrics["f1"] = 2 * p * r / (p + r)
    else:
        metrics["f1"] = 0.0
    return metrics


def sklearn_inference_image() -> str:
    return image_uris.retrieve(
        framework="sklearn",
        region=REGION,
        version="1.2-1",
        py_version="py3",
        instance_type="ml.m5.large",
    )


def create_model_package_group(group_name: str) -> str:
    sm = _sm()
    try:
        resp = sm.create_model_package_group(
            ModelPackageGroupName=group_name,
            ModelPackageGroupDescription="Lab 4 — churn-style sklearn classifier registry",
            Tags=[
                {"Key": "project", "Value": "mlops-course"},
                {"Key": "lab", "Value": "module-4"},
            ],
        )
        print(f"Model package group created: {group_name}")
        return resp["ModelPackageGroupArn"]
    except ClientError as err:
        msg = (err.response.get("Error") or {}).get("Message", "").lower()
        if "already exists" in msg:
            print(f"Model package group already exists: {group_name}")
            out = sm.describe_model_package_group(ModelPackageGroupName=group_name)
            return out["ModelPackageGroupArn"]
        raise


def register_model_version(
    group_name: str,
    model_s3_uri: str,
    training_job_name: str,
    metrics: dict,
    inference_image: str,
) -> str:
    sm = _sm()

    model_metrics = {
        "ModelQuality": {
            "Statistics": {
                "ContentType": "application/json",
                "Value": json.dumps(metrics),
            }
        }
    }

    resp = sm.create_model_package(
        ModelPackageGroupName=group_name,
        ModelPackageDescription=f"Sklearn RandomForest from {training_job_name}",
        ModelApprovalStatus="PendingManualApproval",
        InferenceSpecification={
            "Containers": [
                {
                    "Image": inference_image,
                    "ModelDataUrl": model_s3_uri,
                }
            ],
            "SupportedContentTypes": ["text/csv", "application/json"],
            "SupportedResponseMIMETypes": ["text/csv", "application/json"],
        },
        ModelMetrics=model_metrics,
        CustomerMetadataProperties={
            "training_job_name": training_job_name,
            "training_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model_type": "RandomForestClassifier",
            "created_by": "mlops-lab4",
            "n_estimators": "100",
        },
    )

    arn = resp["ModelPackageArn"]
    print(f"Model package version registered: {arn}")
    print("Status: PendingManualApproval")
    return arn


def main():
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")
    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN.")
        raise SystemExit(1)

    job_file = SCRIPT_DIR / "training_job_name.txt"
    model_file = SCRIPT_DIR / "model_data_uri.txt"
    if not job_file.exists() or not model_file.exists():
        print("ERROR: Run train_model.py first (missing training_job_name.txt or model_data_uri.txt).")
        raise SystemExit(1)

    training_job_name = job_file.read_text(encoding="utf-8").strip()
    model_s3_uri = model_file.read_text(encoding="utf-8").strip()

    group_name = os.environ.get(
        "MODEL_PACKAGE_GROUP", f"lab4-churn-group-{int(time.time())}"
    )

    print("=" * 60)
    print("MODEL REGISTRATION")
    print("=" * 60)

    inference_image = sklearn_inference_image()
    print(f"Inference image (sklearn): {inference_image}")

    metrics = fetch_job_metrics(training_job_name)
    print(f"Metrics from training job: {metrics}")

    create_model_package_group(group_name)
    pkg_arn = register_model_version(
        group_name,
        model_s3_uri,
        training_job_name,
        metrics,
        inference_image,
    )

    (SCRIPT_DIR / "model_package_group.txt").write_text(group_name, encoding="utf-8")
    (SCRIPT_DIR / "model_package_arn.txt").write_text(pkg_arn, encoding="utf-8")

    print("Registration finished.")
    print(f"Group: {group_name}")
    print(f"ModelPackageArn: {pkg_arn}")


if __name__ == "__main__":
    main()
