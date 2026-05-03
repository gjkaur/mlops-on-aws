"""Remove auto-scaling policy, SageMaker endpoint, configs, and lab-created models."""

from __future__ import annotations

from pathlib import Path

import boto3
from botocore.exceptions import ClientError

SCRIPT_DIR = Path(__file__).resolve().parent
REGION = "us-east-1"
SCALABLE = "sagemaker:variant:DesiredInstanceCount"


def _remove_autoscaling(endpoint: str):
    aas = boto3.client("application-autoscaling", region_name=REGION)
    targets: dict[tuple[str, str], None] = {}
    token = None
    while True:
        kwargs: dict = {"ServiceNamespace": "sagemaker", "MaxResults": 50}
        if token:
            kwargs["NextToken"] = token
        resp = aas.describe_scalable_targets(**kwargs)
        for t in resp.get("ScalableTargets", []):
            rid = t["ResourceId"]
            if rid.startswith(f"endpoint/{endpoint}/"):
                targets[(rid, t["ScalableDimension"])] = None
        token = resp.get("NextToken")
        if not token:
            break

    st = SCRIPT_DIR / "scalable_target_id.txt"
    if st.is_file():
        rid = st.read_text(encoding="utf-8").strip()
        if rid:
            targets[(rid, SCALABLE)] = None

    for resource_id, dim in targets:
        pol = aas.describe_scaling_policies(
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension=dim,
        )
        for p in pol.get("ScalingPolicies", []):
            aas.delete_scaling_policy(
                PolicyName=p["PolicyName"],
                ServiceNamespace="sagemaker",
                ResourceId=resource_id,
                ScalableDimension=dim,
            )
        try:
            aas.deregister_scalable_target(
                ServiceNamespace="sagemaker",
                ResourceId=resource_id,
                ScalableDimension=dim,
            )
        except Exception as exc:
            print(f"Deregister scalable target skipped: {exc}")


def _delete_endpoint_and_related(sm, endpoint_name: str) -> None:
    try:
        sm.delete_endpoint(EndpointName=endpoint_name)
        print(f"Deleting endpoint {endpoint_name}...")
        waiter = sm.get_waiter("endpoint_deleted")
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={"Delay": 15, "MaxAttempts": 40},
        )
    except Exception as exc:
        print(f"Endpoint delete: {exc}")


def _delete_config(sm, cfg_name: str) -> None:
    try:
        sm.delete_endpoint_config(EndpointConfigName=cfg_name)
        print(f"Deleted EndpointConfig {cfg_name}")
    except Exception as exc:
        print(f"Endpoint config delete skipped ({cfg_name}): {exc}")


def _delete_model(sm, name: str) -> None:
    try:
        sm.delete_model(ModelName=name)
        print(f"Deleted model {name}")
    except Exception as exc:
        print(f"Model delete skipped ({name}): {exc}")


def main():
    print("=" * 60)
    print("LAB 6 CLEANUP")
    ef = SCRIPT_DIR / "endpoint_name.txt"
    if not ef.is_file():
        print("No endpoint_name.txt — nothing server-side to delete.")
        return

    endpoint = ef.read_text(encoding="utf-8").strip()
    sm = boto3.client("sagemaker", region_name=REGION)

    try:
        _remove_autoscaling(endpoint)
    except Exception as exc:
        print(f"Autoscaling cleanup: {exc}")

    try:
        desc = sm.describe_endpoint(EndpointName=endpoint)
        cfg = desc["EndpointConfigName"]

        variants = desc.get("ProductionVariants", [])
        variant_models = []
        for v in variants:
            variant_models.append(v["ModelName"])

        _delete_endpoint_and_related(sm, endpoint)
        _delete_config(sm, cfg)

        extras = {_m for _m in variant_models}

        sf = SCRIPT_DIR / "canary_state.txt"
        if sf.is_file():
            kv = dict(
                line.split("=", 1)
                for line in sf.read_text(encoding="utf-8").splitlines()
                if "=" in line
            )
            extras.update({kv[k] for k in ("blue_model", "green_model") if k in kv})

        for mname in sorted(extras):
            _delete_model(sm, mname)

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ValidationException":
            print(f"Endpoint {endpoint} not found ({exc}); continuing local tidy.")
        else:
            raise

    for name in (
        "endpoint_name.txt",
        "endpoint_variant_name.txt",
        "scalable_target_id.txt",
        "canary_state.txt",
        "model_data_uri.txt",
        "training_job_name.txt",
    ):
        fp = SCRIPT_DIR / name
        if fp.is_file():
            fp.unlink()

    print("Local state files cleared.")
    print("Run terraform destroy from infrastructure/ to drop the sandbox bucket.")


if __name__ == "__main__":
    main()
