import json

from eventos import armar_evento

ESPECIES = {"Pachito": "Gato", "Nina": "Perro", "Laika": "Perro", "Mono": "Perro"}


def _cita(id_cita, fecha="2026-12-01", hora="09:30", mascota="Nina"):
    return {
        "pk": f"{fecha}#{hora}",
        "id": id_cita,
        "fecha": fecha,
        "hora": hora,
        "mascota": mascota,
        "especie": ESPECIES[mascota],
        "dueno": "Juan Pérez",
        "correo": "juan@gmail.com",
        "telefono": "3001234567",
        "motivo": "Vacuna",
        "estado": "ACTIVA",
        "creada_en": "2026-11-25T10:00:00",
        "consentimiento_en": "2026-11-25T10:00:00",
    }


def _llamar(*args, **kwargs):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento(*args, **kwargs), None)
    return resp, json.loads(resp["body"])


def test_get_citas_devuelve_200_con_datos_enmascarados(tabla):
    tabla.put_item(Item=_cita("1"))

    resp, citas = _llamar("GET", "/citas")

    assert resp["statusCode"] == 200
    assert len(citas) == 1
    assert "***" in citas[0]["correo"]
    assert citas[0]["correo"] == "j***@gmail.com"
    assert citas[0]["telefono"] == "******4567"


def test_get_citas_no_expone_la_llave_interna(tabla):
    tabla.put_item(Item=_cita("1"))

    _, citas = _llamar("GET", "/citas")

    assert "pk" not in citas[0]


def test_get_citas_sin_citas_devuelve_lista_vacia(tabla):
    resp, citas = _llamar("GET", "/citas")

    assert resp["statusCode"] == 200
    assert citas == []


def test_get_citas_con_fecha_filtra(tabla):
    tabla.put_item(Item=_cita("1", fecha="2026-12-01"))
    tabla.put_item(Item=_cita("2", fecha="2026-12-02", mascota="Laika"))

    resp, citas = _llamar("GET", "/citas", query={"fecha": "2026-12-02"})

    assert resp["statusCode"] == 200
    assert [c["id"] for c in citas] == ["2"]
    assert citas[0]["mascota"] == "Laika"


def test_delete_cita_existente_devuelve_200(tabla):
    tabla.put_item(Item=_cita("abc"))

    resp, body = _llamar("DELETE", "/citas/abc", path_params={"id": "abc"})

    assert resp["statusCode"] == 200
    assert body == {"id": "abc", "estado": "CANCELADA"}


def test_delete_toma_el_id_del_path_si_no_hay_path_params(tabla):
    tabla.put_item(Item=_cita("abc"))

    resp, _ = _llamar("DELETE", "/citas/abc")

    assert resp["statusCode"] == 200


def test_delete_cita_inexistente_devuelve_404(tabla):
    resp, body = _llamar("DELETE", "/citas/no-existe", path_params={"id": "no-existe"})

    assert resp["statusCode"] == 404
    assert body == {"error": "Cita no encontrada"}


def test_delete_y_luego_get_muestra_la_cita_cancelada(tabla):
    tabla.put_item(Item=_cita("abc"))

    _llamar("DELETE", "/citas/abc", path_params={"id": "abc"})
    _, citas = _llamar("GET", "/citas")

    assert [(c["id"], c["estado"]) for c in citas] == [("abc", "CANCELADA")]


def test_options_devuelve_200(tabla):
    resp, _ = _llamar("OPTIONS", "/citas")

    assert resp["statusCode"] == 200


def test_toda_respuesta_trae_cors(tabla):
    tabla.put_item(Item=_cita("abc"))

    respuestas = [
        _llamar("GET", "/citas")[0],
        _llamar("DELETE", "/citas/abc", path_params={"id": "abc"})[0],
        _llamar("DELETE", "/citas/x", path_params={"id": "x"})[0],
        _llamar("OPTIONS", "/citas")[0],
    ]

    for resp in respuestas:
        assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


def test_los_logs_no_tienen_datos_personales(tabla, caplog):
    tabla.put_item(Item=_cita("abc"))

    with caplog.at_level("INFO"):
        _llamar("GET", "/citas")
        _llamar("DELETE", "/citas/abc", path_params={"id": "abc"})

    assert "juan@gmail.com" not in caplog.text
    assert "3001234567" not in caplog.text
    assert "Juan Pérez" not in caplog.text
