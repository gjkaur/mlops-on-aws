# Lab 7 Instructor Notes — Monitoring & drift

## Learning goals

Articulate why **captures**, **statistics/constraints**, and **scheduled executions** isolate *data drift* from *model regressions*. Contrast SNS fan-out vs ticket routing in real programs.

## Suggested narration

1. **Capture** persists what the variant actually consumed — not the training corpus.
2. **Baseline** aligns with **`DatasetFormat.csv(header=False)` + 10 floats** identical to realtime CSV invokes (mirrors Lab 6’s contract).
3. **Hourly cron** aligns with **`Period=3600`** alarms; demos can opt into **`LAB7_MONITOR_NOW=1`** cautiously (narrow analysis windows may miss buffered captures).
4. **CloudWatch metric** spelling matters: **`/aws/sagemaker/Endpoints/data-metric`**, **`EndpointName`**, **`ScheduleName`**, **`feature_baseline_drift_<column>`**.
5. **Cost hygiene**: **`cleanup.py` first**, then **`terraform destroy`** once endpoints finish deleting.

## Dry-run sequencing

Infrastructure → **`train_model.py`** → **`deploy_with_capture.py`** → **`generate_baseline.py`** → **`create_monitoring_schedule.py`** → **`test_endpoint`** / **`simulate_drift`** → **`setup_alerts.py`**.

Budget ~35–45 minutes of wall clock excluding the first hourly firing.

## Common classroom issues

| Symptom | Likely fix |
|---------|------------|
| Baselines fail | Wrong CSV shape vs capture (must be exactly 10 feature columns without header rows) |
| Empty capture prefix | Buffer delay (~2 min); confirm `SamplingPercentage=100`; verify prefix `lab7/data-capture/` |
| Schedule stuck Pending | Typical for a few minutes; confirm role has **`AmazonSageMakerFullAccess`** + S3 RW |
| Alarm never fires | Metric/dimension mismatch (`Endpoint` ≠ **`EndpointName`**); rerun after first execution emits metrics |
| Email missing | Spam + **SNS confirmation** |

## Privacy note

Captured payloads may resemble production traffic — purge bucket aggressively after class.
