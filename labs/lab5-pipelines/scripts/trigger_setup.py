"""Create EventBridge rule to start the Lab 5 pipeline when objects land under new-data/."""

from __future__ import annotations

import json
import os
import sys

import boto3

from pipeline_definition import pipeline_name_for_bucket

REGION = "us-east-1"


def default_rule_and_pipeline_names(bucket_name: str) -> tuple[str, str]:
    suf = bucket_name[-8:] if len(bucket_name) >= 8 else bucket_name.replace("-", "")[:8]
    rule = f"lab5-trigger-pipeline-{suf}"
    pipeline = pipeline_name_for_bucket(bucket_name)
    return rule, pipeline


def create_trigger(rule_name: str, bucket_name: str, pipeline_name: str, eventbridge_role_arn: str):
    events = boto3.client("events", region_name=REGION)
    sm = boto3.client("sagemaker", region_name=REGION)

    pattern = {
        "source": ["aws.s3"],
        "detail-type": ["Object Created"],
        "detail": {
            "bucket": {"name": [bucket_name]},
            "object": {"key": [{"prefix": "new-data/"}]},
        },
    }

    events.put_rule(
        Name=rule_name,
        EventPattern=json.dumps(pattern),
        State="ENABLED",
        Description="Lab 5: start SageMaker pipeline when data appears under new-data/",
    )

    pipeline_arn = sm.describe_pipeline(PipelineName=pipeline_name)["PipelineArn"]

    pipeline_params = {
        "ProcessingInstanceType": "ml.m5.large",
        "TrainingInstanceType": "ml.m5.large",
        "NEstimators": "150",
        "MaxDepth": "12",
        "AccuracyThreshold": "0.75",
    }

    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": "SageMakerPipelineTarget",
                "Arn": pipeline_arn,
                "RoleArn": eventbridge_role_arn,
                "SageMakerPipelineParameters": {
                    "PipelineParameterList": [
                        {"Name": k, "Value": str(v)}
                        for k, v in pipeline_params.items()
                    ]
                },
            }
        ],
    )


def delete_trigger(rule_name: str):
    events = boto3.client("events", region_name=REGION)
    events.remove_targets(Rule=rule_name, Ids=["SageMakerPipelineTarget"], Force=True)
    events.delete_rule(Name=rule_name)


def main(argv: list[str]) -> None:
    bucket = os.environ.get("BUCKET_NAME")
    if not bucket:
        print("ERROR: Set BUCKET_NAME.")
        raise SystemExit(1)

    role_arn = os.environ.get("EVENTBRIDGE_ROLE_ARN")
    rule_name, pipeline_name = default_rule_and_pipeline_names(bucket)

    if len(argv) > 1 and argv[1] == "delete":
        delete_trigger(rule_name)
        print(f"Removed rule + target: {rule_name}")
        return

    if not role_arn:
        print("ERROR: Set EVENTBRIDGE_ROLE_ARN (terraform output eventbridge_role_arn).")
        raise SystemExit(1)

    create_trigger(rule_name, bucket, pipeline_name, role_arn)
    print(f"Rule: {rule_name}")
    print(f"Target pipeline: {pipeline_name}")
    print(f"Matches uploads to s3://{bucket}/new-data/")
    print("Ensure S3 event delivery to EventBridge is enabled on the bucket (Terraform does this).")


if __name__ == "__main__":
    main(sys.argv)
