"""
Smoke-test serverless, asynchronous, and multi-model endpoints (Lab 9).

Reads endpoint names from sibling text files written by deploy scripts.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import boto3
import numpy as np
from sagemaker.deserializers import JSONDeserializer
from sagemaker.predictor import Predictor
from sagemaker.serializers import CSVSerializer

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
N_FEATURES = 10


def _prob(obj: dict) -> float:
    if "probability" in obj:
        return float(obj["probability"])
    return float(obj.get("probability_positive", 0.0))


def test_serverless(endpoint_name: str) -> None:
    print("\n" + "=" * 60)
    print("TEST SERVERLESS")
    print("=" * 60)

    predictor = Predictor(
        endpoint_name=endpoint_name,
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )

    row = np.random.RandomState(7).rand(1, N_FEATURES).astype("float64")
    print("First request may pay serverless cold-start tax…")
    t0 = time.time()
    out = predictor.predict(row)
    if isinstance(out, (bytes, str)):
        out = json.loads(out if isinstance(out, str) else out.decode())
    print(f"Response: {out}")
    print(f"Cold/warm path latency: {time.time() - t0:.2f}s")

    t1 = time.time()
    out2 = predictor.predict(row)
    if isinstance(out2, (bytes, str)):
        out2 = json.loads(out2 if isinstance(out2, str) else out2.decode())
    print(f"Second call: {time.time() - t1:.3f}s → {out2}")


def wait_s3_object(s3_uri: str, timeout_s: int = 600) -> bool:
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        return False
    bucket, key = parsed.netloc, parsed.path.lstrip("/")
    s3 = boto3.client("s3", region_name=REGION)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            time.sleep(2)
    return False


def test_async(endpoint_name: str, bucket_name: str) -> None:
    print("\n" + "=" * 60)
    print("TEST ASYNCHRONOUS")
    print("=" * 60)

    runtime = boto3.client("sagemaker-runtime", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)

    sample_csv = ",".join(str(float(x)) for x in np.random.RandomState(8).rand(N_FEATURES))
    payload_key = f"async-requests/request-{int(time.time())}.csv"
    s3.put_object(Bucket=bucket_name, Key=payload_key, Body=sample_csv.encode())
    inp = f"s3://{bucket_name}/{payload_key}"
    print(f"Input staged: {inp}")

    rsp = runtime.invoke_endpoint_async(
        EndpointName=endpoint_name,
        InputLocation=inp,
        ContentType="text/csv",
        Accept="application/json",
        InvocationTimeoutSeconds=3600,
    )

    output_loc = rsp.get("OutputLocation", "")
    print(f"Queued. Output manifest: {output_loc}")

    if not output_loc.startswith("s3://"):
        print("(No OutputLocation parsed — check InferenceId via console.)")
        return

    ok = wait_s3_object(output_loc, timeout_s=480)
    if ok:
        print("✓ Result object present in S3")
        parsed = urlparse(output_loc)
        body = (
            s3.get_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))["Body"]
            .read()
            .decode()
        )
        print(f"Snippet: {body[:200]}...")
    else:
        print("⚠ Timeout waiting for async output (still processing or IAM issue).")


def test_mme(endpoint_name: str) -> None:
    print("\n" + "=" * 60)
    print("TEST MULTI-MODEL ENDPOINT")
    print("=" * 60)

    rt = boto3.client("sagemaker-runtime", region_name=REGION)
    sample_csv = ",".join(map(str, np.random.RandomState(9).rand(N_FEATURES)))

    models = ["model-v1", "model-v2", "model-v3"]
    for name in models:
        target = f"{name}/model.tar.gz"
        rsp = rt.invoke_endpoint(
            EndpointName=endpoint_name,
            TargetModel=target,
            ContentType="text/csv",
            Accept="application/json",
            Body=sample_csv.encode("utf-8"),
        )
        raw = rsp["Body"].read()
        result = json.loads(raw)
        print(
            f"{name}: prediction={result.get('prediction')} prob={_prob(result):.3f}",
        )


def main():
    bucket = os.environ.get("BUCKET_NAME", "").strip()

    srv = SCRIPT_DIR / "serverless_endpoint_name.txt"
    if srv.is_file():
        test_serverless(srv.read_text(encoding="utf-8").strip())

    async_f = SCRIPT_DIR / "async_endpoint_name.txt"
    if async_f.is_file():
        ep = async_f.read_text(encoding="utf-8").strip()
        if not bucket:
            print("⚠ Missing BUCKET_NAME — skip async test.")
        else:
            test_async(ep, bucket)

    mme_f = SCRIPT_DIR / "mme_endpoint_name.txt"
    if mme_f.is_file():
        test_mme(mme_f.read_text(encoding="utf-8").strip())

    print("\n✅ test_endpoints sweep complete")


if __name__ == "__main__":
    main()
