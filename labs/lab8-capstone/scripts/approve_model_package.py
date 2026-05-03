"""
Approve (or optionally reject) the newest PendingManualApproval model package for the Lab 8 group.

Reads model_package_group.txt from pipeline_definition.py. Writes approved_model_package_arn.txt.
"""

from __future__ import annotations

import os
from pathlib import Path

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def main():
    gf = SCRIPT_DIR / "model_package_group.txt"
    if not gf.is_file():
        print("ERROR: Run pipeline_definition.py first.")
        raise SystemExit(1)
    group = gf.read_text(encoding="utf-8").strip()

    sm = boto3.client("sagemaker", region_name=REGION)
    resp = sm.list_model_packages(
        ModelPackageGroupName=group,
        ModelApprovalStatus="PendingManualApproval",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=5,
    )
    rows = resp.get("ModelPackageSummaryList") or []
    if not rows:
        print("No PendingManualApproval packages. Did the ConditionStep gate pass? Check pipeline graph.")
        raise SystemExit(1)

    pkg = rows[0]
    arn = pkg["ModelPackageArn"]
    print(f"Latest pending package: {arn}")

    notes = os.environ.get("CAPSTONE_APPROVAL_NOTES", "Lab 8 capstone manual approval.")
    decision = os.environ.get("CAPSTONE_APPROVAL", "Approved")
    sm.update_model_package(
        ModelPackageArn=arn,
        ModelApprovalStatus=decision,
        ApprovalDescription=notes[:1024],
    )
    print(f"ModelApprovalStatus → {decision}")

    if decision == "Approved":
        (SCRIPT_DIR / "approved_model_package_arn.txt").write_text(arn, encoding="utf-8")


if __name__ == "__main__":
    main()
