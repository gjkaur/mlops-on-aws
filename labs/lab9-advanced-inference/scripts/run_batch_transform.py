"""
Run SageMaker Batch Transform (Lab 9).
"""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import pandas as pd
import sagemaker
from sklearn.datasets import make_classification

from sagemaker.sklearn import SKLearnModel

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"


def upload_batch_csv(bucket_name: str) -> str:
    """Upload 100-line CSV without header consistent with sklearn training features."""
    X, _ = make_classification(
        n_samples=100,
        n_features=10,
        n_informative=8,
        n_redundant=2,
        random_state=123,
    )

    csv_path = SCRIPT_DIR / "batch_input.csv"
    pd.DataFrame(X).to_csv(csv_path, index=False, header=False)

    key = "batch-input/data.csv"
    boto3.client("s3", region_name=REGION).upload_file(
        str(csv_path), bucket_name, key
    )
    prefix = f"s3://{bucket_name}/batch-input/"
    print(f"✓ Batch data → s3://{bucket_name}/{key}")
    return prefix


def run_batch_transform(
    model_uri: str, role_arn: str, input_s3_uri: str, output_s3_uri: str
):
    print("=" * 60)
    print("RUNNING BATCH TRANSFORM")
    print("=" * 60)
    print(f"Input prefix: {input_s3_uri}")
    print(f"Output prefix: {output_s3_uri}")

    boto_sess = boto3.Session(region_name=REGION)
    sess = sagemaker.Session(boto_session=boto_sess)

    model = SKLearnModel(
        model_data=model_uri,
        role=role_arn,
        entry_point="inference.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=sess,
    )

    transformer = model.transformer(
        instance_count=1,
        instance_type="ml.m5.large",
        output_path=output_s3_uri,
        strategy="SingleRecord",
        assemble_with="Line",
        accept="application/json",
    )

    transformer.transform(
        data=input_s3_uri,
        content_type="text/csv",
        split_type="Line",
        wait=True,
        logs=True,
    )

    print("\n✅ Batch transform complete")


def main():
    bucket = os.environ.get("BUCKET_NAME", "").strip()
    role = os.environ.get("ROLE_ARN", "").strip()
    if not bucket or not role:
        raise SystemExit("ERROR: export BUCKET_NAME and ROLE_ARN.")

    model_uri = os.environ.get("MODEL_S3_URI", "").strip() or (
        f"s3://{bucket}/models/model-v2/model.tar.gz"
    )
    input_uri = upload_batch_csv(bucket)
    output_uri = f"s3://{bucket}/batch-output/"
    run_batch_transform(model_uri, role, input_uri, output_uri)


if __name__ == "__main__":
    main()
