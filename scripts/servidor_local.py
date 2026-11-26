import importlib
import os
import sys
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PUERTO = 8000
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND = os.path.join(REPO, "frontend")
TABLA = "citas-local"
TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}
EJEMPLOS = [
    ("09:00", "Pachito", "Gato", "Juan Pérez", "juan@gmail.com", "3001234567"),
    ("10:30", "Nina", "Perro", "Ana Ruiz", "ana@correo.com", "3109876543"),
    ("08:00", "Laika", "Perro", "Luis Gómez", "luis@correo.com", "3204567890"),
    ("15:00", "Mono", "Perro", "Sara Díaz", "sara@correo.com", "3157654321"),
]


def preparar_entorno():
    os.environ.update(
        TABLE_NAME=TABLA,
        AWS_DEFAULT_REGION="us-east-1",
        AWS_ACCESS_KEY_ID="local",
        AWS_SECRET_ACCESS_KEY="local",
    )
    os.environ.pop("AWS_PROFILE", None)
    sys.path.insert(0, os.path.join(REPO, "backend"))

    boto3 = importlib.import_module("boto3")
    mock_aws = importlib.import_module("moto").mock_aws
    mock = mock_aws()
    mock.start()
    boto3.resource("dynamodb").create_table(
        TableName=TABLA,
        KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    return importlib.import_module("handler"), importlib.import_module("repositorio")


def proximos_dias_habiles(cantidad):
    dia = date.today()
    dias = []
    while len(dias) < cantidad:
        dia += timedelta(days=1)
        if dia.weekday() != 6:
            dias.append(dia.isoformat())
    return dias


def cargar_ejemplos(repositorio):
    dias = proximos_dias_habiles(len(EJEMPLOS))
    for fecha, ejemplo in zip(dias, EJEMPLOS, strict=True):
        hora, mascota, especie, dueno, correo, telefono = ejemplo
        repositorio.guardar(
            {
                "fecha": fecha,
                "hora": hora,
                "mascota": mascota,
                "especie": especie,
                "dueno": dueno,
                "correo": correo,
                "telefono": telefono,
                "motivo": "Consulta general",
            }
        )


def crear_manejador(handler):
    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, formato, *args):
            print(f"{self.command} {self.path}")

        def _api(self, metodo):
            url = urlparse(self.path)
            largo = int(self.headers.get("Content-Length") or 0)
            cuerpo = self.rfile.read(largo).decode("utf-8") if largo else None
            ruta = url.path[len("/api") :] or "/"
            query = {k: v[0] for k, v in parse_qs(url.query).items()} or None
            partes = ruta.strip("/").split("/")
            evento = {
                "httpMethod": metodo,
                "path": ruta,
                "body": cuerpo,
                "queryStringParameters": query,
                "pathParameters": {"id": partes[1]} if len(partes) == 2 else None,
            }
            resp = handler.lambda_handler(evento, None)
            self.send_response(resp["statusCode"])
            for nombre, valor in resp.get("headers", {}).items():
                self.send_header(nombre, valor)
            self.end_headers()
            self.wfile.write(resp["body"].encode("utf-8"))

        def _archivo(self):
            ruta = urlparse(self.path).path.lstrip("/") or "index.html"
            if ruta == "config.js":
                datos = f'window.API_URL = "http://localhost:{PUERTO}/api";'.encode()
                tipo = TIPOS[".js"]
            else:
                archivo = os.path.normpath(os.path.join(FRONTEND, ruta))
                if not archivo.startswith(FRONTEND + os.sep) or not os.path.isfile(archivo):
                    self.send_response(404)
                    self.end_headers()
                    return
                with open(archivo, "rb") as f:
                    datos = f.read()
                tipo = TIPOS.get(os.path.splitext(archivo)[1], "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", tipo)
            self.end_headers()
            self.wfile.write(datos)

        def do_GET(self):
            if self.path.startswith("/api"):
                self._api("GET")
            else:
                self._archivo()

        def do_POST(self):
            self._api("POST")

        def do_DELETE(self):
            self._api("DELETE")

        def do_OPTIONS(self):
            self._api("OPTIONS")

    return Manejador


def main():
    handler, repositorio = preparar_entorno()
    if "--vacio" not in sys.argv:
        cargar_ejemplos(repositorio)
    print(f"Patitas corriendo en http://localhost:{PUERTO}")
    print("Los datos estan en memoria: se borran al cerrar (Ctrl+C).")
    try:
        ThreadingHTTPServer(("localhost", PUERTO), crear_manejador(handler)).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
