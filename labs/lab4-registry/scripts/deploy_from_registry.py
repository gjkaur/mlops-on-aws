"""
Deploy latest Approved model package from a group to a realtime endpoint.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
import numpy as np
import sagemaker
from sagemaker.model import ModelPackage

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def get_latest_approved_model(group_name: str) -> str | None:
    sm = _sm()
    resp = sm.list_model_packages(
        ModelPackageGroupName=group_name,
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1,
    )
    rows = resp.get("ModelPackageSummaryList") or []
    if not rows:
        return None
    arn = rows[0]["ModelPackageArn"]
    print(f"Latest approved model package: {arn}")
    return arn


def deploy_model(model_package_arn: str, role_arn: str, endpoint_name: str):
    boto_session = boto3.Session(region_name=REGION)
    sess = sagemaker.Session(boto_session=boto_session)

    print(f"Deploying {model_package_arn} -> {endpoint_name}")
    pkg = ModelPackage(
        role=role_arn,
        model_package_arn=model_package_arn,
        sagemaker_session=sess,
    )
    return pkg.deploy(
        initial_instance_count=1,
        instance_type="ml.t2.medium",
        endpoint_name=endpoint_name,
    )


def test_endpoint(predictor, n_features: int = 10):
    sample = np.random.RandomState(0).rand(1, n_features).astype("float32")
    out = predictor.predict(sample)
    print("Sample prediction:")
    print(f"  input shape: {sample.shape}")
    print(f"  output: {out}")


def main():
    bucket_name = os.environ.get("BUCKET_NAME")
    role_arn = os.environ.get("ROLE_ARN")
    if not bucket_name or not role_arn:
        print("ERROR: Set BUCKET_NAME and ROLE_ARN.")
        raise SystemExit(1)

    group_file = SCRIPT_DIR / "model_package_group.txt"
    if not group_file.exists():
        print("ERROR: Run register_model.py first.")
        raise SystemExit(1)

    group_name = group_file.read_text(encoding="utf-8").strip()

    print("=" * 60)
    print("DEPLOY FROM MODEL REGISTRY")
    print("=" * 60)

    model_arn = get_latest_approved_model(group_name)
    if not model_arn:
        print("No Approved model packages in this group. Run approve_model.py first.")
        raise SystemExit(1)

    endpoint_name = f"lab4-registry-{int(time.time())}"
    endpoint_name = endpoint_name[:63]

    predictor = deploy_model(model_arn, role_arn, endpoint_name)
    test_endpoint(predictor)

    (SCRIPT_DIR / "endpoint_name.txt").write_text(
        predictor.endpoint_name, encoding="utf-8"
    )
    print(f"Endpoint name written to endpoint_name.txt ({predictor.endpoint_name})")


if __name__ == "__main__":
    main()
