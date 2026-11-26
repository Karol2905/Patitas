"""Builder de events falsos, con la forma que API Gateway le manda a la Lambda."""

import json


def armar_evento(metodo, path, body=None, query=None, path_params=None):
    """Devuelve un event como el que recibe lambda_handler.

    Ejemplos:
        armar_evento("GET", "/citas", query={"fecha": "2026-12-01"})
        armar_evento("DELETE", "/citas/abc", path_params={"id": "abc"})
        armar_evento("POST", "/citas", body={"mascota": "Firulais"})

    ``body`` puede ser un dict (se convierte a texto JSON, como hace API
    Gateway), un string tal cual (sirve para probar JSON inválido) o None.
    """
    if isinstance(body, (dict, list)):
        body = json.dumps(body)
    return {
        "httpMethod": metodo,
        "path": path,
        "body": body,
        "queryStringParameters": query,
        "pathParameters": path_params,
    }
