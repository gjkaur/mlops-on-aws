"""
Canary-style multi-variant endpoint update (Lab 6).

Default demo reuses the SAME model tarball for blue + green to keep the lab short.
Run train_model.py twice and set GREEN_MODEL_DATA_URI to the second artifact for a real A/B.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import boto3
import sagemaker
from sagemaker.sklearn import SKLearnModel

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _session():
    b = boto3.Session(region_name=REGION)
    return sagemaker.Session(boto_session=b)


def _create_sklearn_model(sm_client, session, model_name: str, artifact: str, role_arn: str):
    sk = SKLearnModel(
        model_data=artifact,
        role=role_arn,
        entry_point="inference.py",
        source_dir=str(SCRIPT_DIR),
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=session,
    )
    container = sk.prepare_container_def(instance_type="ml.t2.medium")
    sm_client.create_model(
        ModelName=model_name,
        PrimaryContainer=container,
        ExecutionRoleArn=role_arn,
    )


def apply_canary(role_arn: str, blue_weight: float, green_weight: float) -> None:
    endpoint = os.environ.get("ENDPOINT_NAME", "").strip()
    if not endpoint:
        ef = SCRIPT_DIR / "endpoint_name.txt"
        endpoint = ef.read_text(encoding="utf-8").strip() if ef.is_file() else ""
    if not endpoint:
        raise SystemExit("ERROR: deploy_endpoint.py first (endpoint_name.txt).")

    blue_uri = (SCRIPT_DIR / "model_data_uri.txt").read_text(encoding="utf-8").strip()
    green_uri = os.environ.get("GREEN_MODEL_DATA_URI", blue_uri).strip()

    sm = boto3.client("sagemaker", region_name=REGION)
    session = _session()

    ts = int(time.time())
    blue_model = f"lab6-blue-{ts}"
    green_model = f"lab6-green-{ts}"
    _create_sklearn_model(sm, session, blue_model, blue_uri, role_arn)
    _create_sklearn_model(sm, session, green_model, green_uri, role_arn)

    cfg_name = f"lab6-canary-{ts}"
    sm.create_endpoint_config(
        EndpointConfigName=cfg_name,
        ProductionVariants=[
            {
                "VariantName": "blue",
                "ModelName": blue_model,
                "InstanceType": "ml.t2.medium",
                "InitialInstanceCount": 1,
                "InitialVariantWeight": blue_weight,
            },
            {
                "VariantName": "green",
                "ModelName": green_model,
                "InstanceType": "ml.t2.medium",
                "InitialInstanceCount": 1,
                "InitialVariantWeight": green_weight,
            },
        ],
    )

    sm.update_endpoint(EndpointName=endpoint, EndpointConfigName=cfg_name)
    waiter = sm.get_waiter("endpoint_in_service")
    print("Waiting until endpoint finishes update (often several minutes)...")
    waiter.wait(EndpointName=endpoint)

    print("Canary routing active.")
    print(f"  EndpointConfig: {cfg_name}")
    print(f"  Blue (weight {blue_weight}): {blue_model}")
    print(f"  Green (weight {green_weight}): {green_model}")

    state = {
        "endpoint": endpoint,
        "config": cfg_name,
        "blue_model": blue_model,
        "green_model": green_model,
    }
    (SCRIPT_DIR / "canary_state.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in state.items()), encoding="utf-8"
    )
    # refresh variant tracker for autoscaler callers
    ep = sm.describe_endpoint(EndpointName=endpoint)
    # multi-variant scaling usually targets primary variant named in policy — document multi-variant caveat
    (SCRIPT_DIR / "endpoint_variant_name.txt").write_text(
        ep["ProductionVariants"][0]["VariantName"], encoding="utf-8"
    )


def promote_green_only() -> None:
    sf = SCRIPT_DIR / "canary_state.txt"
    if not sf.is_file():
        raise SystemExit("ERROR: run `canary_deployment.py apply` first.")

    kv = dict(line.split("=", 1) for line in sf.read_text(encoding="utf-8").splitlines())
    endpoint = kv["endpoint"]
    green_model = kv["green_model"]

    sm = boto3.client("sagemaker", region_name=REGION)
    ts = int(time.time())
    cfg_name = f"lab6-stable-{ts}"
    sm.create_endpoint_config(
        EndpointConfigName=cfg_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": green_model,
                "InstanceType": "ml.t2.medium",
                "InitialInstanceCount": 1,
            }
        ],
    )
    sm.update_endpoint(EndpointName=endpoint, EndpointConfigName=cfg_name)
    sm.get_waiter("endpoint_in_service").wait(EndpointName=endpoint)
    print(f"Promotion complete — single-variant config {cfg_name} using former green model.")
    (SCRIPT_DIR / "endpoint_variant_name.txt").write_text("AllTraffic", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Lab 6 multi-variant routing demo.")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("apply", help="Deploy 90/10 style split (adjust via flags)")
    a.add_argument("--blue-weight", type=float, default=90.0)
    a.add_argument("--green-weight", type=float, default=10.0)

    sub.add_parser("promote-green", help="Collapse to single variant using winning green")

    args = p.parse_args()

    if args.cmd == "apply":
        role_arn = os.environ.get("ROLE_ARN", "").strip()
        if not role_arn:
            raise SystemExit("ERROR: Set ROLE_ARN.")
        apply_canary(role_arn, args.blue_weight, args.green_weight)
    elif args.cmd == "promote-green":
        promote_green_only("")


if __name__ == "__main__":
    main()
