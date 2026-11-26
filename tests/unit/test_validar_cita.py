"""Pruebas de validar_cita. Python puro: no necesitan el DynamoDB falso."""

from datetime import date

import pytest
import validacion
from validacion import validar_cita

# Fijamos "hoy" en el martes 1 de diciembre de 2026 para que las pruebas no
# dependan del día en que se corran.
HOY = date(2026, 12, 1)


@pytest.fixture(autouse=True)
def hoy_fijo(monkeypatch):
    """Antes de cada prueba, reemplaza hoy_en_colombia() por una que siempre devuelve HOY."""
    monkeypatch.setattr(validacion, "hoy_en_colombia", lambda: HOY)


def cita_valida(**cambios):
    """Devuelve una cita válida. Con cambios=... se reemplazan campos para cada prueba."""
    datos = {
        "fecha": "2026-12-02",  # miércoles, mañana
        "hora": "09:30",
        "mascota": "Firulais",
        "especie": "Perro",
        "dueno": "Ana Gómez",
        "correo": "ana@gmail.com",
        "telefono": "3001234567",
        "motivo": "Vacunación",
        "acepta_tratamiento_datos": True,
    }
    datos.update(cambios)
    return datos


def test_cita_valida_no_tiene_errores():
    assert validar_cita(cita_valida()) == []


def test_cita_para_hoy_es_valida():
    assert validar_cita(cita_valida(fecha="2026-12-01")) == []


@pytest.mark.parametrize("campo", validacion.CAMPOS_OBLIGATORIOS)
def test_campo_faltante_da_error(campo):
    datos = cita_valida()
    del datos[campo]
    assert f"El campo '{campo}' es obligatorio" in validar_cita(datos)


def test_campo_con_solo_espacios_da_error():
    assert "El campo 'mascota' es obligatorio" in validar_cita(cita_valida(mascota="   "))


def test_sin_consentimiento_da_error():
    datos = cita_valida()
    del datos["acepta_tratamiento_datos"]
    assert "Debe aceptar el tratamiento de datos personales" in validar_cita(datos)


def test_consentimiento_como_texto_no_sirve():
    errores = validar_cita(cita_valida(acepta_tratamiento_datos="true"))
    assert "Debe aceptar el tratamiento de datos personales" in errores


@pytest.mark.parametrize("correo", ["ana", "ana@", "ana@gmail", "ana gomez@gmail.com"])
def test_correo_invalido_da_error(correo):
    assert "El correo no tiene un formato válido" in validar_cita(cita_valida(correo=correo))


def test_fecha_pasada_da_error():
    errores = validar_cita(cita_valida(fecha="2026-11-30"))
    assert "La fecha no puede estar en el pasado" in errores


def test_fecha_mal_escrita_da_error_sin_romperse():
    errores = validar_cita(cita_valida(fecha="02/12/2026"))
    assert "La fecha debe tener el formato AAAA-MM-DD" in errores


def test_domingo_da_error():
    errores = validar_cita(cita_valida(fecha="2026-12-06"))
    assert "No se atiende los domingos" in errores


@pytest.mark.parametrize("hora", ["07:30", "18:00", "17:31"])
def test_hora_fuera_de_horario_da_error(hora):
    assert "La hora debe estar entre 08:00 y 17:30" in validar_cita(cita_valida(hora=hora))


@pytest.mark.parametrize("hora", ["08:00", "17:30"])
def test_horas_limite_son_validas(hora):
    assert validar_cita(cita_valida(hora=hora)) == []


def test_hora_que_no_es_en_punto_ni_y_media_da_error():
    errores = validar_cita(cita_valida(hora="09:15"))
    assert "Las citas son en punto o y media (por ejemplo 09:00 o 09:30)" in errores


def test_hora_mal_escrita_da_error_sin_romperse():
    assert "La hora debe tener el formato HH:MM" in validar_cita(cita_valida(hora="9 am"))


def test_devuelve_todos_los_errores_a_la_vez():
    errores = validar_cita(cita_valida(fecha="2026-11-30", hora="07:00", correo="mal"))
    assert len(errores) == 3
