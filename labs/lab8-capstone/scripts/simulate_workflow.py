"""
Exercise the realtime endpoint plus upload a sentinel CSV so EventBridge starts the churn pipeline.

Feature order mirrors preprocess.py CSV columns before the trailing churn label column.
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import boto3
import numpy as np
import pandas as pd
import sagemaker
from sagemaker.deserializers import JSONDeserializer
from sagemaker.predictor import Predictor
from sagemaker.serializers import CSVSerializer

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _random_rows(n: int) -> pd.DataFrame:
    rows = []
    for _ in range(n):
        tenure = np.random.randint(1, 72)
        monthly = round(float(np.random.uniform(20, 119)), 2)
        tickets = int(np.random.poisson(1))
        delays = int(np.random.poisson(0.6))
        c = np.random.randint(0, 3)
        mm = float(c == 0)
        oy = float(c == 1)
        ty = float(c == 2)
        rows.append([tenure, monthly, tickets, delays, mm, oy, ty])
    cols = [
        "tenure",
        "monthly_charges",
        "support_tickets",
        "payment_delays",
        "contract_type_Month-to-month",
        "contract_type_One year",
        "contract_type_Two year",
    ]
    return pd.DataFrame(rows, columns=cols)


def _upload_new_data_bucket(bucket: str):
    df = _random_rows(96)
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False)
    key = "new-data/capstone-simulated-batch.csv"
    boto3.client("s3", region_name=REGION).put_object(
        Bucket=bucket,
        Key=key,
        Body=buf.getvalue().encode("utf-8"),
    )
    print(f"Uploaded {key} → EventBridge attempts StartPipelineExecution on {bucket}.")


def main():
    data_bucket = os.environ.get("DATA_BUCKET_NAME", "").strip()
    endpoint = ""
    ef = SCRIPT_DIR / "endpoint_name.txt"
    if ef.is_file():
        endpoint = ef.read_text(encoding="utf-8").strip()

    boto_sess = boto3.Session(region_name=REGION)

    print("=" * 60)
    print("CAPSTONE DEMO — INFERENCE SMOKE + RETRAINING SEED OBJECT")

    if endpoint:
        print(f"Issuing realtime requests → {endpoint}")
        predictor = Predictor(
            endpoint_name=endpoint,
            sagemaker_session=sagemaker.Session(boto_session=boto_sess),
            serializer=CSVSerializer(),
            deserializer=JSONDeserializer(),
        )
        for idx in range(5):
            row = _random_rows(1).iloc[0].tolist()
            out = predictor.predict(row)
            pb = float(out.get("probability_positive") or 0)
            print(
                f"  Sample {idx+1}: preds={out.get('prediction')} P(+)= "
                f"{pb:.3f} | row[:4]={row[:4]}"
            )
    else:
        print("(Skip Predictor — endpoint_name.txt missing.)")

    if data_bucket:
        _upload_new_data_bucket(data_bucket)
    else:
        print("WARN: DATA_BUCKET_NAME unset — skipping seed upload.")

    print("Observe EventBridge executions in CloudWatch/Event history + SageMaker executions.")


if __name__ == "__main__":
    main()
