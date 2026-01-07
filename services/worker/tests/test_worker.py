import json
import importlib

import boto3
import pytest
from moto import mock_aws


class StopWorker(Exception):
    pass


@mock_aws
def test_worker_reads_sqs_and_writes_to_s3(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("POLL_INTERVAL_SECONDS", "1")

    sqs = boto3.client("sqs", region_name="us-east-1")
    s3 = boto3.client("s3", region_name="us-east-1")

    q = sqs.create_queue(QueueName="test-queue")
    bucket = "test-bucket"
    s3.create_bucket(Bucket=bucket)

    monkeypatch.setenv("SQS_QUEUE_URL", q["QueueUrl"])
    monkeypatch.setenv("S3_BUCKET", bucket)

    worker = importlib.reload(importlib.import_module("app.worker"))

    worker.sqs = sqs
    worker.s3 = s3

    payload = {"email_timestream": 123, "hello": "world"}
    sqs.send_message(
        QueueUrl=q["QueueUrl"],
        MessageBody=json.dumps(payload),
    )

    def stop_sleep(_):
        raise StopWorker()

    monkeypatch.setattr(worker.time, "sleep", stop_sleep)

    with pytest.raises(StopWorker):
        worker.main()

    objects = s3.list_objects_v2(Bucket=bucket).get("Contents", [])
    assert len(objects) == 1

    key = objects[0]["Key"]
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode()
    assert json.loads(body) == payload

    resp = sqs.receive_message(
        QueueUrl=q["QueueUrl"],
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1,
    )
    assert resp.get("Messages") is None
