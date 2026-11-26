import json
import logging

from repositorio import CitaNoEncontrada, FranjaOcupada, cancelar, guardar, listar
from validacion import enmascarar_correo, enmascarar_telefono, validar_cita

logger = logging.getLogger()
logger.setLevel(logging.INFO)

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def respuesta(status, body):

    return {
        "statusCode": status,
        "headers": HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


def lambda_handler(event, context):

    metodo = event.get("httpMethod")
    path = event.get("path", "")

    try:
        if metodo == "OPTIONS":
            return respuesta(200, {})
        elif path == "/citas" and metodo == "POST":
            return crear_cita(event)
        elif path == "/citas" and metodo == "GET":
            return listar_citas(event)
        elif path.startswith("/citas/") and metodo == "DELETE":
            return cancelar_cita(event)
        else:
            return respuesta(404, {"error": "Ruta no encontrada"})
    except Exception:
        logger.exception("Error inesperado")
        return respuesta(500, {"error": "Error interno"})


def crear_cita(event):
    try:
        datos = json.loads(event.get("body") or "")
    except json.JSONDecodeError:
        return respuesta(400, {"errores": ["El cuerpo de la petición debe ser un JSON válido"]})

    if not isinstance(datos, dict):
        return respuesta(400, {"errores": ["El cuerpo de la petición debe ser un objeto JSON"]})

    errores = validar_cita(datos)
    if errores:
        return respuesta(400, {"errores": errores})

    try:
        cita = guardar(datos)
    except FranjaOcupada:
        return respuesta(409, {"error": "Ya hay una cita agendada en esa fecha y hora"})

    logger.info("Cita creada id=%s", cita["id"])
    return respuesta(
        201,
        {"id": cita["id"], "fecha": cita["fecha"], "hora": cita["hora"], "estado": cita["estado"]},
    )


def listar_citas(event):
    query = event.get("queryStringParameters") or {}
    citas = listar(query.get("fecha"))
    resultado = []
    for cita in citas:
        visible = {k: v for k, v in cita.items() if k != "pk"}
        visible["correo"] = enmascarar_correo(cita.get("correo"))
        visible["telefono"] = enmascarar_telefono(cita.get("telefono"))
        resultado.append(visible)
    return respuesta(200, resultado)


def cancelar_cita(event):
    parametros = event.get("pathParameters") or {}
    id_cita = parametros.get("id") or event.get("path", "").split("/")[-1]
    try:
        cancelar(id_cita)
    except CitaNoEncontrada:
        return respuesta(404, {"error": "Cita no encontrada"})
    logger.info("Cita cancelada id=%s", id_cita)
    return respuesta(200, {"id": id_cita, "estado": "CANCELADA"})
