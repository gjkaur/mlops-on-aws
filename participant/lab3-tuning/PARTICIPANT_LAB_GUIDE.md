# Lab 3: Hyperparameter Tuning & Experiment Tracking

## Participant Lab Guide

**Duration:** 90 minutes  
**Difficulty:** Beginner  
**Module:** 3 - Experimentation  
**AWS Region:** `us-east-1`

---

## Lab Objective

In this lab you will use **SageMaker automatic model tuning** to search for better hyperparameters for a **sklearn RandomForest** on the Diabetes dataset. You will:

- Train a **baseline** model with default hyperparameters
- Define **search ranges** for four hyperparameters
- Launch a tuning job that runs **10 training jobs**, up to **two at a time**
- **Analyze** results (tables + plots) and compare to the baseline
- **Deploy** the best trial to a **real-time endpoint**

---

## What You Will Build

By the end of this lab, you will have:

- A baseline training job and metrics to compare against  
- A hyperparameter tuning job with **10 child training jobs**  
- PNG plots showing tuning progress and hyperparameter effects  
- The best model hosted on an endpoint (remember to **delete the endpoint** when done)

---

## Why Hyperparameter Tuning Matters

Default hyperparameters rarely give the best accuracy. **Manual** grid search burns time. **SageMaker** uses a **Bayesian-style** search plus **early stopping** (Hyperband): it learns from finished jobs and focuses on promising regions of the search space.

---

## AWS Services You Will Use

| Service | Purpose |
|---------|---------|
| **SageMaker Training** | Runs each training job inside a managed container |
| **SageMaker Hyperparameter Tuning** | Orchestrates many training jobs and picks a best objective |
| **SageMaker Hosting** | Real-time endpoint for the champion model |
| **S3** | Code and model artifacts |
| **CloudWatch** | Training logs (including metrics parsed for the tuner) |

Experiment-style views in **SageMaker Studio** may list these jobs; this lab is driven from **scripts** and the AWS console.

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop / class environment | ✅ |
| VS Code + cloned `mlops-on-aws` repo | ✅ |
| AWS CLI configured (**Lab 00**) | ✅ |
| `pip install -r requirements.txt` from **repo root** (includes `matplotlib`, `sagemaker`, `scikit-learn`) | ✅ |
| Lab 1 (optional) | Helpful context on SageMaker jobs |

---

## Shell note (bash vs PowerShell)

Commands use **bash**. On **Windows PowerShell**, use the **PowerShell** alternatives where shown, or **Git Bash**.

---

## Lab files overview

| File | Location | Purpose |
| --- | --- | --- |
| `infrastructure/` | `labs/lab3-tuning/infrastructure/` | S3 bucket + SageMaker execution role |
| `scripts/train.py` | `labs/lab3-tuning/scripts/` | Training entry (runs in SageMaker); prints `rmse:` / `r2:` for tuning |
| `scripts/predict.py` | `labs/lab3-tuning/scripts/` | Inference code used **only** when you deploy an endpoint |
| `scripts/baseline.py` | `labs/lab3-tuning/scripts/` | One job with default hyperparameters |
| `scripts/tuning_config.py` | `labs/lab3-tuning/scripts/` | Starts HPO (**10 jobs**, **2 parallel**) |
| `scripts/analyze_results.py` | `labs/lab3-tuning/scripts/` | Rank trials + write PNG plots |
| `scripts/deploy_best.py` | `labs/lab3-tuning/scripts/` | Deploy best trial to **`ml.t2.medium`** |

Abbreviated reference: [`labs/lab3-tuning/LAB_OVERVIEW.md`](../../labs/lab3-tuning/LAB_OVERVIEW.md).

---

## Hyperparameters we tune

CLI / tuner names use **hyphens** (SageMaker maps them to Python args). Conceptually:

| Concept | Default (baseline) | Search range |
| --- | --- | --- |
| Number of trees (`n-estimators`) | 100 | 50 – 200 |
| Max depth (`max-depth`) | 10 | 3 – 15 |
| Min samples to split (`min-samples-split`) | 2 | 2 – 20 |
| Min samples per leaf (`min-samples-leaf`) | 1 | 1 – 10 |

**Tuner objective:** minimize **RMSE** (parsed from training logs).

---

## Step-by-step instructions

### Step 1: Open the lab folder

1. In VS Code: **mlops-on-aws** → **labs** → **lab3-tuning**  
2. Right‑click **lab3-tuning** → **Open in Integrated Terminal**

---

### Step 2: Deploy the infrastructure

**2.1** Go to Terraform:

```bash
cd infrastructure
```

**2.2** Copy variables file  

Bash:

```bash
cp terraform.tfvars.example terraform.tfvars
```

PowerShell:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

**2.3** Edit **`terraform.tfvars`**

```bash
code terraform.tfvars
```

Set **`aws_account_id`** to your 12-digit account ID (Lab 00). Save.

**2.4** Apply

```bash
terraform init
terraform apply -auto-approve
```

**Expected:** `Apply complete!` with **8 resources** added (S3 bucket + IAM role + attachments, etc.).

**2.5** Export outputs (stay in **`infrastructure/`**)  

Bash:

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw sagemaker_role_arn)
```

PowerShell:

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw sagemaker_role_arn
```

---

### Step 3: Run baseline training

```bash
cd ../scripts
python baseline.py
```

**Typical runtime:** ~3–6 minutes.

The script writes **`baseline_job_name.txt`** next to the other scripts (same folder) and prints **Baseline Performance** metrics when CloudWatch aggregates them—if the list is empty at first, wait a few seconds and check the job in **SageMaker → Training**.

**Remember your baseline RMSE** for comparison after tuning.

---

### Step 4: Launch hyperparameter tuning

Still in **`scripts/`** with **`BUCKET_NAME`** and **`ROLE_ARN`** set:

```bash
python tuning_config.py
```

This:

- Builds the search ranges above  
- Runs **10** training jobs with **`max_parallel_jobs=2`** (two concurrent)  
- Waits until the **parent tuning job** finishes (**often ~15–25 minutes**)

When it exits, **`tuning_job_name.txt`** contains the tuning job name.

**Optional:** Console → **SageMaker** → **Training** → **Hyperparameter tuning jobs** → find a name like **`tuning-diabetes-...`**.

---

### Step 5: Monitor progress (optional)

In the AWS Console, open your tuning job and watch child training jobs move from **InProgress** to **Completed** (or early-stopped).

---

### Step 6: Analyze results

After tuning completes:

```bash
python analyze_results.py
```

This prints ranked trials, optionally compares **baseline RMSE** to the best tuned RMSE, and saves:

- **`tuning_progress.png`**
- **`hyperparameter_impact.png`**

in the **`scripts/`** folder (`ls *.png` or Explorer).

---

### Step 7: Deploy the best model

```bash
python deploy_best.py
```

Creates a real-time endpoint (name like **`tuning-best-<timestamp>`**, saved in **`endpoint_name.txt`** in **`scripts/`**). Hosting uses **`predict.py`**; training used **`train.py`** inside jobs.

Endpoints incur cost until deleted.

---

### Step 8: Clean up

**8.1 Delete the endpoint** (from **`scripts/`**, where **`endpoint_name.txt`** lives)

Bash:

```bash
aws sagemaker delete-endpoint --region us-east-1 --endpoint-name "$(cat endpoint_name.txt)"
```

PowerShell:

```powershell
$name = Get-Content endpoint_name.txt -Raw
$name = $name.Trim()
aws sagemaker delete-endpoint --region us-east-1 --endpoint-name $name
```

**8.2 Destroy Terraform**

```bash
cd ../infrastructure
terraform destroy -auto-approve
```

**Expected:** `Destroy complete!` with **8 resources** destroyed.

---

## Lab completion checklist

- [ ] Terraform apply succeeded  
- [ ] Baseline job finished  
- [ ] Tuning job finished (10 child jobs)  
- [ ] `analyze_results.py` ran and PNGs exist  
- [ ] `deploy_best.py` ran and prediction printed  
- [ ] Endpoint deleted  
- [ ] `terraform destroy` completed  

---

## Understanding results (illustrative)

Exact numbers vary by run. You should see **best tuned RMSE ≤ baseline RMSE** in most cases. Plots help you see which hyperparameters correlated with lower RMSE on this small search.

---

## Troubleshooting

| Issue | What to try |
| --- | --- |
| Tuning longer than ~30 min | Normal under load; confirm child jobs in console |
| `ResourceLimitExceeded` | Ask instructor; or lower instance type in **`baseline.py`** / **`tuning_config.py`** (e.g. `ml.m5.large` → `ml.t3.medium` if allowed) |
| `No module named 'matplotlib'` | `pip install -r requirements.txt` from repo root |
| `FinalMetricDataList` empty on baseline | Wait for metrics; ensure training logs contain lines like `rmse: 54.xxxx` |
| Deploy quota errors | Endpoint already uses **`ml.t2.medium`**; delete old endpoints |

---

## Key takeaways

| Idea | Takeaway |
| --- | --- |
| Baseline first | You need a reference before claiming tuning “wins.” |
| Search, not brute force | Bayesian / early stopping focuses budget on promising trials. |
| Metrics in logs | The tuner relies on **`metric_definitions`** aligned with **`train.py`** output. |
| Train vs serve | **`train.py`** trains; **`predict.py`** serves the packaged model. |
| Costs | Training + tuning + endpoints cost money — **always delete endpoints** and run **`terraform destroy`**. |

---

**Next:** Continue with your course schedule — see other lab folders under [`labs/`](../../labs/).
