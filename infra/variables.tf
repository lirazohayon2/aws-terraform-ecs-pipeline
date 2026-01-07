variable "aws_region" {
  type        = string
  description = "AWS region to deploy to."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Prefix for naming AWS resources."
  default     = "devops-project"
}

variable "image_tag" {
  type        = string
  description = "Docker image tag to deploy."
  default     = "manual"

  validation {
    condition     = length(var.image_tag) >= 3
    error_message = "image_tag must be at least 3 characters."
  }
}

variable "github_repo" {
  type        = string
  description = "GitHub repo in the format owner/repo."
  default     = "lirazohayon2/aws-terraform-ecs-pipeline"
}

