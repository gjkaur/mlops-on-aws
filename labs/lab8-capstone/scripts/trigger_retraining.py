"""Wire DATA_BUCKET uploads under new-data/ to SageMaker Pipeline StartPipelineExecution."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def rule_name(bucket: str) -> str:
    suf = bucket[-12:] if len(bucket) >= 12 else "".join(c for c in bucket if c.isalnum())[:12]
    return f"lab8-trigger-{suf}"[:63]


def delete_trigger_explicit(rule_name_: str) -> None:
    events = boto3.client("events", region_name=REGION)
    events.remove_targets(Rule=rule_name_, Ids=["SageMakerPipelineTarget"], Force=True)
    events.delete_rule(Name=rule_name_)
    print(f"Deleted rule: {rule_name_}")


def create_trigger(bucket_name: str, pipeline_name: str, eb_role_arn: str, rname: str) -> None:
    events = boto3.client("events", region_name=REGION)
    sm = boto3.client("sagemaker", region_name=REGION)

    pattern = json.dumps(
        {
            "source": ["aws.s3"],
            "detail-type": ["Object Created"],
            "detail": {
                "bucket": {"name": [bucket_name]},
                "object": {"key": [{"prefix": "new-data/"}]},
            },
        }
    )

    events.put_rule(
        Name=rname,
        EventPattern=pattern,
        State="ENABLED",
        Description="Lab 8 — start churn pipeline after new batches land under new-data/",
    )

    pipe_arn = sm.describe_pipeline(PipelineName=pipeline_name)["PipelineArn"]
    pipe_params = {
        "ProcessingInstanceType": os.environ.get("CAPSTONE_PROCESSING", "ml.m5.large"),
        "TrainingInstanceType": os.environ.get("CAPSTONE_TRAINING", "ml.m5.large"),
        "NEstimators": os.environ.get("CAPSTONE_N_EST", "150"),
        "MaxDepth": os.environ.get("CAPSTONE_MAX_DEPTH", "12"),
        "AccuracyThreshold": os.environ.get("CAPSTONE_ACC_GATE", "0.75"),
    }

    events.put_targets(
        Rule=rname,
        Targets=[
            {
                "Id": "SageMakerPipelineTarget",
                "Arn": pipe_arn,
                "RoleArn": eb_role_arn,
                "SageMakerPipelineParameters": {
                    "PipelineParameterList": [
                        {"Name": k, "Value": str(v)}
                        for k, v in pipe_params.items()
                    ]
                },
            }
        ],
    )


def main():
    pfn = SCRIPT_DIR / "pipeline_name.txt"
    if not pfn.is_file():
        print("ERROR: Missing pipeline_name.txt (run pipeline_definition.py).")
        raise SystemExit(1)
    pipeline_name = pfn.read_text(encoding="utf-8").strip()
    bucket = os.environ.get("DATA_BUCKET_NAME", "").strip()

    if len(sys.argv) > 1 and sys.argv[1] == "delete":
        rf = SCRIPT_DIR / "eventbridge_rule_name.txt"
        if rf.is_file():
            delete_trigger_explicit(rf.read_text(encoding="utf-8").strip())
        elif bucket:
            delete_trigger_explicit(rule_name(bucket))
        return

    role_arn = os.environ.get("EVENTBRIDGE_ROLE_ARN", "").strip()
    if not bucket or not role_arn:
        print("ERROR: DATA_BUCKET_NAME and EVENTBRIDGE_ROLE_ARN.")
        raise SystemExit(1)

    rname = rule_name(bucket)
    create_trigger(bucket, pipeline_name, role_arn, rname)
    SCRIPT_DIR.joinpath("eventbridge_rule_name.txt").write_text(rname, encoding="utf-8")
    print(f"Rule: {rname}")
    print(f"Triggers pipeline {pipeline_name} on s3://{bucket}/new-data/*")


if __name__ == "__main__":
    main()
