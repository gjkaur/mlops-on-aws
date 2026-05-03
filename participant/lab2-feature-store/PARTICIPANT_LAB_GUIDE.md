# Lab 2: Feature Store Pipeline

## Participant Lab Guide

**Duration:** 90 minutes  
**Difficulty:** Beginner  
**Module:** 2 - Data Management  
**AWS Region:** `us-east-1`

---

## Lab Objective

In this lab, you will learn how to use SageMaker Feature Store to manage ML features. You will:

- Create Feature Groups (online + offline stores)
- Ingest batch data into Feature Store
- Retrieve features for real-time inference
- Query the offline store using SQL (Athena)
- Build a training dataset from feature store data

---

## What You Will Build

By the end of this lab, you will have:

- Customer and order feature groups in SageMaker Feature Store
- Ingested sample data into both online and offline stores
- Retrieved features for real-time predictions
- Queried historical features using Athena
- Trained a churn prediction model using features from the store

---

## Why Feature Store Matters

**The problem:** In traditional ML, features are recreated for each model, leading to inconsistency between training and inference.

**The solution:** Feature Store centralizes feature definitions so the same features are used for both training and real-time predictions.

```
Without Feature Store           With Feature Store
─────────────────────           ─────────────────
Training: Feature A = 0.5       Training: Feature A = 0.5
Inference: Feature A = 0.48     Inference: Feature A = 0.5
    (different calculation!)         (same pipeline!)
         ↓                                   ↓
    Skew risk                          Consistency
```

---

## AWS Services You Will Use

| Service | Purpose |
|---------|---------|
| **SageMaker Feature Store** | Central repository for ML features |
| **Online store (DynamoDB)** | Fast lookups for real-time inference |
| **Offline store (S3 + Glue)** | Historical data for training |
| **Athena** | SQL queries on offline store |

Your **AWS CLI identity** (configured in Lab 00) must allow **Athena**, **Glue**, and **S3** access to the lab bucket and query results—your instructor configures this for the class account.

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop access | ✅ |
| VS Code with cloned `mlops-on-aws` repo | ✅ (same repo as Lab 1) |
| AWS CLI configured | ✅ (Lab 00) |
| Account ID available | ✅ (Lab 00) |
| Lab 1 completed | Optional but recommended |

> Run `pip install -r requirements.txt` from the **repository root** if you have not already (`sagemaker`, `boto3`, `pandas`, `scikit-learn`, etc.).

---

## Shell note (bash vs PowerShell)

Commands below use **bash** syntax. On **Windows PowerShell**, use the alternatives shown where noted, or use **Git Bash**.

---

## Lab Files Overview

| File | Location | Purpose |
| --- | --- | --- |
| `infrastructure/` | `labs/lab2-feature-store/infrastructure/` | S3 bucket, IAM role, Glue catalog DB |
| `scripts/create_features.py` | `labs/lab2-feature-store/scripts/` | Creates Feature Groups |
| `scripts/ingest_data.py` | `labs/lab2-feature-store/scripts/` | Ingests sample data |
| `scripts/retrieve_features.py` | `labs/lab2-feature-store/scripts/` | Retrieves features from online store |
| `scripts/query_offline.py` | `labs/lab2-feature-store/scripts/` | Queries offline store with Athena |
| `scripts/train_model.py` | `labs/lab2-feature-store/scripts/` | Trains a model using features |

Shortcut lab summary (no step-by-step): [`labs/lab2-feature-store/LAB_OVERVIEW.md`](../../labs/lab2-feature-store/LAB_OVERVIEW.md).

---

## Step-by-Step Instructions

### Step 1: Open the Lab Folder

**Tool:** VS Code

1. Navigate to:

   ```
   mlops-on-aws → labs → lab2-feature-store
   ```

2. Right‑click **`lab2-feature-store`** → **Open in Integrated Terminal**.

---

### Step 2: Deploy the Infrastructure

**Tool:** VS Code terminal

**2.1 Go to the infrastructure folder**

```bash
cd infrastructure
```

**2.2 Copy the variables file**

```bash
cp terraform.tfvars.example terraform.tfvars
```

PowerShell:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

**2.3 Edit the variables file**

```bash
code terraform.tfvars
```

Replace `<your-account-id>` with your AWS account ID (from Lab 00). Save (`Ctrl+S`).

**2.4 Initialize and apply Terraform**

```bash
terraform init
terraform apply -auto-approve
```

**Expected:** `Apply complete!` with **about 10 resources** added (S3, IAM role and policy attachments, Glue database, etc.—exact count may vary slightly with provider versions).

**2.5 Export outputs for the scripts**

From **`infrastructure/`** (bash):

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw feature_store_role_arn)
```

PowerShell:

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw feature_store_role_arn
```

> **Created:** An S3 bucket for offline/athena artifacts, an IAM execution role for Feature Store, and a Glue database **`sagemaker_featurestore`** for Athena queries.

---

### Step 3: Create Feature Groups

**Tool:** VS Code terminal

**3.1 Move to scripts**

```bash
cd ../scripts
```

Ensure **`BUCKET_NAME`** and **`ROLE_ARN`** are still set (same terminal session).

**3.2 Create the Feature Groups**

```bash
python create_features.py
```

**What this does:**

- Creates a **customer** feature group (`customer-features-<unique>-<timestamp>`)
- Creates an **order** feature group (`order-features-<unique>-<timestamp>`)
- Each includes an **online** and **offline** store

Names are printed in the logs and saved as **`customer_fg_name.txt`** and **`order_fg_name.txt`** for later scripts.

**Example output:**

```text
✓ Customer Feature Group created: customer-features-a1b2c3d4-1734567890
✓ Order Feature Group created: order-features-e5f60718-1734567910
✓ Feature group is ready!
```

> **Wait:** Allow **1–2 minutes** per feature group if status shows Creating.

---

### Step 4: Ingest Data into Feature Store

**Tool:** VS Code terminal

```bash
python ingest_data.py
```

**Expected shape:**

```text
Ingesting 5 records into customer-features-...
✓ Ingestion complete ...
Ingesting 7 records into order-features-...
✓ Ingestion complete ...
```

Same rows are synced toward **offline** cataloging; Athena may lag **1–2 minutes**.

---

### Step 5: Retrieve Features from Online Store

**Tool:** VS Code terminal

```bash
python retrieve_features.py
```

You should see a **single-record** lookup for customer **101** and a **batch** lookup for customers **101, 103, 105** with ages printed.

---

### Step 6: Query Offline Store with SQL

**Tool:** VS Code terminal

```bash
python query_offline.py
```

If the first query returns empty, wait **1–2 minutes** and rerun. Confirm Glue table names match your Feature Group naming if problems persist ([`LAB_OVERVIEW.md`](../../labs/lab2-feature-store/LAB_OVERVIEW.md) hints).

---

### Step 7: Train a Model Using Features from Feature Store

**Tool:** VS Code terminal

```bash
python train_model.py
```

This pulls customer rows via **Athena**, builds a **demo churn** label for illustration, trains a Random Forest, and prints metrics (exact numbers vary with the random synthetic labels).

---

### Step 8: Clean Up Resources

**Tool:** VS Code terminal

> **Always tear down** the lab infra when finished.

```bash
cd ../infrastructure
terraform destroy -auto-approve
```

> **Important:** SageMaker Feature Groups are **not** deleted by Terraform. After destroy, optionally delete the two feature groups in the **SageMaker console → Feature Store** if your instructor asks you to fully clean up AWS objects.

---

## Lab Completion Checklist

- [ ] Infrastructure deployed (`terraform apply`)
- [ ] Feature groups created (`create_features.py`)
- [ ] Data ingested (`ingest_data.py`)
- [ ] Online retrieval works (`retrieve_features.py`)
- [ ] Athena queries ran (`query_offline.py`)
- [ ] Training script ran (`train_model.py`)
- [ ] Infrastructure destroyed (`terraform destroy`)

---

## Troubleshooting

| Issue | Solution |
| --- | --- |
| Feature group stuck in Creating | Wait **2–3 minutes**; retry or recreate with instructor guidance |
| Athena returns no rows | Wait **1–2 minutes** post-ingestion; verify Glue tables under **`sagemaker_featurestore`** |
| AccessDenied Feature Store APIs | Sandbox IAM permissions—ask instructor |
| AccessDenied Athena / Glue | Your **CLI user** needs Athena + Glue + S3 on the bucket and `athena-results/` prefix |
| `No module named 'sagemaker'` | From repo root: `pip install -r requirements.txt` |

---

## Key Concepts Recap

| Concept | Online store | Offline store |
| --- | --- | --- |
| **Purpose** | Real-time inference | Training & analytics |
| **Speed** | Milliseconds | Seconds to minutes |
| **Data** | Low-latency latest rows | Historical / batch oriented |
| **Access** | `get_record` / `batch_get_record` | Athena SQL |

---

## Next Step

When you finish Lab 2, continue with the next module in your course syllabus (e.g., Lab 3 overview under [`labs/`](../)).

---

**Congratulations—you used Feature Store for ingest, online read, Athena, and training.**
