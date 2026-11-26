import os

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

    tabla.update_item(
        Key={"pk": cita["pk"]},
        UpdateExpression="SET #e = :c",
        ExpressionAttributeNames={"#e": "estado"},
        ExpressionAttributeValues={":c": "CANCELADA"},
    )
