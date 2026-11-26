import json
import logging

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
    """GET /citas?fecha=YYYY-MM-DD -> 200. (Persona B)"""
    return respuesta(501, {"error": "No implementado"})


def cancelar_cita(event):
    """DELETE /citas/{id} -> 200 | 404. (Persona B)"""
    return respuesta(501, {"error": "No implementado"})
