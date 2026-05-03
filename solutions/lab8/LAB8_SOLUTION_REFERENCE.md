# Lab 8 — Capstone cheatsheet

## IaC tally

Roughly twenty Terraform-managed resources (`random`, four buckets incl. artefacts versioning + data EventBridge forwarding, SNS pair + attachments, duplicated IAM envelopes). Operational spend lives in pipelines / endpoints / DQ jobs—teardown **`scripts/cleanup.py` first**.

## Pipeline graph

`Preprocess (SKLearn Processor)` → `Train (RandomForest sklearn estimator)` → `Evaluate (scores test split)` → `JsonGet.Condition` referencing `evaluation.json.accuracy` → `RegisterModel` (`PendingManualApproval`).

Accuracy gate default `0.75` — lower `AccuracyThreshold` parameter if RNG churn drops below threshold sporadically.

## Breadcrumbs

| File | Writer |
|------|--------|
| `pipeline_name.txt` | `pipeline_definition.py` |
| `model_package_group.txt` | `pipeline_definition.py` |
| `preprocess_train_s3_uri.txt` | `run_pipeline.py` |
| `approved_model_package_arn.txt` | `approve_model_package.py` |
| `endpoint_name.txt` / `capture_s3_uri.txt` | `deploy_canary.py` |
| `schedule_name.txt` / `cloudwatch_alarm_name.txt` | `monitoring_setup.py` |
| `eventbridge_rule_name.txt` | `trigger_retraining.py` |

## Serving duplication trick

Canary copies the same **`PrimaryContainer`** twice with distinct **`ModelName`s** + weights **`InitialVariantWeight`**. Mention contrast with real heterogeneous releases.

Capture survives canary uplift by cloning **`describe_endpoint_config["DataCaptureConfig"]`**.

## DQ + alarms

Namespace **`/aws/sagemaker/Endpoints/data-metric`**, dims **`EndpointName` + ScheduleName**, metric **`feature_baseline_drift_<column>`**.

## EventBridge caveat

Buckets must publish to EventBridge (Terraform **`eventbridge=true`** on **`DATA_BUCKET` only**).
