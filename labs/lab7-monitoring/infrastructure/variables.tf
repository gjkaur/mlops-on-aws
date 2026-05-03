variable "aws_account_id" {
  description = "AWS account ID (Lab 00); optional for tagging or auditing artifacts"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alert_email" {
  description = "Email address subscribed to SNS drift alerts (must confirm subscription)"
  type        = string
}

variable "tags" {
  description = "Tags applied to managed resources"
  type        = map(string)
  default = {
    Environment = "training-lab"
    Project     = "mlops-course"
    ManagedBy   = "Terraform"
    Lab         = "module-7"
  }
}
