output "s3_bucket_name" {
  value = aws_s3_bucket.emails.bucket
}

output "sqs_queue_url" {
  value = aws_sqs_queue.emails.url
}

output "ssm_token_param_name" {
  value = aws_ssm_parameter.token.name
}

output "ecr_api_repo_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_worker_repo_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "alb_dns_name" {
  value = aws_lb.app.dns_name
}
