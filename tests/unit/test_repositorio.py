import pytest

ESPECIES = {"Pachito": "Gato", "Nina": "Perro", "Laika": "Perro", "Mono": "Perro"}


def _cita(id_cita, fecha="2026-12-01", hora="09:30", estado="ACTIVA", mascota="Nina"):
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
        "estado": estado,
        "creada_en": "2026-11-25T10:00:00",
        "consentimiento_en": "2026-11-25T10:00:00",
    }


def test_listar_tabla_vacia_devuelve_lista_vacia(tabla):
    import repositorio

    assert repositorio.listar() == []


def test_listar_devuelve_todas_las_citas(tabla):
    import repositorio

    tabla.put_item(Item=_cita("1", hora="09:00", mascota="Pachito"))
    tabla.put_item(Item=_cita("2", hora="10:00", mascota="Laika"))

    assert len(repositorio.listar()) == 2


def test_listar_por_fecha_devuelve_solo_esa_fecha(tabla):
    import repositorio

    tabla.put_item(Item=_cita("1", fecha="2026-12-01"))
    tabla.put_item(Item=_cita("2", fecha="2026-12-02", mascota="Mono"))
    tabla.put_item(Item=_cita("3", fecha="2026-12-01", hora="11:00", mascota="Pachito"))

    citas = repositorio.listar("2026-12-01")

    assert sorted(c["id"] for c in citas) == ["1", "3"]


def test_listar_por_fecha_sin_citas_devuelve_lista_vacia(tabla):
    import repositorio

    tabla.put_item(Item=_cita("1", fecha="2026-12-01"))

    assert repositorio.listar("2030-01-01") == []


def test_listar_ordena_por_fecha_y_hora(tabla):
    import repositorio

    tabla.put_item(Item=_cita("tarde", fecha="2026-12-01", hora="15:00", mascota="Laika"))
    tabla.put_item(Item=_cita("otro-dia", fecha="2026-12-02", hora="08:00", mascota="Mono"))
    tabla.put_item(Item=_cita("temprano", fecha="2026-12-01", hora="08:00", mascota="Pachito"))

    assert [c["id"] for c in repositorio.listar()] == ["temprano", "tarde", "otro-dia"]


def test_cancelar_deja_estado_cancelada(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc"))

    repositorio.cancelar("abc", "juan@gmail.com")

    archivada = tabla.get_item(Key={"pk": "CANCELADA#abc"})["Item"]
    assert archivada["estado"] == "CANCELADA"
    assert "cancelada_en" in archivada


def test_cancelar_libera_la_franja(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc"))

    repositorio.cancelar("abc", "juan@gmail.com")

    assert "Item" not in tabla.get_item(Key={"pk": "2026-12-01#09:30"})


def test_cancelar_conserva_los_datos_de_la_cita(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc", mascota="Pachito"))

    repositorio.cancelar("abc", "juan@gmail.com")

    archivada = tabla.get_item(Key={"pk": "CANCELADA#abc"})["Item"]
    assert archivada["id"] == "abc"
    assert archivada["fecha"] == "2026-12-01"
    assert archivada["hora"] == "09:30"
    assert archivada["mascota"] == "Pachito"
    assert archivada["especie"] == "Gato"


def test_franja_cancelada_se_puede_volver_a_agendar(tabla):
    import repositorio

    tabla.put_item(Item=_cita("vieja", mascota="Laika"))
    repositorio.cancelar("vieja", "juan@gmail.com")

    tabla.put_item(
        Item=_cita("nueva", mascota="Mono"),
        ConditionExpression="attribute_not_exists(pk)",
    )

    estados = {c["id"]: c["estado"] for c in repositorio.listar("2026-12-01")}
    assert estados == {"vieja": "CANCELADA", "nueva": "ACTIVA"}


def test_cancelar_solo_cambia_la_cita_indicada(tabla):
    import repositorio

    tabla.put_item(Item=_cita("1", hora="09:00"))
    tabla.put_item(Item=_cita("2", hora="10:00", mascota="Pachito"))

    repositorio.cancelar("1", "juan@gmail.com")

    otra = tabla.get_item(Key={"pk": "2026-12-01#10:00"})["Item"]
    assert otra["estado"] == "ACTIVA"


def test_cancelar_dos_veces_no_falla_ni_duplica(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc"))

    repositorio.cancelar("abc", "juan@gmail.com")
    repositorio.cancelar("abc", "juan@gmail.com")

    assert len(tabla.scan()["Items"]) == 1


def test_listar_incluye_las_canceladas(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc"))
    repositorio.cancelar("abc", "juan@gmail.com")

    citas = repositorio.listar("2026-12-01")

    assert [(c["id"], c["estado"]) for c in citas] == [("abc", "CANCELADA")]


def test_cancelar_inexistente_lanza_cita_no_encontrada(tabla):
    import repositorio

    with pytest.raises(repositorio.CitaNoEncontrada):
        repositorio.cancelar("no-existe", "juan@gmail.com")


def test_cancelar_con_otro_correo_lanza_correo_no_coincide(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc"))

    with pytest.raises(repositorio.CorreoNoCoincide):
        repositorio.cancelar("abc", "otro@gmail.com")

    sigue = tabla.get_item(Key={"pk": "2026-12-01#09:30"})["Item"]
    assert sigue["estado"] == "ACTIVA"


def test_cancelar_ignora_mayusculas_y_espacios_del_correo(tabla):
    import repositorio

    tabla.put_item(Item=_cita("abc"))

    repositorio.cancelar("abc", "  Juan@Gmail.com ")

    assert tabla.get_item(Key={"pk": "CANCELADA#abc"})["Item"]["estado"] == "CANCELADA"
