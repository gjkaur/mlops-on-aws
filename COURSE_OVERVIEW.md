# MLOps on AWS – Course Labs

This repository contains all code and infrastructure definitions for the Practical MLOps on AWS course.

**Public clone URL:** https://github.com/gjkaur/mlops-on-aws.git

## Repository Structure

| Folder | Purpose |
|--------|---------|
| `participant/` | Participant-facing lab walkthroughs (Markdown guides) |
| `labs/` | Lab-specific code and infrastructure |
| `shared/` | Reusable modules and utilities |
| `solutions/` | Completed solutions (instructors only) |

## Prerequisites

- **[Lab 00](participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) completed** — AWS CLI configured and account ID noted (provided desktop environment)
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

Each lab folder typically contains:

- `infrastructure/` – Terraform code for AWS resources  
- `scripts/` – Python scripts for training, deployment, monitoring  
- **`LAB_OVERVIEW.md`** – Short lab summary and links  

Participant walkthroughs: start at [`participant/PARTICIPANT_DOCUMENTATION_INDEX.md`](participant/PARTICIPANT_DOCUMENTATION_INDEX.md) (these live at repo root—not inside each lab folder).

Complete **[Lab 00 — participant guide](participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md)** first so your AWS CLI and account ID are ready.

Then open [**Lab 0 overview**](labs/lab0-environment-setup/LAB_OVERVIEW.md), [**Lab 1 overview**](labs/lab1-first-training/LAB_OVERVIEW.md) with [**Lab 1 participant guide**](participant/lab1-first-training/PARTICIPANT_LAB_GUIDE.md), and [**Lab 2 overview**](labs/lab2-feature-store/LAB_OVERVIEW.md) with [**Lab 2 participant guide**](participant/lab2-feature-store/PARTICIPANT_LAB_GUIDE.md).

Instructor scaffolding steps (repo layout, file templates): [`INSTRUCTOR_SETUP_GUIDE.md`](INSTRUCTOR_SETUP_GUIDE.md).
