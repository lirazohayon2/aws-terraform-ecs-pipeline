locals {
  name = var.project_name
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "random_password" "ingest_token" {
  length           = 24
  special          = true
  override_special = "!#$%&*+-.:=?@^_"
}

resource "aws_s3_bucket" "emails" {
  bucket = "${local.name}-emails-${random_id.suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "emails" {
  bucket                  = aws_s3_bucket.emails.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "emails" {
  bucket = aws_s3_bucket.emails.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "emails" {
  bucket = aws_s3_bucket.emails.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_sqs_queue" "emails" {
  name                       = "${local.name}-queue"
  visibility_timeout_seconds = 60
  receive_wait_time_seconds  = 20
}

resource "aws_ssm_parameter" "token" {
  name  = "/${local.name}/ingest-token"
  type  = "SecureString"
  value = random_password.ingest_token.result
}

resource "aws_ecr_repository" "api" {
  name                 = "${local.name}-api"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}

resource "aws_ecr_repository" "worker" {
  name                 = "${local.name}-worker"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true
}
