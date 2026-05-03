# Lab 7 — Model monitoring & drift (instructor/student code bundle)

Participant steps: **[`participant/lab7-monitoring/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab7-monitoring/PARTICIPANT_LAB_GUIDE.md)** · Index: **[`LAB7_PARTICIPANT_INDEX.md`](../../participant/lab7-monitoring/LAB7_PARTICIPANT_INDEX.md)**.

Reuse **Terraform** for `us-east-1` sandbox infra, then iterate **Python helpers** locally (`.txt` breadcrumb files in `scripts/` tie the steps together).

## Prerequisites

- Lab 00 account + programmatic access
- `terraform` CLI, Python 3.10+, deps from repo root `requirements.txt`
- Estimated runtime: sklearn training (~5 min), capture endpoint (~10 min), baseline job (~5–15 min), monitoring executions on hourly cron

## Provision

```bash
cd labs/lab7-monitoring/infrastructure
cp terraform.tfvars.example terraform.tfvars  # edit alert_email (+ optional aws_account_id)
terraform init && terraform apply
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw monitoring_role_arn)
export SNS_TOPIC_ARN=$(terraform output -raw sns_topic_arn)
```

Confirm the SNS email subscription Terraform requested.

## Runbook (`scripts/`)

```bash
cd ../scripts

python train_model.py
python deploy_with_capture.py
python generate_baseline.py
python create_monitoring_schedule.py          # LAB7_MONITOR_NOW=1 Optional “run once now” knob
python test_endpoint.py
export BUCKET_NAME=...                         # Notebook + S3 listing convenience
python setup_alerts.py
python simulate_drift.py
python cleanup.py
```

Artifacts land under `lab7/` inside the sandbox bucket (`data-capture`, `baseline-output`, `reports`, etc.).

## Reference docs

| File | Audience |
|------|----------|
| `LAB_OVERVIEW.md` | Module abstract |
| `INSTRUCTOR_LAB_GUIDE.md` | Teaching notes |
| `solutions/lab7/LAB7_SOLUTION_REFERENCE.md` | Cheat sheet |

## Environment knobs

| Variable | Purpose |
|----------|---------|
| `LAB7_MONITOR_NOW` | `1` ⇒ `CronExpressionGenerator.now()` (+ `LAB7_NOW_START`/`LAB7_NOW_END`) |
| `LAB7_CAPTURE_URI`, `LAB7_REPORTS_URI` | Overrides for capture/report prefixes |
| `LAB7_ALARM_FEATURE_COL` | Force drift metric suffix if telemetry names differ |
