"""Start SageMaker Pipeline execution for Lab 8 and capture preprocess train.csv S3 URI."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _sm():
    return boto3.client("sagemaker", region_name=REGION)


def _discover_preprocess_train_csv(execution_arn: str) -> str:
    """Return s3 URI to train.csv produced by PreprocessData step."""
    sm = _sm()
    token = None
    while True:
        kwargs = {"PipelineExecutionArn": execution_arn}
        if token:
            kwargs["NextToken"] = token
        resp = sm.list_pipeline_execution_steps(**kwargs)
        for st in resp.get("PipelineExecutionSteps", []):
            if st.get("StepName") != "PreprocessData":
                continue
            meta = (st.get("Metadata") or {}).get("ProcessingJob") or {}
            pj_arn = meta.get("Arn")
            if not pj_arn:
                continue
            job_name = pj_arn.split("/")[-1]
            desc = sm.describe_processing_job(ProcessingJobName=job_name)
            for outp in desc.get("ProcessingOutputConfig", {}).get("Outputs", []) or []:
                if outp.get("OutputName") == "train_data":
                    base = outp["S3Output"]["S3Uri"].rstrip("/")
                    return f"{base}/train.csv"
        token = resp.get("NextToken")
        if not token:
            break
    return ""


def run_execution(pipeline_name: str, params: dict) -> str:
    sm = _sm()
    resp = sm.start_pipeline_execution(
        PipelineName=pipeline_name,
        PipelineExecutionDisplayName=f"lab8-exec-{int(time.time())}",
        PipelineParameters=[{"Name": k, "Value": str(v)} for k, v in params.items()],
    )
    return resp["PipelineExecutionArn"]


def wait_terminal(execution_arn: str, poll_seconds: int = 30) -> str:
    sm = _sm()
    while True:
        resp = sm.describe_pipeline_execution(PipelineExecutionArn=execution_arn)
        status = resp["PipelineExecutionStatus"]
        print(f"PipelineExecutionStatus={status}")
        if status in ("Succeeded", "Failed", "Stopped"):
            return status
        time.sleep(poll_seconds)


def main():
    pfn = SCRIPT_DIR / "pipeline_name.txt"
    if not pfn.is_file():
        print("ERROR: Run pipeline_definition.py first.")
        raise SystemExit(1)
    pipeline_name = pfn.read_text(encoding="utf-8").strip()

    params = {
        "ProcessingInstanceType": os.environ.get("CAPSTONE_PROCESSING", "ml.m5.large"),
        "TrainingInstanceType": os.environ.get("CAPSTONE_TRAINING", "ml.m5.large"),
        "NEstimators": os.environ.get("CAPSTONE_N_EST", "150"),
        "MaxDepth": os.environ.get("CAPSTONE_MAX_DEPTH", "12"),
        "AccuracyThreshold": os.environ.get("CAPSTONE_ACC_GATE", "0.75"),
    }

    print("=" * 60)
    print("CAPSTONE PIPELINE EXECUTION")
    print(f"{pipeline_name=}")
    print(json.dumps(params, indent=2))

    exec_arn = run_execution(pipeline_name, params)
    (SCRIPT_DIR / "pipeline_execution_arn.txt").write_text(exec_arn, encoding="utf-8")
    print(f"Started: {exec_arn}")

    terminal = wait_terminal(exec_arn)
    (SCRIPT_DIR / "pipeline_terminal_status.txt").write_text(terminal, encoding="utf-8")

    csv_uri = _discover_preprocess_train_csv(exec_arn)
    if csv_uri:
        (SCRIPT_DIR / "preprocess_train_s3_uri.txt").write_text(csv_uri, encoding="utf-8")
        print(f"Preprocess train.csv: {csv_uri}")
    else:
        print("WARN: Could not resolve preprocess train URI (inspect pipeline execution in Console).")


if __name__ == "__main__":
    main()
