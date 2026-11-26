import json
import random
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

DOMINGO = 6


def pedir(metodo, url, cuerpo=None):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    peticion = urllib.request.Request(url, data=datos, method=metodo)
    peticion.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(peticion, timeout=60) as respuesta:
            texto = respuesta.read().decode("utf-8")
            return respuesta.status, texto
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8")


def fecha_de_prueba():
    fecha = date.today() + timedelta(days=random.randint(30, 300))
    if fecha.weekday() == DOMINGO:
        fecha += timedelta(days=1)
    return fecha.isoformat()


def verificar(condicion, mensaje):
    estado = "OK " if condicion else "FALLO"
    print(f"[{estado}] {mensaje}")
    if not condicion:
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Uso: python scripts/smoke_test.py <url_api> <url_sitio>")
        sys.exit(2)

    url_api = sys.argv[1].rstrip("/")
    url_sitio = sys.argv[2]

    estado, html = pedir("GET", url_sitio)
    verificar(estado == 200 and "Veterinaria Patitas" in html, f"El sitio responde ({estado})")

    fecha = fecha_de_prueba()
    hora = random.choice(["08:00", "09:30", "11:00", "14:30", "16:00", "17:30"])
    cita = {
        "motivo": "Consulta general",
        "fecha": fecha,
        "hora": hora,
        "mascota": "Smoke",
        "especie": "Perro",
        "dueno": "Prueba automática",
        "correo": "smoke@patitas.co",
        "telefono": "3000000000",
        "acepta_tratamiento_datos": True,
    }

    estado, texto = pedir("POST", f"{url_api}/citas", cita)
    verificar(estado == 201, f"POST /citas crea la cita ({estado})")
    id_cita = json.loads(texto)["id"]

    estado, texto = pedir("POST", f"{url_api}/citas", cita)
    verificar(estado == 409, f"POST /citas en la misma franja responde 409 ({estado})")

    estado, texto = pedir("GET", f"{url_api}/citas?fecha={fecha}")
    citas = json.loads(texto) if estado == 200 else []
    encontrada = next((c for c in citas if c.get("id") == id_cita), None)
    verificar(encontrada is not None, f"GET /citas lista la cita creada ({estado})")
    verificar("***" in encontrada.get("correo", ""), "El correo aparece enmascarado")

    estado, _ = pedir("DELETE", f"{url_api}/citas/{id_cita}")
    verificar(estado == 200, f"DELETE /citas/{{id}} cancela la cita ({estado})")

    estado, _ = pedir("POST", f"{url_api}/citas", cita)
    verificar(estado == 201, f"La franja cancelada se puede volver a agendar ({estado})")

    print("Smoke test completado")


if __name__ == "__main__":
    main()
