"""Servidor HTTP: enrutador, CORS, archivos estáticos y manejo de errores."""

import json
import mimetypes
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from api.config import FRONTEND_DIR, HOST, MAX_BODY_BYTES, PORT
from api.errores import ApiError
from api.rutas import resolver
from api.seguridad import autenticar

TIPOS_ESTATICOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
}


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "CatalogoAPI/1.0"

    # --------------------------------------------------------------- verbos
    def do_GET(self) -> None:
        self._despachar("GET")

    def do_POST(self) -> None:
        self._despachar("POST")

    def do_PUT(self) -> None:
        self._despachar("PUT")

    def do_DELETE(self) -> None:
        self._despachar("DELETE")

    def do_OPTIONS(self) -> None:
        # Respuesta al preflight de CORS.
        self._responder_vacio(204)

    # ------------------------------------------------------------- despacho
    def _despachar(self, metodo: str) -> None:
        camino = unquote(urlsplit(self.path).path)

        try:
            if camino == "/api" or camino.startswith("/api/"):
                self._manejar_api(metodo, camino)
            elif metodo == "GET":
                self._servir_estatico(camino)
            else:
                self._responder_json(
                    405,
                    {"error": "Método no permitido."},
                    {"Allow": "GET"},
                )
        except ApiError as error:
            headers = dict(error.headers)
            tiene_cuerpo = self.headers.get("Content-Length") not in (None, "0")
            if error.estado == 401 or (
                self.command in ("POST", "PUT") and tiene_cuerpo
            ):
                # Puede quedar cuerpo sin leer: cerramos la conexión para no
                # interpretarlo como una petición nueva.
                self.close_connection = True
                headers["Connection"] = "close"
            self._responder_json(error.estado, error.a_diccionario(), headers)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc()
            self._responder_json(500, {"error": "Error interno del servidor."})

    def _manejar_api(self, metodo: str, camino: str) -> None:
        ruta, params = resolver(metodo, camino)

        if ruta.requiere_auth:
            autenticar(self.headers.get("Authorization"))

        # Se consume el cuerpo antes de responder para mantener viva la conexión.
        cuerpo = self._leer_cuerpo() if metodo in ("POST", "PUT") else None

        respuesta = ruta.manejador(params, cuerpo)

        if respuesta.estado == 204:
            self._responder_vacio(204, respuesta.headers)
        else:
            self._responder_json(respuesta.estado, respuesta.datos, respuesta.headers)

    # ---------------------------------------------------------------- cuerpo
    def _leer_cuerpo(self) -> object:
        longitud_cruda = self.headers.get("Content-Length")
        if not longitud_cruda:
            raise ApiError(400, "El cuerpo de la solicitud es obligatorio.")

        try:
            longitud = int(longitud_cruda)
        except ValueError:
            raise ApiError(400, "El encabezado Content-Length no es válido.") from None

        if longitud <= 0:
            raise ApiError(400, "El cuerpo de la solicitud está vacío.")
        if longitud > MAX_BODY_BYTES:
            raise ApiError(413, "El cuerpo de la solicitud es demasiado grande.")

        crudo = self.rfile.read(longitud)

        try:
            return json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(400, "El cuerpo debe ser JSON válido.") from None

    # ------------------------------------------------------------ respuestas
    def _responder_json(
        self,
        estado: int,
        datos: object = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        cuerpo = b"" if datos is None else json.dumps(datos, ensure_ascii=False).encode("utf-8")

        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        for clave, valor in (headers or {}).items():
            self.send_header(clave, valor)
        self.end_headers()

        if cuerpo:
            self.wfile.write(cuerpo)

    def _responder_vacio(
        self, estado: int, headers: dict[str, str] | None = None
    ) -> None:
        self.send_response(estado)
        self.send_header("Content-Length", "0")
        for clave, valor in (headers or {}).items():
            self.send_header(clave, valor)
        self.end_headers()

    def _responder_texto(self, estado: int, texto: str) -> None:
        cuerpo = texto.encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    # ------------------------------------------------------------- estáticos
    def _servir_estatico(self, camino: str) -> None:
        relativo = "index.html" if camino in ("", "/") else camino.lstrip("/")
        raiz = FRONTEND_DIR.resolve()

        try:
            archivo = (raiz / relativo).resolve()
            archivo.relative_to(raiz)
        except (ValueError, OSError):
            self._responder_texto(404, "Archivo no encontrado")
            return

        if not archivo.is_file():
            self._responder_texto(404, "Archivo no encontrado")
            return

        tipo = TIPOS_ESTATICOS.get(archivo.suffix.lower())
        if tipo is None:
            tipo = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"

        contenido = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(contenido)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(contenido)

    # ----------------------------------------------------------------- CORS
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        super().end_headers()

    def log_message(self, formato: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {formato % args}", flush=True)


def crear_servidor(host: str = HOST, puerto: int = PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, puerto), Manejador)


def ejecutar() -> None:
    try:
        servidor = crear_servidor()
    except OSError as error:
        print(f"No se pudo iniciar el servidor en {HOST}:{PORT}: {error}")
        print("Prueba con otro puerto, por ejemplo:  $env:PORT=8001; py run.py")
        raise SystemExit(1) from None

    url = f"http://{'localhost' if HOST in ('0.0.0.0', '127.0.0.1') else HOST}:{PORT}"
    print()
    print("  Catalogo de productos - API REST")
    print(f"  Formulario: {url}")
    print(f"  API:        {url}/api/productos")
    print("  Detener:    Ctrl + C")
    print()

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()
