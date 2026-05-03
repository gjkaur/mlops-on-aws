# Lab 8 — End-to-End Capstone (code + Terraform)

Participant walkthrough: **[`participant/lab8-capstone/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab8-capstone/PARTICIPANT_LAB_GUIDE.md)** · Folder index **[`LAB8_PARTICIPANT_INDEX.md`](../../participant/lab8-capstone/LAB8_PARTICIPANT_INDEX.md)**.

Integrated **pipeline → registry gate → realtime canary w/ capture → DQ monitor → EventBridge retrain**.

## Terraform (`infrastructure/`)

```bash
cd labs/lab8-capstone/infrastructure
cp terraform.tfvars.example terraform.tfvars
terraform init && terraform apply
```

Outputs:

| Output | Exported env suggestion |
|--------|--------------------------|
| `data_bucket_name` | `DATA_BUCKET_NAME` (+ EventBridge `new-data/`) |
| `artifacts_bucket_name` | `ARTIFACTS_BUCKET_NAME` (pipelines/train artifacts) |
| `capture_bucket_name` | `CAPTURE_BUCKET_NAME` |
| `reports_bucket_name` | `REPORTS_BUCKET_NAME` |
| `sagemaker_role_arn` | `SAGEMAKER_ROLE_ARN` |
| `eventbridge_role_arn` | `EVENTBRIDGE_ROLE_ARN` |
| `sns_topic_arn` | `SNS_TOPIC_ARN` |

Remember to **confirm the SNS subscription email** before demos.

PowerShell equivalents:

```powershell
$env:DATA_BUCKET_NAME = terraform output -raw data_bucket_name
$env:ARTIFACTS_BUCKET_NAME = terraform output -raw artifacts_bucket_name
$env:CAPTURE_BUCKET_NAME = terraform output -raw capture_bucket_name
$env:REPORTS_BUCKET_NAME = terraform output -raw reports_bucket_name
$env:SAGEMAKER_ROLE_ARN = terraform output -raw sagemaker_role_arn
$env:EVENTBRIDGE_ROLE_ARN = terraform output -raw eventbridge_role_arn
$env:SNS_TOPIC_ARN = terraform output -raw sns_topic_arn
```

## Script order (`scripts/`)

```bash
cd ../scripts

python pipeline_definition.py
python run_pipeline.py                         # persists preprocess_train_s3_uri on success gate
python approve_model_package.py
python deploy_canary.py
python monitoring_setup.py                     # DQ baseline + schedule + CW alarm → SNS_TOPIC_ARN
python trigger_retraining.py
python simulate_workflow.py
python cleanup.py                              # destroys SageMaker + EB + CW artefacts; not buckets
```

`trigger_retraining.py delete` mirrors Lab 5 for tear-down rehearsals.

### CSV contract

Preprocessing emits **seven** churn features + churn label (**no CSV header**) before deployment:  
`tenure, monthly_charges, support_tickets, payment_delays, contract_* one-hots ×3`.

Realtime inputs must replay that exact ordering (**text/csv** row with **seven** floats). See **`data/sample_churn_data.csv`** for layout.

### Environment tweak knobs (`CAPSTONE_*`)

| Env | Behaviour |
|-----|-----------|
| `CAPSTONE_ENDPOINT_NAME` | Pin deterministic endpoint naming |
| `CAPSTONE_APPROVAL` | Defaults `Approved` (set `Rejected` for failure drills) |
| `CAPSTONE_BLUE_WEIGHT` / `GREEN_WEIGHT` | Adjust multi-variant percentages |
| `LAB8_MONITOR_NOW` | Shortcut single-shot DQ window (narrow windows risk missing buffered captures — explain during class) |

## Deliverables cue (students)

- Architecture collage covering **Artifacts vs Data buckets**, EventBridge, registry, realtime path, DQ monitor (**see rubric doc**).
- **Model Card** pointers (borrow Lab 4 language).
- 5‑minute narration emphasising separation of automation vs approvals.
