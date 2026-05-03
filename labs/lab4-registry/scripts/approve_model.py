"""
Approve / reject registered model packages; list pendings by group.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def describe_pkg(arn: str) -> dict:
    return _sm().describe_model_package(ModelPackageArn=arn)


def update_approval_status(
    model_package_arn: str,
    approval_status: str,
    notes: str = "",
) -> None:
    sm = _sm()
    sm.update_model_package(
        ModelPackageArn=model_package_arn,
        ModelApprovalStatus=approval_status,
        ApprovalDescription=notes[:1024] if notes else "Updated via Lab 4 script",
    )
    print(f"Model approval status set to: {approval_status}")


def list_pending_models(group_name: str) -> list:
    sm = _sm()
    resp = sm.list_model_packages(
        ModelPackageGroupName=group_name,
        ModelApprovalStatus="PendingManualApproval",
    )

    pending = resp.get("ModelPackageSummaryList", [])
    print("Models pending approval:")
    print("-" * 50)
    for pkg in pending:
        print(f"  Version: {pkg.get('ModelPackageVersion', 'n/a')}")
        print(f"  ARN: {pkg['ModelPackageArn']}")
        print(f"  Created: {pkg['CreationTime']}")
        print()
    return pending


def get_model_metrics(model_package_arn: str) -> dict | None:
    resp = describe_pkg(model_package_arn)
    model_metrics = resp.get("ModelMetrics") or {}
    mq = model_metrics.get("ModelQuality") or {}
    stats = mq.get("Statistics") or {}
    raw = stats.get("Value")
    if not raw:
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def main():
    arn_file = SCRIPT_DIR / "model_package_arn.txt"
    group_file = SCRIPT_DIR / "model_package_group.txt"
    if not arn_file.exists() or not group_file.exists():
        print("ERROR: Run register_model.py first.")
        raise SystemExit(1)

    model_arn = arn_file.read_text(encoding="utf-8").strip()
    group_name = group_file.read_text(encoding="utf-8").strip()

    print("=" * 60)
    print("MODEL APPROVAL WORKFLOW")
    print("=" * 60)

    pending = list_pending_models(group_name)
    if not pending:
        print("No packages in PendingManualApproval for this group.")
        raise SystemExit(0)

    print("Reviewing metrics on registered package...")
    metrics = get_model_metrics(model_arn)
    if metrics:
        print("Model metrics:")
        for k, v in metrics.items():
            try:
                print(f"   {k}: {float(v):.4f}")
            except (TypeError, ValueError):
                print(f"   {k}: {v}")
    else:
        print("No embedded metrics found; defaulting decision to Rejected.")
        metrics = {}

    accuracy = float(metrics.get("accuracy", 0.0))
    threshold = float(os.environ.get("ACCURACY_THRESHOLD", "0.85"))

    if accuracy >= threshold:
        decision = "Approved"
        notes = f"Meets accuracy threshold ({accuracy:.4f} >= {threshold})"
        print(f"PASS: accuracy {accuracy:.4f} >= {threshold}")
    else:
        decision = "Rejected"
        notes = f"Below accuracy threshold ({accuracy:.4f} < {threshold})"
        print(f"FAIL: accuracy {accuracy:.4f} < {threshold}")

    update_approval_status(model_arn, decision, notes)
    print(f"Finished: {decision}")


if __name__ == "__main__":
    main()
