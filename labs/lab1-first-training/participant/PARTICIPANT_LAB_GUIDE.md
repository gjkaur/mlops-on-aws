# Lab 1: First SageMaker Training Job

## Participant Lab Guide

**Duration:** 45-60 minutes  
**Module:** 1 - Foundations  
**AWS Region:** `us-east-1`

---

## Lab Objective

In this lab, you will run your first SageMaker training job using the pre‑written code from the course repository. You will:

- Clone the course repository
- Deploy the required AWS infrastructure (S3 bucket, IAM role) using provided code
- Launch a SageMaker training job from your terminal
- Train a Random Forest model on the diabetes dataset
- Understand model performance metrics (MSE, RMSE, R²)
- Clean up all resources at the end

---

## What You Will Build

By the end of this lab, you will have:

- A trained Random Forest model saved in your own S3 bucket
- A complete record of the training job in SageMaker
- A clear understanding of how to run cloud‑based ML training

---

## AWS Services You Will Use

| AWS Service | What It Does | How It Helps in MLOps |
| --- | --- | --- |
| **AWS IAM** | Manages users, roles, and permissions | SageMaker assumes a role to access your S3 bucket |
| **Amazon S3** | Object storage | Stores training code, logs, and the trained model |
| **Amazon SageMaker** | Managed ML platform | Runs the training job on AWS compute |
| **Amazon CloudWatch** | Logging service | Captures training logs for debugging |

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop (provided by instructor) | ✅ |
| VS Code installed | ✅ |
| AWS IAM access key and secret key (from Lab 00) | ✅ |
| All tools pre‑installed (Python, AWS CLI, Terraform, Git) | ✅ |

> **You do NOT write any infrastructure or training code. All files are already provided in the repository.**

---

## Lab Files Overview

| File | Location | Purpose |
| --- | --- | --- |
| `infrastructure/main.tf` | `labs/lab1-first-training/infrastructure/` | Creates S3 bucket and IAM role |
| `scripts/train.py` | `labs/lab1-first-training/scripts/` | Training script (runs inside SageMaker) |
| `scripts/run_training.py` | `labs/lab1-first-training/scripts/` | Launches the SageMaker training job |

---

## Shell environments (Linux / macOS / Git Bash vs Windows PowerShell)

Most commands below use **bash** syntax. If your integrated terminal is **PowerShell**:

- Prefer **Git Bash** (bundled with Git for Windows) for the closest match, **or**
- Use the PowerShell equivalents shown inline where noted.

---

## Step-by-Step Instructions

### Step 1: Clone the Repository

**Tool:** VS Code

1. Open **Visual Studio Code**.

2. Click the **Source Control** icon in the left toolbar (third icon down – looks like a branching tree).

3. Click **Clone Repository**.

4. In the text box that appears, paste the repository URL:

   ```text
   https://github.com/gjkaur/mlops-on-aws.git
   ```

5. Press **Enter**.

6. When prompted to select a folder, choose:

   ```text
   C:\Users\tekstudent\mlops-labs
   ```

   > If the folder does not exist, click **New Folder** and name it `mlops-labs`.

7. Click **Select as Repository Destination**.

8. When prompted "Would you like to open the cloned repository?", click **Open**.

✅ **Repository cloned successfully.**

---

### Step 2: Open the Lab Folder

**Tool:** VS Code

1. In the **Explorer** sidebar (left side), you should see the `mlops-on-aws` folder.

2. Navigate to:

   ```
   mlops-on-aws → labs → lab1-first-training
   ```

3. Right‑click on the `lab1-first-training` folder and select **Open in Integrated Terminal**.

> A terminal opens already positioned inside the correct lab folder.

---

### Step 3: Review the Infrastructure Code (No Changes Needed)

**Tool:** VS Code file explorer

Take a quick look at the provided files – you will **not** change them:

- `infrastructure/main.tf` – defines the S3 bucket and IAM role
- `infrastructure/variables.tf` – defines inputs
- `infrastructure/providers.tf` – tells Terraform to use AWS

> All code is pre‑written and ready to use.

---

### Step 4: Set Up Your AWS Account ID

**Tool:** VS Code terminal (already open)

**4.1 Copy the example variables file**

```bash
cp infrastructure/terraform.tfvars.example infrastructure/terraform.tfvars
```

**PowerShell (from `lab1-first-training`):**

```powershell
Copy-Item infrastructure\terraform.tfvars.example infrastructure\terraform.tfvars
```

**4.2 Open the file for editing**

```bash
code infrastructure/terraform.tfvars
```

**4.3 Replace the placeholder with your actual AWS account ID**

Find the line:

```hcl
aws_account_id = "<your-account-id>"
```

Replace `<your-account-id>` with **your AWS account ID** (you saved this from Lab 00).

**Example:**

```hcl
aws_account_id = "123456789012"
```

Save the file (`Ctrl+S`) and close the editor tab.

---

### Step 5: Deploy the AWS Infrastructure

**Tool:** VS Code terminal

**5.1 Move into the infrastructure folder**

```bash
cd infrastructure
```

**5.2 Initialize Terraform**

```bash
terraform init
```

**Expected output:** `Terraform has been successfully initialized!`

**5.3 Preview the resources that will be created**

```bash
terraform plan
```

**5.4 Create the resources**

```bash
terraform apply -auto-approve
```

**Expected output:** `Apply complete! Resources: 8 added, 0 changed, 0 destroyed.`

**5.5 Save the outputs (used by the training script)**

Bash:

```bash
export BUCKET_NAME=$(terraform output -raw s3_bucket_name)
export ROLE_ARN=$(terraform output -raw sagemaker_role_arn)
```

**PowerShell** (run from `infrastructure/`):

```powershell
$env:BUCKET_NAME = terraform output -raw s3_bucket_name
$env:ROLE_ARN = terraform output -raw sagemaker_role_arn
```

---

### Step 6: Run the SageMaker Training Job

**Tool:** VS Code terminal

**6.1 Go back to the lab root folder**

```bash
cd ..
```

**6.2 Run the training script**

```bash
python scripts/run_training.py
```

**What happens now:**

1. SageMaker launches a training instance in the cloud
2. The `train.py` script is copied to that instance
3. A Random Forest model is trained on the diabetes dataset
4. The trained model is saved to your S3 bucket
5. The training instance automatically shuts down

⏱️ **This step takes 3–5 minutes.** Do not close the terminal.

**Expected output (final lines):**

```text
Training complete
Model artifact: s3://sagemaker-lab1-xxxxx/output/diabetes-training-xxxxx/output/model.tar.gz
Training job name: diabetes-training-xxxxx
```

---

### Step 7: Verify the Model Performance Metrics

**Tool:** VS Code terminal

Bash:

```bash
export JOB_NAME=$(cat training_job_name.txt)
aws sagemaker describe-training-job --region us-east-1 --training-job-name "$JOB_NAME" --query "FinalMetricDataList" --output json
```

**PowerShell:**

```powershell
$env:JOB_NAME = Get-Content training_job_name.txt -Raw
$env:JOB_NAME = $env:JOB_NAME.Trim()
aws sagemaker describe-training-job --region us-east-1 --training-job-name $env:JOB_NAME --query "FinalMetricDataList" --output json
```

**Expected output:**

```json
[
  {"MetricName": "rmse", "Value": 54.54},
  {"MetricName": "r2", "Value": 0.44}
]
```

**What these numbers mean:**

| Metric | Interpretation |
| --- | --- |
| **RMSE = 54.54** | On average, the model’s prediction is off by about 54 points |
| **R² = 0.44** | The model explains 44% of the variation in diabetes progression |

For a first model with default settings, this is a solid baseline.

---

### Step 8: Download the Trained Model (Optional)

**Tool:** VS Code terminal

Bash:

```bash
export MODEL_URI=$(aws sagemaker describe-training-job --region us-east-1 --training-job-name "$JOB_NAME" --query "ModelArtifacts.S3ModelArtifacts" --output text)
aws s3 cp "$MODEL_URI" ./model.tar.gz --region us-east-1
tar -xzf model.tar.gz
cat metrics.json
```

**PowerShell:**

```powershell
$MODEL_URI = aws sagemaker describe-training-job --region us-east-1 --training-job-name $env:JOB_NAME --query "ModelArtifacts.S3ModelArtifacts" --output text
aws s3 cp $MODEL_URI ./model.tar.gz --region us-east-1
tar -xzf model.tar.gz
Get-Content metrics.json
```

You will see the same metrics again, confirming the model was saved correctly.

---

### Step 9: Clean Up All AWS Resources

**Tool:** VS Code terminal

> ⚠️ **Always clean up** after finishing a lab to avoid unnecessary charges.

```bash
cd infrastructure
terraform destroy -auto-approve
```

**Expected output:** `Destroy complete! Resources: 8 destroyed.`

**Close the terminal** (right‑click in the terminal → **Kill Terminal**).

---

## ✅ Lab Completion Checklist

- [ ] Repository cloned successfully
- [ ] Infrastructure deployed with `terraform apply`
- [ ] Training job completed successfully
- [ ] You can explain what RMSE and R² mean
- [ ] `terraform destroy` completed
- [ ] All resources cleaned up

---

## 🚨 Troubleshooting

| Issue | Solution |
| --- | --- |
| `terraform: command not found` | **Notify instructor** (tools are pre‑installed on the VM) |
| `AccessDenied` on `terraform apply` | Your IAM user needs more permissions. Ask your instructor. |
| Training fails with `ResourceLimitExceeded` | In `scripts/run_training.py`, change `instance_type="ml.m5.large"` to `instance_type="ml.t2.medium"` |
| `ModuleNotFoundError` | A package is missing. Run: `pip install -r requirements.txt` from the repository root |

---

## 📚 Key Metrics Reference

| Metric | Formula | Interpretation | Goal |
| --- | --- | --- | --- |
| **MSE** | `(1/n) Σ(yᵢ - ŷᵢ)²` | Average squared error | Lower is better |
| **RMSE** | `√MSE` | Typical error in original units | Lower is better |
| **R²** | `1 - (SS_res / SS_tot)` | Proportion of variance explained | Higher is better (max 1.0) |

---

## 🎉 Congratulations!

You have completed Lab 1. You cloned the repo, deployed infrastructure as code, trained a model in SageMaker, and cleaned up—all core moves in hands‑on MLOps on AWS.
