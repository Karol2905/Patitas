"""Acceso a la tabla de citas en DynamoDB."""

import os

import boto3

# Se crea una sola vez, cuando AWS carga la Lambda, y se reutiliza en cada
# invocación. El nombre viene de la variable de entorno, nunca del código.
tabla = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])


class CitaNoEncontrada(Exception):
    """No existe una cita con ese id."""


def _todas_las_citas():
    """Lee toda la tabla.

    DynamoDB devuelve el scan por páginas de hasta 1 MB. Si hay más,
    trae "LastEvaluatedKey" y hay que pedir la siguiente página desde ahí.
    """
    pagina = tabla.scan()
    citas = pagina["Items"]
    while "LastEvaluatedKey" in pagina:
        pagina = tabla.scan(ExclusiveStartKey=pagina["LastEvaluatedKey"])
        citas.extend(pagina["Items"])
    return citas


def listar(fecha=None):
    """Devuelve las citas ordenadas por fecha y hora, o solo las de `fecha`."""
    citas = _todas_las_citas()
    if fecha:
        citas = [c for c in citas if c.get("fecha") == fecha]
    return sorted(citas, key=lambda c: (c.get("fecha", ""), c.get("hora", "")))


def cancelar(id_cita):
    """Marca la cita como CANCELADA (borrado lógico: la cita no se elimina).

    Lanza CitaNoEncontrada si no hay ninguna cita con ese id.
    """
    cita = next((c for c in _todas_las_citas() if c.get("id") == id_cita), None)
    if cita is None:
        raise CitaNoEncontrada(id_cita)

    # La llave de la tabla es pk (fecha#hora), no id: por eso primero se busca.
    # "estado" va con #e porque algunas palabras están reservadas en DynamoDB.
    tabla.update_item(
        Key={"pk": cita["pk"]},
        UpdateExpression="SET #e = :c",
        ExpressionAttributeNames={"#e": "estado"},
        ExpressionAttributeValues={":c": "CANCELADA"},
    )
