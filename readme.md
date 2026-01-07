# AWS Terraform ECS Pipeline

This project demonstrates a complete DevOps workflow for deploying and validating a containerized, event-driven application on AWS using Terraform and GitHub Actions.

The system is composed of two microservices (API + Worker), integrated via AWS-managed services, and validated using automated integration tests.

---

## Overview

The application consists of two containerized services:

1. **API Service**
   - Exposes an HTTP endpoint.
   - Validates an authentication token stored in AWS SSM Parameter Store.
   - Validates request payloads.
   - Publishes valid messages to an Amazon SQS queue.

2. **Worker Service**
   - Polls messages from the SQS queue.
   - Persists each message as a JSON object in Amazon S3.
   - Deletes the message from SQS only after successful upload.

The entire infrastructure is provisioned using Terraform, and the CI/CD pipeline is implemented using GitHub Actions.

---

## Architecture Flow

1. Client sends a request to the API service.
2. API retrieves and validates a token from AWS SSM (SecureString).
3. API validates the request payload and publishes it to SQS.
4. Worker service consumes messages from SQS.
5. Worker writes the message to S3.
6. Worker deletes the message from the queue upon success.

---

## Project Structure

```
.
├── infra/                      # Terraform infrastructure (ECS, IAM, ALB, SQS, S3, etc.)
├── services/
│   ├── api/
│   │   ├── app/                # FastAPI application code
│   │   ├── tests/              # API integration tests (mocked AWS)
│   │   ├── Dockerfile
│   │   └── requirements-dev.txt
│   └── worker/
│       ├── app/                # Worker application code
│       ├── tests/              # Worker integration tests (mocked AWS)
│       ├── Dockerfile
│       └── requirements-dev.txt
├── .github/workflows/           # CI/CD pipelines
├── .gitignore
└── README.md
```

---

## Prerequisites

- Python 3.12+
- Docker
- Git
- AWS CLI (only required for real AWS deployment)

---

## Running Tests Locally

Integration tests are implemented using **pytest** and **moto** to mock AWS services.  
No real AWS credentials are required to run the tests.

### API Tests

```bash
cd services/api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirements.txt -r requirements-dev.txt
pytest -q
```

### Worker Tests

```bash
cd services/worker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirements.txt -r requirements-dev.txt
pytest -q
```

The tests validate:
- Token retrieval from SSM
- Message publishing to SQS
- Message consumption from SQS
- Object persistence in S3
- Proper deletion of processed messages

---

## CI Pipeline

The CI pipeline is implemented using GitHub Actions and includes:

1. Running integration tests for the API service
2. Running integration tests for the Worker service
3. Building Docker images for both services
4. Pushing images to Amazon ECR

Image builds are gated by successful test execution.

---

## CD Pipeline

The CD pipeline is triggered after a successful CI run and performs the following steps:

1. Updates ECS task definitions with the newly built image tag
2. Deploys updated task definitions to the API and Worker services
3. Waits for ECS services to become stable
4. Runs a smoke test against the API `/health` endpoint via the ALB

---

## Infrastructure

Infrastructure is provisioned using Terraform and includes:

- ECS Cluster and Services (Fargate)
- Application Load Balancer
- IAM roles and policies
- Amazon SQS queue
- Amazon S3 bucket
- AWS SSM Parameter Store (SecureString)
- CloudWatch log groups

Terraform configuration is located under the `infra/` directory.

---

## End-to-End Validation (AWS)

After deployment, the system can be validated end-to-end in AWS:

```bash
# Verify service health
curl -i http://<alb-dns>/health

# Send ingest request
curl -i -X POST http://<alb-dns>/ingest \
  -H "Content-Type: application/json" \
  -d '{"token":"<token>","data":{"email_timestream":<epoch>,"hello":"world"}}'

# Verify object in S3
aws s3 ls s3://<bucket-name>/emails/ --recursive | tail
```

A JSON object is created under:

```
s3://<bucket-name>/emails/YYYY/MM/DD/<message-id>.json
```

This confirms that the full API → SQS → Worker → S3 flow is working.
