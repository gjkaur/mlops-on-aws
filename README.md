# mlops-on-aws

Course materials for **Practical MLOps on AWS** — labs, Terraform infrastructure, SageMaker workflows, shared utilities, and instructor notes.

## Automated repository setup

The following commands were executed to create this repo and publish it to GitHub (the intended first line `# mlops-on-aws` is the title above; README content was authored in full rather than appended via `echo`):

```bash
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/gjkaur/mlops-on-aws.git
git push -u origin main
```

**Remote:** https://github.com/gjkaur/mlops-on-aws.git  
**Default branch:** `main`

To clone locally after the first push:

```bash
git clone https://github.com/gjkaur/mlops-on-aws.git
cd mlops-on-aws
```

---

## Repository structure (from course setup guide)

```
mlops-on-aws/
├── README.md
├── requirements.txt
├── labs/
│   ├── lab1-first-training/
│   ├── lab2-feature-store/
│   ├── lab3-tuning/
│   ├── lab4-registry/
│   ├── lab5-pipelines/
│   ├── lab6-deployment/
│   ├── lab7-monitoring/
│   ├── lab8-capstone/
│   ├── lab9-advanced-inference/
│   └── lab10-enterprise/
├── shared/
│   ├── modules/
│   └── utils/
└── solutions/
```

| Area | Purpose |
|------|---------|
| `labs/` | Lab-specific code and infrastructure |
| `shared/` | Reusable Terraform modules and Python utilities |
| `solutions/` | Completed solutions (instructors) |

---

## Prerequisites

- Python 3.10+
- AWS CLI configured
- Terraform 1.7+
- VS Code (recommended)

---

## Quick start

```bash
git clone https://github.com/gjkaur/mlops-on-aws.git
cd mlops-on-aws

python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```

Start with Lab 1: `labs/lab1-first-training/README.md` once that folder exists in the repo.

---

## Planned root files

- **README.md** — this file  
- **requirements.txt** — e.g. `boto3`, `sagemaker`, `pandas`, `numpy`, `scikit-learn`, `joblib`, `matplotlib`, `seaborn`, `pyyaml`

---

## Instructor setup milestones (reference)

| Step | Description |
|------|-------------|
| 1 | Repository root: README + requirements |
| 2 | Lab 1: SageMaker training (Terraform + `train.py` + `run_training.py`) |
| 3 | Shared utilities (e.g. `shared/utils/aws_helpers.py`) |
| 4 | `solutions/` for instructor reference |
| 5 | Optional script to build a participant copy (no `solutions/`) |

---

## Lab navigation

Each lab typically includes:

- `infrastructure/` — Terraform for AWS resources  
- `scripts/` — training, deployment, monitoring scripts  
- `README.md` — lab instructions  

For full step-by-step file templates and Terraform/Python snippets, see the instructor setup document `step1.md` in the course materials.
