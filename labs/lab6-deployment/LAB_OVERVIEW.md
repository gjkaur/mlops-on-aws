# Lab 6: Model deployment & serving

Module **6 – Deployment** · **`us-east-1`** · about **90 minutes** · intermediate

## Goals

- Train a churn-style **sklearn RandomForest**, package **`model.joblib`** for inference  
- Deploy a **real-time endpoint** with **`SKLearnModel`** (**`CSVSerializer`** in, **`JSONDeserializer`** out)  
- Optionally attach **Application Auto Scaling** to the serving **variant** (invocation target tracking)  
- Explore **multi-variant routing** (**canary**) and **collapse** (“promote-green”) toward a single stable fleet  
- Test with **Predictor** + **`sagemaker-runtime`** and a small threaded load profile  
- Tear down reliably (**`cleanup.py`** + Terraform)

Prerequisites:

- [**Lab 00**](../../participant/lab0-environment-setup/PARTICIPANT_LAB_GUIDE.md) (AWS CLI)  
- Repo root **`pip install -r requirements.txt`**

## Participant walkthrough

- **[participant/lab6-deployment/PARTICIPANT_LAB_GUIDE.md](../../participant/lab6-deployment/PARTICIPANT_LAB_GUIDE.md)**  
- **[participant/lab6-deployment/LAB6_PARTICIPANT_INDEX.md](../../participant/lab6-deployment/LAB6_PARTICIPANT_INDEX.md)**  

## Repository layout (`labs/lab6-deployment/`)

| Path | Purpose |
|------|---------|
| `infrastructure/` | S3 + SageMaker execution role |
| `scripts/train.py` | Training container entry |
| `scripts/train_model.py` | Generates CSV → **`SKLearn`** job → **`model_data_uri.txt`** |
| `scripts/inference.py` | Inference handlers for realtime container |
| `scripts/deploy_endpoint.py` | Builds **`SKLearnModel`** endpoint (**`endpoint_name.txt`**) |
| `scripts/configure_scaling.py` | Registers auto-scaling target + policy (**`scalable_target_id.txt`**) |
| `scripts/canary_deployment.py` | **`apply`** (dual variant) **`promote-green`** (collapse) |
| `scripts/test_endpoint.py` | Predictor / boto runtime / load spike |
| `scripts/cleanup.py` | Drops scaling hooks, endpoint, configs, **`lab6-*`** models + local state |
| `notebooks/endpoint_analysis.ipynb` | Quick **`describe_endpoint`** |

## Canonical script order

1. Terraform **`apply`**  
2. **`python train_model.py`**  
3. **`python deploy_endpoint.py`** (**t2.medium realtime fleet**)  
4. **`python configure_scaling.py`** (optional, **Application Auto Scaling** SLR prerequisites may apply)  
5. **`python test_endpoint.py`**  
6. Optional **`python canary_deployment.py apply --blue-weight 90 --green-weight 10`** (**`GREEN_MODEL_DATA_URI`** for true A/B)  
7. Optional **`python canary_deployment.py promote-green`**  
8. **`python cleanup.py`**, then **`terraform destroy`**

Terraform **does not** delete SageMaker **models/endpoints/configs** you created outside refreshed state—the **`cleanup.py`** script clears the cloud objects this lab spins up.

Facilitators: **`INSTRUCTOR_LAB_GUIDE.md`** · condensed tips: **`../../solutions/lab6/LAB6_SOLUTION_REFERENCE.md`**.
