import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

tabla = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


class FranjaOcupada(Exception):
    pass


class CitaNoEncontrada(Exception):
    pass


class CorreoNoCoincide(Exception):
    pass


CAMPOS_DE_LA_CITA = ["fecha", "hora", "mascota", "especie", "dueno", "correo", "telefono", "motivo"]


def guardar(datos):
    ahora = datetime.now(timezone.utc).isoformat()
    cita = {campo: str(datos.get(campo) or "").strip() for campo in CAMPOS_DE_LA_CITA}
    cita.update(
        {
            "pk": f"{cita['fecha']}#{cita['hora']}",
            "id": str(uuid.uuid4()),
            "estado": "ACTIVA",
            "creada_en": ahora,
            "consentimiento_en": ahora,
        }
    )

    try:
        tabla.put_item(Item=cita, ConditionExpression="attribute_not_exists(pk)")
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise FranjaOcupada(cita["pk"]) from error
        raise

    return cita


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


def _mismo_correo(a, b):
    return str(a or "").strip().lower() == str(b or "").strip().lower()


def listar_por_correo(correo):
    return [c for c in listar() if _mismo_correo(c.get("correo"), correo)]


def cancelar(id_cita, correo):
    cita = next((c for c in _todas_las_citas() if c.get("id") == id_cita), None)
    if cita is None:
        raise CitaNoEncontrada(id_cita)
    if not _mismo_correo(cita.get("correo"), correo):
        raise CorreoNoCoincide(id_cita)
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
