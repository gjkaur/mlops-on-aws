# Lab 7 — Monitoring & drift (instructor cheat sheet)

## Resource tally

Terraform: **bucket + versioning + PA block + IAM role + 3 × managed policy attachments + SNS topic + email subscription** (≈9 base resources excluding random id).

Operational: **Monitoring schedule + DQ job definition + processing/baseline jobs**, **Realtime endpoint trio** (endpoint / config / model), **CW alarm**.

## Telemetry contract

- **Invoke body**: CSV row of length **10**.
- **`inference.py` JSON**: `prediction`, **`probability_positive`** (Lab 6 parity).
- **Baseline CSV**: **`baseline_features.csv`** — **`X_train` only**, **no header**, **10 cols**.

## Scripted breadcrumbs (`labs/lab7-monitoring/scripts`)

| Writer | Outputs |
|--------|---------|
| **`train_model.py`** | local `*.csv`, `model_data_uri.txt`, `baseline_features_s3_uri.txt`, `training_job_name.txt` |
| **`deploy_with_capture.py`** | `endpoint_name.txt`, `capture_s3_uri.txt`, `endpoint_variant_name.txt` |
| **`generate_baseline.py`** | `statistics_s3_uri.txt`, `constraints_s3_uri.txt`, `baseline_output_s3_uri.txt` |
| **`create_monitoring_schedule.py`** | `schedule_name.txt` |
| **`setup_alerts.py`** | `cloudwatch_alarm_name.txt` |

## CloudWatch recap

Alarm targets **`feature_baseline_drift_<baselineColumn0>`**, namespace **`/aws/sagemaker/Endpoints/data-metric`**, dimensions **`EndpointName`**, **`ScheduleName`** (not `Endpoint`).

If CloudWatch silently omits datapoints until the first hourly execution completes, rerun **`describe_alarms`** after the cron fires.

## Optional accelerators

```bash
export LAB7_MONITOR_NOW=1 LAB7_NOW_START=-P1D LAB7_NOW_END=-PT1S
python create_monitoring_schedule.py   # Narrow windows may miss buffered captures — test first!
```

Manual alarm column override:

```bash
export LAB7_ALARM_FEATURE_COL='<exact statistics.json feature name>'
```

## Cleanup pitfalls

Attach-based deletion handles **data-quality job definition** cleanup; boto-only fallback deletes schedule shells but may orphan definitions if IAM denies attachments.
