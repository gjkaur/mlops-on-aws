"""Start a SageMaker Pipeline execution (Lab 5) and poll until a terminal status."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import boto3

from pipeline_definition import pipeline_name_for_bucket

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"

DEFAULT_PARAMETERS = {
    "ProcessingInstanceType": "ml.m5.large",
    "TrainingInstanceType": "ml.m5.large",
    "NEstimators": "150",
    "MaxDepth": "12",
    "AccuracyThreshold": "0.75",
}


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def run_pipeline(pipeline_name: str, parameters: dict[str, str]) -> str:
    sm = _sm()
    response = sm.start_pipeline_execution(
        PipelineName=pipeline_name,
        PipelineExecutionDisplayName=f"execution-{int(time.time())}",
        PipelineParameters=[{"Name": k, "Value": str(v)} for k, v in parameters.items()],
    )
    return response["PipelineExecutionArn"]


def wait_for_completion(execution_arn: str, poll_seconds: int = 30) -> str:
    sm = _sm()
    while True:
        resp = sm.describe_pipeline_execution(PipelineExecutionArn=execution_arn)
        status = resp["PipelineExecutionStatus"]
        print(f"  Pipeline status: {status}")
        if status in {"Succeeded", "Failed", "Stopped"}:
            return status
        time.sleep(poll_seconds)


def main():
    bucket = os.environ.get("BUCKET_NAME")
    if not bucket:
        print("ERROR: Set BUCKET_NAME environment variable.")
        raise SystemExit(1)

    name_file = SCRIPT_DIR / "pipeline_name.txt"
    if name_file.is_file():
        pipeline_name = name_file.read_text(encoding="utf-8").strip()
    else:
        pipeline_name = pipeline_name_for_bucket(bucket)

    params = dict(DEFAULT_PARAMETERS)

    print("=" * 60)
    print("RUNNING SAGEMAKER PIPELINE")
    print("=" * 60)
    print(f"Pipeline: {pipeline_name}")
    print(f"Parameters: {json.dumps(params, indent=2)}")

    arn = run_pipeline(pipeline_name, params)
    print(f"Started: {arn}")
    print("Waiting for completion (this may take 10–18 minutes)...")

    final = wait_for_completion(arn)

    details = _sm().describe_pipeline_execution(PipelineExecutionArn=arn)

    print(f"\nFinal status: {final}")
    if final != "Succeeded":
        print(f"Failure reason (if present): {details.get('PipelineExecutionFailureReason', '(none)')}")

    (SCRIPT_DIR / "pipeline_execution_arn.txt").write_text(arn, encoding="utf-8")


if __name__ == "__main__":
    main()
