from validacion import enmascarar_correo, enmascarar_nombre, enmascarar_telefono


def test_enmascarar_correo_deja_primera_letra_y_dominio():
    assert enmascarar_correo("juan@gmail.com") == "j***@gmail.com"


def test_enmascarar_correo_no_revela_largo_del_usuario():
    assert enmascarar_correo("a@x.co") == "a***@x.co"
    assert enmascarar_correo("alejandra.perez@x.co") == "a***@x.co"


def test_enmascarar_correo_sin_arroba_lo_oculta_todo():
    assert enmascarar_correo("no-es-correo") == "***"


def test_enmascarar_correo_vacio_o_none_no_falla():
    assert enmascarar_correo("") == ""
    assert enmascarar_correo(None) is None


def test_enmascarar_telefono_deja_ultimos_cuatro():
    assert enmascarar_telefono("3001234567") == "******4567"


def test_enmascarar_telefono_corto_lo_oculta_todo():
    assert enmascarar_telefono("1234") == "****"
    assert enmascarar_telefono("12") == "**"


def test_enmascarar_telefono_vacio_o_none_no_falla():
    assert enmascarar_telefono("") == ""
    assert enmascarar_telefono(None) is None


def test_enmascarar_nombre_deja_la_inicial_de_cada_palabra():
    assert enmascarar_nombre("Karol Estupiñán") == "K*** E***"


def test_enmascarar_nombre_vacio_o_none_no_falla():
    assert enmascarar_nombre("") == ""
    assert enmascarar_nombre(None) is None
