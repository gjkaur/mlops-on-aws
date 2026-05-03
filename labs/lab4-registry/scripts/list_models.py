"""
List SageMaker Model Registry groups and package versions (Lab 4).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def list_model_groups() -> list:
    sm = _sm()
    resp = sm.list_model_package_groups()
    groups = resp.get("ModelPackageGroupSummaryList", [])
    print("MODEL PACKAGE GROUPS:")
    print("-" * 50)
    for g in groups:
        print(f"  {g['ModelPackageGroupName']}")
        print(f"    Status: {g.get('ModelPackageGroupStatus')}")
        print(f"    Created: {g.get('CreationTime')}")
        print()
    return groups


def list_models_in_group(group_name: str) -> None:
    sm = _sm()
    resp = sm.list_model_packages(ModelPackageGroupName=group_name)

    print(f"MODEL PACKAGES IN GROUP: {group_name}")
    print("-" * 60)
    for pkg in resp.get("ModelPackageSummaryList", []):
        print(f"  Version: {pkg.get('ModelPackageVersion', 'n/a')}")
        print(f"    Approval: {pkg.get('ModelApprovalStatus')}")
        print(f"    Created: {pkg.get('CreationTime')}")
        print(f"    ARN: {pkg['ModelPackageArn']}")
        print()


def get_model_details(model_package_arn: str) -> None:
    sm = _sm()
    resp = sm.describe_model_package(ModelPackageArn=model_package_arn)

    print("MODEL PACKAGE DETAIL")
    print("-" * 50)
    print(f"  ARN: {resp.get('ModelPackageArn')}")
    print(f"  Group: {resp.get('ModelPackageGroupName')}")
    print(f"  Version: {resp.get('ModelPackageVersion')}")
    print(f"  Approval: {resp.get('ModelApprovalStatus')}")
    print(f"  Created: {resp.get('CreationTime')}")

    model_metrics = resp.get("ModelMetrics") or {}
    mq = model_metrics.get("ModelQuality") or {}
    stats = mq.get("Statistics") or {}
    raw = stats.get("Value")
    if raw:
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        m = json.loads(raw)
        print("  Metrics:")
        for name, val in m.items():
            print(f"    {name}: {val}")

    meta = resp.get("CustomerMetadataProperties") or {}
    if meta:
        print("  Metadata:")
        for k, v in meta.items():
            print(f"    {k}: {v}")


def main():
    print("=" * 60)
    print("MODEL REGISTRY LISTING")
    print("=" * 60)

    groups = list_model_groups()
    if not groups:
        print("No model package groups in this account/region.")
        sys.exit(0)

    preferred = SCRIPT_DIR / "model_package_group.txt"
    group_name = None
    if preferred.exists():
        group_name = preferred.read_text(encoding="utf-8").strip()
        print(f"Using group from model_package_group.txt: {group_name}\n")

    if not group_name or not any(
        g["ModelPackageGroupName"] == group_name for g in groups
    ):
        group_name = groups[0]["ModelPackageGroupName"]
        print(f"(Falling back to first group shown: {group_name})\n")

    list_models_in_group(group_name)

    sm = _sm()
    resp = sm.list_model_packages(ModelPackageGroupName=group_name, MaxResults=20)
    rows = sorted(
        resp.get("ModelPackageSummaryList", []),
        key=lambda x: x["CreationTime"],
        reverse=True,
    )
    if rows:
        get_model_details(rows[0]["ModelPackageArn"])
    else:
        print("(No packages in group yet)")


if __name__ == "__main__":
    main()
