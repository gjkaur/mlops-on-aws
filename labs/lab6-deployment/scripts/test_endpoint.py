"""Invoke a deployed realtime endpoint via SDK + boto3 runtime and optional load test."""

from __future__ import annotations

import concurrent.futures
import json
import os
import time
from pathlib import Path

import boto3
import numpy as np
from sagemaker.deserializers import JSONDeserializer
from sagemaker.predictor import Predictor
from sagemaker.serializers import CSVSerializer

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"
N_FEATURES = 10


def _endpoint_name() -> str:
    name = os.environ.get("ENDPOINT_NAME", "").strip()
    if not name:
        f = SCRIPT_DIR / "endpoint_name.txt"
        if f.is_file():
            name = f.read_text(encoding="utf-8").strip()
    if not name:
        raise SystemExit("ERROR: Set ENDPOINT_NAME or run deploy_endpoint.py first.")
    return name


def test_sdk(endpoint_name: str) -> None:
    print("=" * 60)
    print("INVOKE via SageMaker Predictor (CSV)")
    predictor = Predictor(
        endpoint_name=endpoint_name,
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )

    rng = np.random.RandomState(0)
    row = rng.rand(1, N_FEATURES).astype("float64")
    out = predictor.predict(row)
    if isinstance(out, (bytes, str)):
        out = json.loads(out if isinstance(out, str) else out.decode())

    print("Single row prediction:")
    print(f"  input (first 3): {row.ravel()[:3].tolist()} ...")
    print(f"  output: {json.dumps(out, indent=2)}")

    print("Mini batch:")
    for i in range(3):
        samp = rng.rand(1, N_FEATURES).astype("float64")
        resp = predictor.predict(samp)
        if isinstance(resp, (bytes, str)):
            resp = json.loads(resp if isinstance(resp, str) else resp.decode())
        print(
            f"  sample {i + 1}: class={resp.get('prediction')} "
            f"p_pos={resp.get('probability_positive', resp.get('probability')):.4f}"
        )


def test_boto3(endpoint_name: str) -> None:
    print("=" * 60)
    print("INVOKE via sagemaker-runtime (text/csv)")
    rt = boto3.client("sagemaker-runtime", region_name=REGION)
    rng = np.random.RandomState(1)
    csv_body = ",".join(str(float(x)) for x in rng.rand(N_FEATURES).tolist())

    rsp = rt.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="text/csv",
        Accept="application/json",
        Body=csv_body,
    )
    payload = rsp["Body"].read()
    obj = json.loads(payload)
    print(f"CSV body preview: {csv_body[:48]}...")
    print(f"Parsed JSON: {obj}")


def load_test(endpoint_name: str, num_requests: int = 40, concurrency: int = 5) -> None:
    print("=" * 60)
    print(f"LOAD TEST: {num_requests} requests ({concurrency} workers)")

    predictor = Predictor(
        endpoint_name=endpoint_name,
        serializer=CSVSerializer(),
        deserializer=JSONDeserializer(),
    )
    rng = np.random.RandomState(42)

    def one(i: int):
        sample = rng.rand(1, N_FEATURES).astype("float64")
        t0 = time.time()
        out = predictor.predict(sample)
        if isinstance(out, (bytes, str)):
            out = json.loads(out if isinstance(out, str) else out.decode())
        dt = time.time() - t0
        return i, dt, out.get("prediction")

    t_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        results = list(ex.map(one, range(num_requests)))
    total = time.time() - t_start

    lat = [r[1] for r in results]
    ok = sum(1 for r in results if r[2] is not None)
    print(f"Successful: {ok}/{num_requests}")
    print(f"Wall clock: {total:.2f}s (~{ok / total:.2f} ok/s)")
    print(f"Avg latency: {float(np.mean(lat)):.4f}s  max={max(lat):.4f}s")


def main():
    endpoint = _endpoint_name()
    print(f"Endpoint: {endpoint}")
    test_sdk(endpoint)
    test_boto3(endpoint)
    load_test(endpoint)


if __name__ == "__main__":
    main()
