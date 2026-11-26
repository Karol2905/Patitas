import json

from eventos import armar_evento


def test_tabla_empieza_vacia(tabla):
    assert tabla.scan()["Items"] == []


def test_tabla_usa_el_nombre_de_la_variable_de_entorno(tabla):
    assert tabla.name == "citas-test"


def test_tabla_guarda_y_lee_por_pk(tabla):
    tabla.put_item(Item={"pk": "2026-12-01#09:30", "id": "1", "estado": "ACTIVA"})
    item = tabla.get_item(Key={"pk": "2026-12-01#09:30"})["Item"]
    assert item["estado"] == "ACTIVA"


def test_cada_prueba_recibe_una_tabla_nueva(tabla):
    assert tabla.scan()["Items"] == []


def test_evento_convierte_body_dict_a_texto():
    evento = armar_evento("POST", "/citas", body={"mascota": "Pachito"})
    assert evento["httpMethod"] == "POST"
    assert evento["path"] == "/citas"
    assert isinstance(evento["body"], str)
    assert json.loads(evento["body"]) == {"mascota": "Pachito"}


def test_evento_sin_datos_opcionales_trae_none():
    evento = armar_evento("GET", "/citas")
    assert evento["body"] is None
    assert evento["queryStringParameters"] is None
    assert evento["pathParameters"] is None


def test_evento_con_query_y_path_params():
    evento = armar_evento(
        "DELETE", "/citas/abc", query={"fecha": "2026-12-01"}, path_params={"id": "abc"}
    )
    assert evento["queryStringParameters"] == {"fecha": "2026-12-01"}
    assert evento["pathParameters"] == {"id": "abc"}


def test_evento_deja_pasar_body_texto_para_probar_json_invalido():
    evento = armar_evento("POST", "/citas", body="{no es json")
    assert evento["body"] == "{no es json"
