"""Register Application Auto Scaling target + target-tracking policy on a SageMaker endpoint variant."""

from __future__ import annotations

import os
import time
from pathlib import Path

import boto3

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"


def _endpoint_variant() -> tuple[str, str]:
    endpoint = os.environ.get("ENDPOINT_NAME", "").strip()
    if not endpoint:
        ef = SCRIPT_DIR / "endpoint_name.txt"
        if ef.is_file():
            endpoint = ef.read_text(encoding="utf-8").strip()
    if not endpoint:
        raise SystemExit(
            "ERROR: Set ENDPOINT_NAME or deploy first (endpoint_name.txt missing)."
        )

    vf = SCRIPT_DIR / "endpoint_variant_name.txt"
    if vf.is_file():
        variant = vf.read_text(encoding="utf-8").strip()
    else:
        sm = boto3.client("sagemaker", region_name=REGION)
        ep = sm.describe_endpoint(EndpointName=endpoint)
        variant = ep["ProductionVariants"][0]["VariantName"]
        vf.write_text(variant, encoding="utf-8")

    return endpoint, variant


def main():
    endpoint, variant = _endpoint_variant()
    resource_id = f"endpoint/{endpoint}/variant/{variant}"

    aas = boto3.client("application-autoscaling", region_name=REGION)

    print("=" * 60)
    print("APPLICATION AUTO SCALING (SageMaker variant)")
    print(f"ResourceId: {resource_id}")

    aas.register_scalable_target(
        ServiceNamespace="sagemaker",
        ResourceId=resource_id,
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        MinCapacity=1,
        MaxCapacity=3,
    )

    policy_name = f"lab6-rpm-{int(time.time())}"
    aas.put_scaling_policy(
        PolicyName=policy_name,
        ServiceNamespace="sagemaker",
        ResourceId=resource_id,
        ScalableDimension="sagemaker:variant:DesiredInstanceCount",
        PolicyType="TargetTrackingScaling",
        TargetTrackingScalingPolicyConfiguration={
            "TargetValue": 50.0,
            "PredefinedMetricSpecification": {
                "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance",
            },
            "ScaleInCooldown": 300,
            "ScaleOutCooldown": 120,
        },
    )

    print("Scalable target registered (min=1 max=3).")
    print(f"Target tracking policy: {policy_name} (invocations / instance / minute ≈ 50).")
    (SCRIPT_DIR / "scalable_target_id.txt").write_text(resource_id, encoding="utf-8")


if __name__ == "__main__":
    main()
