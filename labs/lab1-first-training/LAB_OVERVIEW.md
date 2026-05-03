# Lab 1: First SageMaker Training Job

> **Before starting:** Finish [Lab 00 — participant guide](../../participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) so AWS CLI, access keys, and account ID are ready.

## What You Will Do

- Deploy pre-written infrastructure code
- Run your first SageMaker training job
- Train a Random Forest model on the diabetes dataset
- Understand model performance metrics

## Files in This Lab

| File | Purpose |
|------|---------|
| `infrastructure/` | Terraform code for S3 bucket and IAM role |
| `scripts/train.py` | Training script (runs inside SageMaker) |
| `scripts/run_training.py` | Launches SageMaker training job |

## Participant lab guide

**Full instructions:** [`participant/lab1-first-training/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab1-first-training/PARTICIPANT_LAB_GUIDE.md) — participant index [`participant/PARTICIPANT_DOCUMENTATION_INDEX.md`](../../participant/PARTICIPANT_DOCUMENTATION_INDEX.md), Lab 1 index [`participant/lab1-first-training/LAB1_PARTICIPANT_INDEX.md`](../../participant/lab1-first-training/LAB1_PARTICIPANT_INDEX.md).

## Step-by-Step Instructions (summary)

Follow the participant guide linked above—it covers clone paths, Terraform, training, metrics, cleanup, and troubleshooting.
