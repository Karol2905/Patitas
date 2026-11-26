"""Reglas de negocio de una cita. Python puro: aquí no hay AWS ni HTTP."""

import re
from datetime import date, datetime, time, timedelta, timezone

# Colombia está siempre en UTC-5 (no tiene horario de verano). La Lambda corre
# en UTC, así que "hoy" hay que calcularlo en hora de Colombia: a las 8 p. m.
# en Bogotá ya es "mañana" en UTC.
ZONA_COLOMBIA = timezone(timedelta(hours=-5))

CAMPOS_OBLIGATORIOS = ["fecha", "hora", "mascota", "especie", "dueno", "correo", "telefono"]

HORA_APERTURA = time(8, 0)
HORA_ULTIMA_CITA = time(17, 30)
DOMINGO = 6  # date.weekday(): lunes = 0 ... domingo = 6

# Algo@algo.algo, sin espacios. No es perfecto, pero atrapa los errores comunes.
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hoy_en_colombia():
    """Fecha de hoy en Colombia. Está en una función aparte para poder simularla en pruebas."""
    return datetime.now(ZONA_COLOMBIA).date()


def validar_cita(datos):
    """Revisa los datos de una cita.

    Devuelve una lista con un mensaje por cada problema encontrado. Si la lista
    está vacía, la cita es válida. Devolvemos TODOS los errores a la vez (y no
    solo el primero) para que el formulario pueda mostrarlos juntos.
    """
    errores = []

    # 1. Campos obligatorios: que existan y no estén vacíos ni sean solo espacios.
    for campo in CAMPOS_OBLIGATORIOS:
        valor = datos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            errores.append(f"El campo '{campo}' es obligatorio")

    # 2. Consentimiento de tratamiento de datos (Ley 1581): debe ser exactamente True.
    if datos.get("acepta_tratamiento_datos") is not True:
        errores.append("Debe aceptar el tratamiento de datos personales")

    # 3. Correo con formato válido (solo si vino; si no, ya se reportó arriba).
    correo = datos.get("correo")
    if isinstance(correo, str) and correo.strip() and not PATRON_CORREO.match(correo.strip()):
        errores.append("El correo no tiene un formato válido")

    # 4 y 5. Fecha y hora: cada una tiene su propia función de ayuda.
    errores.extend(_errores_de_fecha(datos.get("fecha")))
    errores.extend(_errores_de_hora(datos.get("hora")))

    return errores


def _errores_de_fecha(texto):
    """Valida que la fecha tenga formato AAAA-MM-DD, no esté en el pasado y no sea domingo."""
    if not isinstance(texto, str) or not texto.strip():
        return []  # Ya se reportó como campo obligatorio.

    try:
        fecha = date.fromisoformat(texto.strip())
    except ValueError:
        return ["La fecha debe tener el formato AAAA-MM-DD"]

    errores = []
    if fecha < hoy_en_colombia():
        errores.append("La fecha no puede estar en el pasado")
    if fecha.weekday() == DOMINGO:
        errores.append("No se atiende los domingos")
    return errores


def _errores_de_hora(texto):
    """Valida que la hora tenga formato HH:MM, en punto o y media, entre 08:00 y 17:30."""
    if not isinstance(texto, str) or not texto.strip():
        return []  # Ya se reportó como campo obligatorio.

    try:
        hora = time.fromisoformat(texto.strip())
    except ValueError:
        return ["La hora debe tener el formato HH:MM"]

    errores = []
    if hora.minute not in (0, 30) or hora.second != 0:
        errores.append("Las citas son en punto o y media (por ejemplo 09:00 o 09:30)")
    if not HORA_APERTURA <= hora <= HORA_ULTIMA_CITA:
        errores.append("La hora debe estar entre 08:00 y 17:30")
    return errores
