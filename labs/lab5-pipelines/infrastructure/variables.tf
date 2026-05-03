variable "aws_account_id" {
  description = "AWS account ID that owns SageMaker pipelines and S3 buckets (Lab 00)"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags applied to managed resources"
  type        = map(string)
  default = {
    Environment = "training-lab"
    Project     = "mlops-course"
    ManagedBy   = "Terraform"
    Lab         = "module-5"
  }
}
