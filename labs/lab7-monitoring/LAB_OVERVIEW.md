# Lab 7: Model Monitoring & Drift Detection (Module 7)

| Attribute | Value |
|-----------|-------|
| **Duration** | ~90 minutes |
| **Difficulty** | Intermediate |
| **Region** | `us-east-1` |

Students enable **capture** on a realtime sklearn endpoint, build a **data-quality baseline** from feature-only CSV (matching capture shape), attach an hourly **monitoring schedule**, skim **reports in S3**, and wire **CloudWatch → SNS**.

## Layout

| Path | Role |
|------|------|
| `infrastructure/` | S3 sandbox, IAM role, SNS alerts topic (+ email subscription stub) |
| `scripts/` | Train → capture deploy → baseline → schedule → drift load → SNS alarm helpers |
| `notebooks/monitoring_analysis.ipynb` | Lightweight S3/report inspection patterns |
| **`INSTRUCTOR_LAB_GUIDE.md`** | Classroom pacing & pitfalls |
| Participant walkthrough | [`PARTICIPANT_LAB_GUIDE.md`](../../participant/lab7-monitoring/PARTICIPANT_LAB_GUIDE.md) |
| Instructor solution | [`LAB7_SOLUTION_REFERENCE.md`](../../solutions/lab7/LAB7_SOLUTION_REFERENCE.md) |
## Flow (high level)

1. **`terraform apply`** → bucket + IAM + SNS ARN.
2. **`train_model.py`** → uploads training CSV + **`baseline_features.csv`** (10 columns, headerless — same as invokes).
3. **`deploy_with_capture.py`** → endpoint + **`DataCaptureConfig`** (`lab7/data-capture/` prefix).
4. **`generate_baseline.py`** → `DefaultModelMonitor.suggest_baseline` → writes `statistics_s3_uri.txt` / `constraints_s3_uri.txt`.
5. **`create_monitoring_schedule.py`** → data-quality cron (hourly default, optional `LAB7_MONITOR_NOW=1`).
6. **`simulate_drift.py`** + **`test_endpoint.py`** traffic.
7. **`setup_alerts.py`** → CloudWatch alarm on `feature_baseline_drift_<firstBaselineColumn>` (`/aws/sagemaker/Endpoints/data-metric`).
8. **`cleanup.py`** + **`terraform destroy`**.
