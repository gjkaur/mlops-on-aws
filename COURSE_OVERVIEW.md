# MLOps on AWS – Course Labs

This repository contains all code and infrastructure definitions for the Practical MLOps on AWS course.

**Public clone URL:** https://github.com/gjkaur/mlops-on-aws.git

## Repository Structure

| Folder | Purpose |
|--------|---------|
| `labs/` | Lab-specific code and infrastructure |
| `shared/` | Reusable modules and utilities |
| `solutions/` | Completed solutions (instructors only) |

## Prerequisites

- Python 3.10+
- AWS CLI configured
- Terraform 1.7+
- VS Code (recommended)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/gjkaur/mlops-on-aws.git
cd mlops-on-aws

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Lab Navigation

Each lab folder contains:

- `infrastructure/` – Terraform code for AWS resources
- `scripts/` – Python scripts for training, deployment, monitoring
- `README.md` – Lab index  
- `participant/` – Participant lab guides (Lab 1: full walkthrough)

Start with [Lab 1](labs/lab1-first-training/README.md). The participant walkthrough is [**Lab 1 — participant guide**](labs/lab1-first-training/participant/PARTICIPANT_LAB_GUIDE.md).

Instructor scaffolding steps (repo layout, file templates): [`INSTRUCTOR_SETUP_GUIDE.md`](INSTRUCTOR_SETUP_GUIDE.md).
