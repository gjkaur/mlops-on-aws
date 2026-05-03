# Lab 5: SageMaker Pipelines (module 5)

**Region:** `us-east-1` · Intermediate · ~90 min

Minimal path:

1. `cd infrastructure` → copy `terraform.tfvars.example`, set **`aws_account_id`**, **`terraform apply`**
2. Export **`BUCKET_NAME`**, **`ROLE_ARN`**, **`EVENTBRIDGE_ROLE_ARN`** from outputs
3. `cd ../scripts`
4. `python pipeline_definition.py` — registers/updates pipeline; writes **`pipeline_name.txt`**
5. `python run_pipeline.py` — starts execution + polls (10–18+ min)
6. Optional: `python trigger_setup.py` — EventBridge rule on `s3://…/new-data/`
7. Cleanup: optional `python trigger_setup.py delete`, then **`terraform destroy`**

Details: **`LAB_OVERVIEW.md`**, **`INSTRUCTOR_LAB_GUIDE.md`** (facilitators), **`../../solutions/lab5/LAB5_SOLUTION_REFERENCE.md`**.
