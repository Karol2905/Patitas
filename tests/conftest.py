import sys

import boto3
import pytest
from moto import mock_aws

NOMBRE_TABLA = "citas-test"


@pytest.fixture
def tabla(monkeypatch):
    monkeypatch.setenv("TABLE_NAME", NOMBRE_TABLA)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    for modulo in ("repositorio", "handler"):
        sys.modules.pop(modulo, None)

    with mock_aws():
        tabla_creada = boto3.resource("dynamodb").create_table(
            TableName=NOMBRE_TABLA,
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield tabla_creada
