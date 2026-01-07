import json
import os
import time
from typing import Any, Dict

import boto3
from botocore.config import Config
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
SSM_TOKEN_PARAM_NAME = os.environ["SSM_TOKEN_PARAM_NAME"]

boto_cfg = Config(retries={"max_attempts": 10, "mode": "standard"})
ssm = boto3.client("ssm", region_name=AWS_REGION, config=boto_cfg)
sqs = boto3.client("sqs", region_name=AWS_REGION, config=boto_cfg)

app = FastAPI(title="email-ingest-api")


class RequestBody(BaseModel):
    data: Dict[str, Any] = Field(...)
    token: str = Field(..., min_length=1)


def get_expected_token() -> str:
    resp = ssm.get_parameter(Name=SSM_TOKEN_PARAM_NAME, WithDecryption=True)
    return resp["Parameter"]["Value"]


def validate_timestream(data: Dict[str, Any]) -> None:
    ts = data.get("email_timestream")
    if ts is None:
        raise HTTPException(status_code=400, detail="email_timestream is missing")

    try:
        ts_int = int(ts)
        if ts_int <= 0:
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="email_timestream must be a positive epoch integer")

    now = int(time.time())
    if ts_int > now + 300:
        raise HTTPException(status_code=400, detail="email_timestream is in the future")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(body: RequestBody):
    expected = get_expected_token()
    if body.token != expected:
        raise HTTPException(status_code=401, detail="invalid token")

    validate_timestream(body.data)

    msg_body = json.dumps(body.data, separators=(",", ":"), ensure_ascii=False)
    sqs.send_message(QueueUrl=SQS_QUEUE_URL, MessageBody=msg_body)

    return {"status": "accepted"}
