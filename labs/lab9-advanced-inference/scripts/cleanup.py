"""
Delete SageMaker endpoints created during Lab 9 (models + configs when discoverable).

S3 buckets and IAM are torn down separately with terraform destroy.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"


def _delete_bundle(endpoint_name: str, sm):
    """Delete endpoint → endpoint config → model names referenced by config."""
    try:
        cfg_name = sm.describe_endpoint(EndpointName=endpoint_name)[
            "EndpointConfigName"
        ]
        sm.delete_endpoint(EndpointName=endpoint_name)

        waiter = sm.get_waiter("endpoint_deleted")
        try:
            waiter.wait(EndpointName=endpoint_name, WaiterConfig={"Delay": 5, "MaxAttempts": 40})
        except Exception:
            time.sleep(10)

        desc = sm.describe_endpoint_config(EndpointConfigName=cfg_name)
        sm.delete_endpoint_config(EndpointConfigName=cfg_name)

        for pv in desc.get("ProductionVariants", []):
            mn = pv.get("ModelName")
            if mn:
                try:
                    sm.delete_model(ModelName=mn)
                    print(f"✓ Deleted model {mn}")
                except Exception as err:
                    print(f"⚠ Model {mn}: {err}")
        print(f"✓ Deleted endpoint + config ({endpoint_name})")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code == "ValidationException":
            print(f"(Endpoint not found): {endpoint_name}")
        else:
            print(f"⚠ Endpoint {endpoint_name}: {e}")


def main():
    print("=" * 60)
    print("LAB 9 SAGEMAKER CLEANUP")
    print("=" * 60)
    sm = boto3.client("sagemaker", region_name=REGION)

    for fname in (
        "serverless_endpoint_name.txt",
        "async_endpoint_name.txt",
        "mme_endpoint_name.txt",
    ):
        path = SCRIPT_DIR / fname
        if path.is_file():
            name = path.read_text(encoding="utf-8").strip()
            if name:
                _delete_bundle(name, sm)

    print("\nNext: terraform destroy in infrastructure/")

if __name__ == "__main__":
    main()
