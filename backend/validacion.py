"""Validación de datos de citas y enmascarado de datos personales."""


def enmascarar_correo(correo):
    """Oculta el usuario del correo: 'juan@gmail.com' -> 'j***@gmail.com'."""
    if not correo:
        return correo
    if "@" not in correo:
        return "***"
    usuario, dominio = correo.split("@", 1)
    return usuario[:1] + "***@" + dominio


def enmascarar_telefono(tel):
    """Deja solo los últimos 4 dígitos: '3001234567' -> '******4567'."""
    if not tel:
        return tel
    if len(tel) <= 4:
        # Si mostráramos los "últimos 4" se vería el número completo.
        return "*" * len(tel)
    return "*" * (len(tel) - 4) + tel[-4:]
