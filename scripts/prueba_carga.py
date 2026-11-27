import json
import random
import sys
import threading
import time
import uuid
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HORAS = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in (0, 30)]
MASCOTAS = [("Pachito", "Gato"), ("Nina", "Perro"), ("Laika", "Perro"), ("Mono", "Perro")]
MEZCLA = [("consulta_fecha", 0.7), ("listado", 0.1), ("reserva", 0.2)]
TIEMPO_MAXIMO = 15
CALENTAMIENTO = 5


def dias_habiles(desde, cantidad):
    dia = date.today() + timedelta(days=desde)
    dias = []
    while len(dias) < cantidad:
        if dia.weekday() != 6:
            dias.append(dia.isoformat())
        dia += timedelta(days=1)
    return dias


def pedir(metodo, url, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = Request(url, data=datos, method=metodo, headers={"Content-Type": "application/json"})
    inicio = time.perf_counter()
    try:
        with urlopen(req, timeout=TIEMPO_MAXIMO) as resp:
            estado = resp.status
            resp.read()
    except HTTPError as e:
        estado = e.code
    except (URLError, TimeoutError, OSError):
        estado = 0
    return estado, (time.perf_counter() - inicio) * 1000


def cita(fecha, hora):
    mascota, especie = random.choice(MASCOTAS)
    return {
        "fecha": fecha,
        "hora": hora,
        "mascota": mascota,
        "especie": especie,
        "dueno": "Prueba de carga",
        "correo": f"carga-{uuid.uuid4().hex[:8]}@ejemplo.com",
        "telefono": "3000000000",
        "motivo": "Prueba de carga",
        "acepta_tratamiento_datos": True,
    }


def elegir_tipo():
    r = random.random()
    acumulado = 0
    for tipo, peso in MEZCLA:
        acumulado += peso
        if r < acumulado:
            return tipo
    return MEZCLA[-1][0]


def percentil(valores, p):
    if not valores:
        return None
    ordenados = sorted(valores)
    k = max(0, min(len(ordenados) - 1, round(p / 100 * len(ordenados) + 0.5) - 1))
    return round(ordenados[k], 1)


def calentar(api):
    estados = [pedir("GET", f"{api}/citas")[0] for _ in range(CALENTAMIENTO)]
    print(f"Calentamiento: {CALENTAMIENTO} peticiones GET /citas sin medir, estados {estados}")


def fase(api, nombre, ritmo, duracion, dias):
    total = int(ritmo * duracion)
    resultados = []
    candado = threading.Lock()

    def una(tipo):
        if tipo == "consulta_fecha":
            estado, ms = pedir("GET", f"{api}/citas?fecha={random.choice(dias)}")
        elif tipo == "listado":
            estado, ms = pedir("GET", f"{api}/citas")
        else:
            cuerpo = cita(random.choice(dias), random.choice(HORAS))
            estado, ms = pedir("POST", f"{api}/citas", cuerpo)
        with candado:
            resultados.append((tipo, estado, ms))

    hilos = []
    inicio = time.perf_counter()
    for i in range(total):
        espera = inicio + i / ritmo - time.perf_counter()
        if espera > 0:
            time.sleep(espera)
        h = threading.Thread(target=una, args=(elegir_tipo(),))
        h.start()
        hilos.append(h)
    for h in hilos:
        h.join()

    latencias = [ms for _, _, ms in resultados]
    estados = {}
    for _, estado, _ in resultados:
        estados[str(estado)] = estados.get(str(estado), 0) + 1
    errores = sum(1 for _, e, _ in resultados if e >= 500)
    sin_respuesta = sum(1 for _, e, _ in resultados if e == 0)
    resumen = {
        "fase": nombre,
        "peticiones": len(resultados),
        "ritmo_pet_s": ritmo,
        "duracion_s": duracion,
        "errores_5xx": errores,
        "sin_respuesta": sin_respuesta,
        "estados": estados,
        "p50_ms": percentil(latencias, 50),
        "p95_ms": percentil(latencias, 95),
        "p99_ms": percentil(latencias, 99),
        "max_ms": round(max(latencias), 1) if latencias else None,
    }
    print(
        f"{nombre}: {resumen['peticiones']} peticiones a {ritmo} pet/s, "
        f"{errores} errores 5xx, {sin_respuesta} sin respuesta, "
        f"p50 {resumen['p50_ms']} ms, p95 {resumen['p95_ms']} ms, "
        f"p99 {resumen['p99_ms']} ms, max {resumen['max_ms']} ms, estados {estados}"
    )
    return resumen


def doble_reserva(api, simultaneas, fecha, hora):
    barrera = threading.Barrier(simultaneas)
    estados = []
    candado = threading.Lock()

    def una():
        cuerpo = cita(fecha, hora)
        barrera.wait()
        estado, _ = pedir("POST", f"{api}/citas", cuerpo)
        with candado:
            estados.append(estado)

    hilos = [threading.Thread(target=una) for _ in range(simultaneas)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    creadas = estados.count(201)
    resumen = {
        "simultaneas": simultaneas,
        "fecha": fecha,
        "hora": hora,
        "creadas": creadas,
        "rechazadas_409": estados.count(409),
        "limitadas_429": estados.count(429),
        "errores_5xx": sum(1 for e in estados if e >= 500),
        "sin_respuesta": estados.count(0),
    }
    resumen["correcto"] = (
        creadas == 1 and resumen["errores_5xx"] == 0 and resumen["sin_respuesta"] == 0
    )
    print(
        f"Doble reserva con {simultaneas} simultaneas: {creadas} creadas, "
        f"{resumen['rechazadas_409']} con 409, {resumen['limitadas_429']} con 429, "
        f"{resumen['errores_5xx']} errores 5xx, {resumen['sin_respuesta']} sin respuesta"
    )
    return resumen


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/prueba_carga.py URL_API [PETICIONES_POR_SEGUNDO] [SEGUNDOS]")
        sys.exit(2)
    api = sys.argv[1].rstrip("/")
    ritmo = float(sys.argv[2]) if len(sys.argv) > 2 else 2
    duracion = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    dias = dias_habiles(30, 20)
    calentar(api)
    fases = [
        fase(api, "Carga base", ritmo, duracion, dias),
        fase(api, "Carga 3x", ritmo * 3, duracion, dias),
    ]
    libres = dias_habiles(200 + random.randint(0, 300), 2)
    dobles = [
        doble_reserva(api, 10, libres[0], random.choice(HORAS)),
        doble_reserva(api, 20, libres[1], random.choice(HORAS)),
    ]

    resultado = {"api": api, "fases": fases, "doble_reserva": dobles}
    with open("resultado_prueba_carga.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print("Resultados en resultado_prueba_carga.json")

    todas = fases + dobles
    hay_5xx = any(r["errores_5xx"] or r["sin_respuesta"] for r in todas)
    hay_doble = any(not d["correcto"] for d in dobles)
    if hay_5xx or hay_doble:
        print("FALLA: hubo errores 5xx, peticiones sin respuesta o una doble reserva incorrecta")
        sys.exit(1)
    print("OK: sin errores 5xx y cada doble reserva creo exactamente una cita")


if __name__ == "__main__":
    main()
