# Lab 6 — Model deployment & serving

**Region:** `us-east-1` · Intermediate · ~90 min

Minimal path:

1. `labs/lab6-deployment/infrastructure` → **`terraform.tfvars`** from example → **`terraform apply`**  
2. Export **`BUCKET_NAME`**, **`ROLE_ARN`**  
3. `labs/lab6-deployment/scripts`: **`train_model.py`** → **`deploy_endpoint.py`** → **`configure_scaling.py`** → **`test_endpoint.py`**  
4. Optional **`canary_deployment.py apply`** then **`canary_deployment.py promote-green`**  
5. **`cleanup.py`** then **`terraform destroy`**

Technical intro: **`LAB_OVERVIEW.md`** · facilitation: **`INSTRUCTOR_LAB_GUIDE.md`** · cheatsheet: **`../../solutions/lab6/LAB6_SOLUTION_REFERENCE.md`**.
