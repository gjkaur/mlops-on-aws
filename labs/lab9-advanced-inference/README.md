# Lab 9 — Advanced Inference (code + Terraform)

Participant walkthrough: **[`participant/lab9-advanced-inference/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab9-advanced-inference/PARTICIPANT_LAB_GUIDE.md)** · Folder index **[`LAB9_PARTICIPANT_INDEX.md`](../../participant/lab9-advanced-inference/LAB9_PARTICIPANT_INDEX.md)**.

Serverless realtime, asynchronous queues, sklearn **multi-model** hosting, plus **Batch Transform** — exercised from curated scripts so you compare economics and behaviour without fighting packaging.

## Terraform (`infrastructure/`)

```bash
cd labs/lab9-advanced-inference/infrastructure
terraform init && terraform apply
```

Suggested exports (POSIX):

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw inference_role_arn)
```

PowerShell:

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw inference_role_arn
```

Outputs:

| Terraform output | Typical env export |
|-----------------|---------------------|
| `s3_bucket_name` | `BUCKET_NAME` |
| `inference_role_arn` | `ROLE_ARN` |

Destroy after class: **`python cleanup.py`** (in `scripts/`) then **`terraform destroy`**.

## Script order (`scripts/`)

Provisioning order matters only where endpoints contend for quotas; safest:

```bash
cd ../scripts
python train_models.py          # uploads models/*/model.tar.gz (+ model.joblib inside)
python deploy_serverless.py
python deploy_async.py
python deploy_mme.py
python run_batch_transform.py

python test_endpoints.py       # reads endpoint_name txt files (+ BUCKET_NAME for async)
python compare_costs.py
python cleanup.py
```

Overrides:

| Env var | Meaning |
|---------|---------|
| `MODEL_S3_URI` | Point deploy/batch helpers at alternate tarball URI |
| `LAB9_SERVERLESS_NAME` / `LAB9_ASYNC_NAME` / `LAB9_MME_NAME` | Pin deterministic endpoint names (default timestamped `lab9-*`) |

Inference contract: **CSV body** (`text/csv`) or **`{"features": [...]}`** JSON; **`10`** numeric inputs per row aligned with sklearn training.
