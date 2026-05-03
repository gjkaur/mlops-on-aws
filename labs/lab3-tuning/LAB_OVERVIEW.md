# Lab 3: Hyperparameter tuning & experiments

Module **3 – Experimentation** · **`us-east-1`** · about **90 minutes**

## Goals

- Run a baseline sklearn SageMaker training job on the Diabetes dataset  
- Launch **Hyperparameter Tuner** (Bayesian-style search + early stopping) minimizing **RMSE**  
- Inspect results with **`HyperparameterTuningJobAnalytics`** and plots emitted by **`analyze_results.py`**  
- **Deploy** the champion trial to an endpoint (**`predict.py`**)

## Prerequisites

- [Lab 00](../../participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) (AWS CLI)  
- Repo root: `pip install -r requirements.txt` (`matplotlib`, `sagemaker`, `scikit-learn`, …)

## Participant lab guide

- **[PARTICIPANT_LAB_GUIDE.md](../../participant/lab3-tuning/PARTICIPANT_LAB_GUIDE.md)** — step-by-step  
- **[LAB3_PARTICIPANT_INDEX.md](../../participant/lab3-tuning/LAB3_PARTICIPANT_INDEX.md)** — folder index  

## Layout

| Path | Purpose |
|------|---------|
| `infrastructure/` | S3 bucket + SageMaker IAM role (`sagemaker_role_arn`) |
| `scripts/train.py` | SageMaker training entry (hyperparameters as CLI args); logs `rmse:` / `r2:` lines for tuner metrics |
| `scripts/predict.py` | Lightweight inference hooks for realtime hosting |
| `scripts/baseline.py` | Single default training job (`baseline_job_name.txt`) |
| `scripts/tuning_config.py` | **10 trials**, `max_parallel_jobs=2` (`tuning_job_name.txt`) |
| `scripts/analyze_results.py` | Ranking + `tuning_progress.png` / `hyperparameter_impact.png` |
| `scripts/deploy_best.py` | Best child job → **`ml.t2.medium`** realtime endpoint (**`endpoint_name.txt`**) |
| `notebooks/experiment_analysis.ipynb` | Optional follow-up plots using the same helpers |

Instructor shorthand: [**`solutions/lab3/LAB3_SOLUTION_REFERENCE.md`**](../../solutions/lab3/LAB3_SOLUTION_REFERENCE.md).

## Quick path

```bash
cd labs/lab3-tuning/infrastructure
cp terraform.tfvars.example terraform.tfvars   # set aws_account_id
terraform init && terraform apply -auto-approve
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw sagemaker_role_arn)
cd ../scripts
python baseline.py          # wait ~5 min
python tuning_config.py     # waits for HPO (~15–25 min typical)
python analyze_results.py
python deploy_best.py         # exposes endpoint charges — delete afterward
```

**Cleanup**

- **`sagemaker`** console: delete realtime endpoint (**`endpoint_name.txt`**) plus any stale endpoints  
- **`terraform destroy -auto-approve`** from `infrastructure/`
