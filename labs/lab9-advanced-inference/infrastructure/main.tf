locals {
  tags = merge(var.tags, { Project = var.project_name })
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "inference_bucket" {
  bucket        = "mlops-lab9-inference-${random_id.suffix.hex}"
  force_destroy = true
  tags          = local.tags
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.inference_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "block_public" {
  bucket                  = aws_s3_bucket.inference_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "inference_role" {
  name               = "MLOpsLab9InferenceRole-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
  tags               = local.tags
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.inference_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.inference_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  role       = aws_iam_role.inference_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

output "s3_bucket_name" {
  description = "S3 bucket for model artifacts and async / batch paths"
  value       = aws_s3_bucket.inference_bucket.id
}

output "inference_role_arn" {
  description = "Execution role ARN for SageMaker endpoints and batch transform"
  value       = aws_iam_role.inference_role.arn
}
