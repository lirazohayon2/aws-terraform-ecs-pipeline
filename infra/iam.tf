data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.project_name}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role_policy_attachment" "task_execution_managed" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task_api" {
  name               = "${var.project_name}-task-api"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

resource "aws_iam_role" "task_worker" {
  name               = "${var.project_name}-task-worker"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
}

data "aws_iam_policy_document" "api_policy" {
  statement {
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.token.arn]
  }

  statement {
    actions   = ["kms:Decrypt"]
    resources = ["*"]
  }

  statement {
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.emails.arn]
  }
}

resource "aws_iam_role_policy" "api_inline" {
  name   = "${var.project_name}-api-inline"
  role   = aws_iam_role.task_api.id
  policy = data.aws_iam_policy_document.api_policy.json
}

data "aws_iam_policy_document" "worker_policy" {
  statement {
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = [aws_sqs_queue.emails.arn]
  }

  statement {
    actions = ["s3:PutObject"]
    resources = [
      "${aws_s3_bucket.emails.arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "worker_inline" {
  name   = "${var.project_name}-worker-inline"
  role   = aws_iam_role.task_worker.id
  policy = data.aws_iam_policy_document.worker_policy.json
}
