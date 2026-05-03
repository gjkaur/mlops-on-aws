"""
Smoke-test the monitored endpoint and list recent capture objects under lab7/data-capture/.
"""

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


def test_endpoint(predictor: Predictor) -> None:
    print("=" * 60)
    print("TEST REQUESTS")
    print("=" * 60)
    for i in range(5):
        sample = np.random.randn(10).tolist()
        response = predictor.predict(sample)
        print(f"\nSample {i + 1}:")
        print(f"  features[:3]={sample[:3]}")
        print(f"  prediction={response.get('prediction')}")
        prob = response.get("probability_positive")
        if prob is not None:
            print(f"  P(pos)={prob:.3f}")


def list_captures(bucket: str, limit: int = 5) -> None:
    s3 = boto3.client("s3", region_name=REGION)
    prefix = os.environ.get("LAB7_CAPTURE_PREFIX", "lab7/data-capture/")
    print("\n" + "=" * 60)
    print("RECENT CAPTURE OBJECTS")
    print("=" * 60)
    paginator = s3.get_paginator("list_objects_v2")
    keys: list[tuple[str, int]] = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, PaginationConfig={"MaxItems": 250}):
        for obj in page.get("Contents") or []:
            keys.append((obj["Key"], int(obj.get("Size") or 0)))
    keys.sort(key=lambda t: t[0], reverse=True)
    trim = keys[:limit]
    if not trim:
        print("None yet — wait ~2 minutes after invokes or check LAB7_CAPTURE_PREFIX.")
        return
    for k, sz in trim:
        print(f"  {k} ({sz} bytes)")


def main():
    bucket = os.environ.get("BUCKET_NAME")
    en_f = SCRIPT_DIR / "endpoint_name.txt"
    if not en_f.is_file():
        print("ERROR: Run deploy_with_capture.py first.")
        raise SystemExit(1)

    boto_sess = boto3.Session(region_name=REGION)
    endpoint_name = en_f.read_text(encoding="utf-8").strip()
    predictor = Predictor(
        endpoint_name=endpoint_name,
        sagemaker_session=sagemaker.Session(boto_session=boto_sess),
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )
    print(f"endpoint_name={endpoint_name}")
    test_endpoint(predictor)

    if bucket:
        list_captures(bucket)
    else:
        print("\nSet BUCKET_NAME to list capture objects in S3.")


if __name__ == "__main__":
    main()
