import json

from eventos import armar_evento


def test_options_devuelve_200(tabla):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("OPTIONS", "/citas"), None)

    assert resp["statusCode"] == 200


def test_ruta_desconocida_devuelve_404(tabla):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("GET", "/otra-cosa"), None)

    assert resp["statusCode"] == 404
    assert json.loads(resp["body"]) == {"error": "Ruta no encontrada"}


def test_metodo_no_soportado_devuelve_404(tabla):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("PUT", "/citas"), None)

    assert resp["statusCode"] == 404


def test_respuesta_trae_cors(tabla):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("OPTIONS", "/citas"), None)

    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


def test_body_es_texto_json(tabla):
    from handler import respuesta

    resp = respuesta(200, {"mensaje": "Cita para nina"})

    assert isinstance(resp["body"], str)
    assert json.loads(resp["body"]) == {"mensaje": "Cita para nina"}
