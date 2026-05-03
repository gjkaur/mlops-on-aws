variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project tag merged into resource tagging"
  type        = string
  default     = "lab9-advanced-inference"
}

variable "tags" {
  description = "Base tags merged with project_name"
  type        = map(string)
  default = {
    Environment = "training-lab"
    ManagedBy   = "Terraform"
    Lab         = "module-9"
  }
}
