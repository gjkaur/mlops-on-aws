variable "aws_account_id" {
  description = "Your AWS Account ID"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "training-lab"
    Project     = "mlops-course"
    ManagedBy   = "Terraform"
    Lab         = "module-3"
  }
}
