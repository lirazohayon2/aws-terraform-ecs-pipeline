import json
import os
import time
from datetime import datetime, timezone

import boto3
from botocore.config import Config

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
S3_BUCKET = os.environ["S3_BUCKET"]
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "1"))

boto_cfg = Config(retries={"max_attempts": 10, "mode": "standard"})
sqs = boto3.client("sqs", region_name=AWS_REGION, config=boto_cfg)
s3 = boto3.client("s3", region_name=AWS_REGION, config=boto_cfg)


def build_s3_key(message_id: str) -> str:
    now = datetime.now(timezone.utc)
    return f"emails/{now:%Y/%m/%d}/{message_id}.json"


def main() -> None:
    while True:
        resp = sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )

        messages = resp.get("Messages", [])
        if not messages:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        for m in messages:
            receipt = m["ReceiptHandle"]
            message_id = m["MessageId"]
            body = m["Body"]

            try:
                payload = json.loads(body)
            except Exception:
                # Bad message (not JSON) – delete it so it won't keep returning forever
                sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)
                continue

            key = build_s3_key(message_id)
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=key,
                Body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                ContentType="application/json",
            )
            sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt)


if __name__ == "__main__":
    main()
