import os
from datetime import datetime, timezone

import boto3

tabla = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


class CitaNoEncontrada(Exception):
    pass


def _todas_las_citas():
    pagina = tabla.scan()
    citas = pagina["Items"]
    while "LastEvaluatedKey" in pagina:
        pagina = tabla.scan(ExclusiveStartKey=pagina["LastEvaluatedKey"])
        citas.extend(pagina["Items"])
    return citas


def listar(fecha=None):
    citas = _todas_las_citas()
    if fecha:
        citas = [c for c in citas if c.get("fecha") == fecha]
    return sorted(citas, key=lambda c: (c.get("fecha", ""), c.get("hora", "")))


def cancelar(id_cita):
    cita = next((c for c in _todas_las_citas() if c.get("id") == id_cita), None)
    if cita is None:
        raise CitaNoEncontrada(id_cita)
    if cita.get("estado") == "CANCELADA":
        return

    archivada = {
        **cita,
        "pk": f"CANCELADA#{id_cita}",
        "estado": "CANCELADA",
        "cancelada_en": datetime.now(timezone.utc).isoformat(),
    }

    tabla.meta.client.transact_write_items(
        TransactItems=[
            {
                "Put": {
                    "TableName": tabla.name,
                    "Item": archivada,
                    "ConditionExpression": "attribute_not_exists(pk)",
                }
            },
            {
                "Delete": {
                    "TableName": tabla.name,
                    "Key": {"pk": cita["pk"]},
                    "ConditionExpression": "#e = :activa",
                    "ExpressionAttributeNames": {"#e": "estado"},
                    "ExpressionAttributeValues": {":activa": "ACTIVA"},
                }
            },
        ]
    )
