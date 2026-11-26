import json
from datetime import date

import pytest
from eventos import armar_evento


@pytest.fixture
def hoy_fijo(monkeypatch):
    import validacion

    monkeypatch.setattr(validacion, "hoy_en_colombia", lambda: date(2026, 12, 1))


def datos_cita(**cambios):
    datos = {
        "motivo": "Vacunación",
        "fecha": "2026-12-02",
        "hora": "09:30",
        "mascota": "Pachito",
        "especie": "Gato",
        "dueno": "Ana Gómez",
        "correo": "ana@gmail.com",
        "telefono": "3001234567",
        "acepta_tratamiento_datos": True,
    }
    datos.update(cambios)
    return datos


def test_guardar_crea_la_cita_activa(tabla):
    import repositorio

    cita = repositorio.guardar(datos_cita())

    guardada = tabla.get_item(Key={"pk": "2026-12-02#09:30"})["Item"]
    assert guardada["id"] == cita["id"]
    assert guardada["estado"] == "ACTIVA"
    assert guardada["motivo"] == "Vacunación"
    assert guardada["consentimiento_en"]


def test_guardar_no_guarda_campos_desconocidos(tabla):
    import repositorio

    repositorio.guardar(datos_cita(rol="admin", acepta_tratamiento_datos=True))

    guardada = tabla.get_item(Key={"pk": "2026-12-02#09:30"})["Item"]
    assert "rol" not in guardada
    assert "acepta_tratamiento_datos" not in guardada


def test_guardar_genera_ids_distintos(tabla):
    import repositorio

    primera = repositorio.guardar(datos_cita(hora="09:00"))
    segunda = repositorio.guardar(datos_cita(hora="10:00"))

    assert primera["id"] != segunda["id"]


def test_guardar_en_franja_ocupada_lanza_franja_ocupada(tabla):
    import repositorio

    repositorio.guardar(datos_cita())

    with pytest.raises(repositorio.FranjaOcupada):
        repositorio.guardar(datos_cita(mascota="Nina"))


def test_franja_cancelada_se_puede_volver_a_agendar(tabla):
    import repositorio

    cita = repositorio.guardar(datos_cita())
    repositorio.cancelar(cita["id"])

    nueva = repositorio.guardar(datos_cita(mascota="Nina"))

    assert nueva["estado"] == "ACTIVA"
    assert len(repositorio.listar("2026-12-02")) == 2


def test_post_valido_devuelve_201(tabla, hoy_fijo):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("POST", "/citas", body=datos_cita()), None)

    assert resp["statusCode"] == 201
    cuerpo = json.loads(resp["body"])
    assert cuerpo["estado"] == "ACTIVA"
    assert cuerpo["fecha"] == "2026-12-02"
    assert "id" in cuerpo
    assert "correo" not in cuerpo


def test_post_sin_body_devuelve_400(tabla, hoy_fijo):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("POST", "/citas"), None)

    assert resp["statusCode"] == 400


def test_post_con_json_roto_devuelve_400(tabla, hoy_fijo):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("POST", "/citas", body="{no es json"), None)

    assert resp["statusCode"] == 400


def test_post_con_json_que_no_es_objeto_devuelve_400(tabla, hoy_fijo):
    from handler import lambda_handler

    resp = lambda_handler(armar_evento("POST", "/citas", body=[1, 2]), None)

    assert resp["statusCode"] == 400


def test_post_sin_consentimiento_devuelve_400_con_errores(tabla, hoy_fijo):
    from handler import lambda_handler

    datos = datos_cita(acepta_tratamiento_datos=False)
    resp = lambda_handler(armar_evento("POST", "/citas", body=datos), None)

    assert resp["statusCode"] == 400
    errores = json.loads(resp["body"])["errores"]
    assert "Debe aceptar el tratamiento de datos personales" in errores


def test_post_invalido_no_guarda_nada(tabla, hoy_fijo):
    from handler import lambda_handler

    lambda_handler(armar_evento("POST", "/citas", body=datos_cita(hora="07:00")), None)

    assert tabla.scan()["Items"] == []


def test_post_en_franja_ocupada_devuelve_409(tabla, hoy_fijo):
    from handler import lambda_handler

    lambda_handler(armar_evento("POST", "/citas", body=datos_cita()), None)
    resp = lambda_handler(armar_evento("POST", "/citas", body=datos_cita(mascota="Nina")), None)

    assert resp["statusCode"] == 409


def test_post_y_luego_get_muestra_la_cita_enmascarada(tabla, hoy_fijo):
    from handler import lambda_handler

    lambda_handler(armar_evento("POST", "/citas", body=datos_cita()), None)
    resp = lambda_handler(armar_evento("GET", "/citas", query={"fecha": "2026-12-02"}), None)

    citas = json.loads(resp["body"])
    assert len(citas) == 1
    assert citas[0]["mascota"] == "Pachito"
    assert "***" in citas[0]["correo"]
