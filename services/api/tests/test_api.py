import json
import time
import importlib

import boto3
from fastapi.testclient import TestClient
from moto import mock_aws

def test_health_ok(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SQS_QUEUE_URL", "dummy")
    monkeypatch.setenv("SSM_TOKEN_PARAM_NAME", "/dummy")

    api = importlib.reload(importlib.import_module("app.main"))
    client = TestClient(api.app)

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

@mock_aws
def test_ingest_sends_message_to_sqs(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SSM_TOKEN_PARAM_NAME", "/email-ingest/token")

    # Create mocked AWS resources
    ssm = boto3.client("ssm", region_name="us-east-1")
    sqs = boto3.client("sqs", region_name="us-east-1")

    q = sqs.create_queue(QueueName="test-queue")
    monkeypatch.setenv("SQS_QUEUE_URL", q["QueueUrl"])

    # Put expected token into SSM
    ssm.put_parameter(
        Name="/email-ingest/token",
        Value="secret123",
        Type="SecureString",
    )

    # Import app AFTER env + moto are ready
    api = importlib.reload(importlib.import_module("app.main"))
    client = TestClient(api.app)

    payload = {
        "email_timestream": int(time.time()),
        "hello": "world",
    }

    r = client.post(
        "/ingest",
        json={"token": "secret123", "data": payload},
    )

    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    # Verify message was sent to SQS
    resp = sqs.receive_message(
        QueueUrl=q["QueueUrl"],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1,
    )

    msgs = resp.get("Messages", [])
    assert len(msgs) == 1
    assert json.loads(msgs[0]["Body"]) == payload

@mock_aws
def test_ingest_invalid_token_returns_401(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SSM_TOKEN_PARAM_NAME", "/email-ingest/token")

    ssm = boto3.client("ssm", region_name="us-east-1")
    sqs = boto3.client("sqs", region_name="us-east-1")

    q = sqs.create_queue(QueueName="test-queue")
    monkeypatch.setenv("SQS_QUEUE_URL", q["QueueUrl"])

    # Expected token in SSM
    ssm.put_parameter(
        Name="/email-ingest/token",
        Value="secret123",
        Type="SecureString",
    )

    api = importlib.reload(importlib.import_module("app.main"))
    client = TestClient(api.app)

    payload = {
        "email_timestream": int(time.time()),
        "hello": "world",
    }

    r = client.post("/ingest", json={"token": "WRONG", "data": payload})
    assert r.status_code == 401

@mock_aws
def test_ingest_missing_email_timestream_returns_400(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("SSM_TOKEN_PARAM_NAME", "/email-ingest/token")

    ssm = boto3.client("ssm", region_name="us-east-1")
    sqs = boto3.client("sqs", region_name="us-east-1")

    q = sqs.create_queue(QueueName="test-queue")
    monkeypatch.setenv("SQS_QUEUE_URL", q["QueueUrl"])

    # Expected token in SSM
    ssm.put_parameter(
        Name="/email-ingest/token",
        Value="secret123",
        Type="SecureString",
    )

    api = importlib.reload(importlib.import_module("app.main"))
    client = TestClient(api.app)

    payload = {
        "hello": "world",
    }  # missing email_timestream

    r = client.post("/ingest", json={"token": "secret123", "data": payload})
    assert r.status_code == 400
