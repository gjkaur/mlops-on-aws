# Lab 1 Solution (Instructor Reference)

## Expected Outputs

### Terraform Apply
```
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.

Outputs:

s3_bucket_name = "sagemaker-lab1-a1b2c3d4"
sagemaker_role_arn = "arn:aws:iam::123456789012:role/SageMakerExecutionRole-a1b2c3d4"
sagemaker_role_name = "SageMakerExecutionRole-a1b2c3d4"
```

### Training Job Metrics
```json
[
  {"MetricName": "rmse", "Value": 54.54},
  {"MetricName": "r2", "Value": 0.44}
]
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| ResourceLimitExceeded | Change instance_type to `ml.t2.medium` in run_training.py |
| AccessDenied | Verify IAM role has required permissions |
| Bucket already exists | Terraform uses random suffix; shouldn't happen |
