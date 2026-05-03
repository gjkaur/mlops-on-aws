"""Send blended traffic — in-distribution samples then shifted features — Lab 7."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import numpy as np
import sagemaker
from sagemaker.deserializers import JSONDeserializer
from sagemaker.serializers import CSVSerializer
from sagemaker.predictor import Predictor

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def send_normal(predictor: Predictor, num_requests: int = 40) -> None:
    print(f"\nSending {num_requests} in-distribution requests...")
    for i in range(num_requests):
        sample = np.random.randn(10).tolist()
        response = predictor.predict(sample)
        if i % 10 == 0:
            print(
                f"  Request {i + 1}: prediction={response.get('prediction')} "
                f"P(pos)={response.get('probability_positive', 0):.3f}"
            )


def send_drift(predictor: Predictor, num_requests: int = 60, strength: float = 2.0) -> None:
    print(f"\nSending {num_requests} shifted requests (mean shift ≈ +{strength})...")
    for i in range(num_requests):
        sample = (np.random.randn(10) * strength + strength).tolist()
        response = predictor.predict(sample)
        if i % 10 == 0:
            print(
                f"  Request {i + 1}: prediction={response.get('prediction')} "
                f"P(pos)={response.get('probability_positive', 0):.3f}"
            )


def main():
    en_f = SCRIPT_DIR / "endpoint_name.txt"
    if not en_f.is_file():
        print("ERROR: Run deploy_with_capture.py first.")
        raise SystemExit(1)
    endpoint_name = en_f.read_text(encoding="utf-8").strip()

    boto_sess = boto3.Session(region_name=REGION)
    predictor = Predictor(
        endpoint_name=endpoint_name,
        sagemaker_session=sagemaker.Session(boto_session=boto_sess),
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )

    print("=" * 60)
    print("LAB 7 DRIFT SIMULATION TRAFFIC")
    print(f"endpoint={endpoint_name}")
    print("=" * 60)

    send_normal(predictor)
    send_drift(predictor, num_requests=int(os.environ.get("LAB7_DRIFT_N", "60")))

    bucket = os.environ.get("BUCKET_NAME", "")
    print("\nMonitoring jobs compare captures to baseline (may take until the hourly tick).")
    if bucket:
        print(f"S3 captures: s3://{bucket}/lab7/data-capture/")
        print(f"S3 reports: s3://{bucket}/lab7/reports/")
    print("CloudWatch drift metrics: namespace /aws/sagemaker/Endpoints/data-metric")


if __name__ == "__main__":
    main()
