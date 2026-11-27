import re
from datetime import date, datetime, time, timedelta, timezone

ZONA_COLOMBIA = timezone(timedelta(hours=-5))

CAMPOS_OBLIGATORIOS = ["fecha", "hora", "mascota", "especie", "dueno", "correo", "telefono"]

HORA_APERTURA = time(8, 0)
HORA_ULTIMA_CITA = time(17, 30)
DOMINGO = 6
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hoy_en_colombia():
    return datetime.now(ZONA_COLOMBIA).date()


def validar_cita(datos):

    errores = []

    for campo in CAMPOS_OBLIGATORIOS:
        valor = datos.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            errores.append(f"El campo '{campo}' es obligatorio")

    if datos.get("acepta_tratamiento_datos") is not True:
        errores.append("Debe aceptar el tratamiento de datos personales")

    correo = datos.get("correo")
    if isinstance(correo, str) and correo.strip() and not PATRON_CORREO.match(correo.strip()):
        errores.append("El correo no tiene un formato válido")

    errores.extend(_errores_de_fecha(datos.get("fecha")))
    errores.extend(_errores_de_hora(datos.get("hora")))

    return errores


def _errores_de_fecha(texto):

    if not isinstance(texto, str) or not texto.strip():
        return []

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

    if not isinstance(texto, str) or not texto.strip():
        return []
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


def enmascarar_correo(correo):
    if not correo:
        return correo
    if "@" not in correo:
        return "***"
    usuario, dominio = correo.split("@", 1)
    return usuario[:1] + "***@" + dominio


def enmascarar_telefono(tel):
    if not tel:
        return tel
    if len(tel) <= 4:
        return "*" * len(tel)
    return "*" * (len(tel) - 4) + tel[-4:]


def enmascarar_nombre(nombre):
    if not nombre:
        return nombre
    return " ".join(palabra[:1] + "***" for palabra in str(nombre).split())
