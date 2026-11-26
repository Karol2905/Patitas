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
