"""Fixtures compartidos por todas las pruebas.

pytest carga este archivo solo: cualquier prueba que reciba un parámetro
llamado ``tabla`` recibe la tabla falsa de DynamoDB creada aquí.
"""

import sys

import boto3
import pytest
from moto import mock_aws

NOMBRE_TABLA = "citas-test"


@pytest.fixture
def tabla(monkeypatch):
    """Tabla de citas en un DynamoDB falso (moto), vacía en cada prueba."""
    # 1. Variables de entorno: el código lee TABLE_NAME, y boto3 necesita
    #    región y credenciales (falsas: nunca se conecta a AWS de verdad).
    monkeypatch.setenv("TABLE_NAME", NOMBRE_TABLA)
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.delenv("AWS_PROFILE", raising=False)

    # repositorio.py crea la conexión a la tabla al importarse. Si otra
    # prueba ya lo importó, Python lo tiene guardado con la tabla de ese
    # mock. Lo borramos para que la prueba lo importe de nuevo dentro de este.
    for modulo in ("repositorio", "handler"):
        sys.modules.pop(modulo, None)

    # 2. Mientras dure el "with", boto3 habla con moto y no con AWS.
    with mock_aws():
        # 3. Crear la tabla: llave pk de tipo texto (S), pago por uso.
        tabla_creada = boto3.resource("dynamodb").create_table(
            TableName=NOMBRE_TABLA,
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        # 4. Entregar la tabla a la prueba. Al terminar, se sale del "with"
        #    y moto borra todo.
        yield tabla_creada
