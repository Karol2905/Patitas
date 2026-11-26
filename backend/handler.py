import json
import logging

from repositorio import CitaNoEncontrada, cancelar, listar
from validacion import enmascarar_correo, enmascarar_telefono

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
    """POST /citas -> 201 | 400 | 409. (Persona A, paso A4)"""
    return respuesta(501, {"error": "No implementado"})


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
