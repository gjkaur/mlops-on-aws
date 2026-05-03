# Lab 9: Advanced Inference Patterns

Short hands-on sprint across SageMaker inference styles that share **one sklearn model family** trained locally and packaged as **`model.joblib`** inside **`model.tar.gz`**.

## What learners practice

| Pattern | Insight |
|---------|---------|
| Serverless Inference | Idle scale-down; unpredictable first-byte latency |
| Asynchronous Inference | `InputLocation` on S3, large/long jobs off the synchronous path |
| Multi-Model Endpoints | One realtime host loads many artefacts — `TargetModel` routing |
| Batch Transform | Offline scoring over whole prefixes |

Infrastructure: **IAM role + bucket** (`labs/lab9-advanced-inference/infrastructure`).

Teaching docs: **`INSTRUCTOR_LAB_GUIDE.md`**, cheatsheet **`solutions/lab9/LAB9_SOLUTION_REFERENCE.md`**.

## Quick links

| Resource | Location |
|---------|----------|
| Lab code + README | [`README.md`](README.md) |
| Participant guide | [`participant/lab9-advanced-inference/PARTICIPANT_LAB_GUIDE.md`](../../participant/lab9-advanced-inference/PARTICIPANT_LAB_GUIDE.md) |
| Instructor notes | [`INSTRUCTOR_LAB_GUIDE.md`](INSTRUCTOR_LAB_GUIDE.md) |

**Region:** `us-east-1` (consistent with Terraform + scripts defaults).
