variable "aws_account_id" {
  description = "AWS account ID (Lab 00); optional for your notes — not referenced by IAM in this bundle"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alert_email" {
  description = "SNS drift-alert subscription email (confirm in inbox)"
  type        = string
}

variable "project_name" {
  description = "Project tag merged into resource tagging"
  type        = string
  default     = "mlops-capstone"
}

variable "tags" {
  description = "Base tags merged with project_name"
  type        = map(string)
  default = {
    Environment = "training-lab"
    ManagedBy   = "Terraform"
    Lab         = "module-8"
  }
}
