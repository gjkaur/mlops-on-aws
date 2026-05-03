variable "aws_account_id" {
  description = "AWS account ID (Lab 00); reserved for tagging / auditing"
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
    Lab         = "module-6"
  }
}
