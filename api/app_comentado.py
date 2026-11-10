"""================================================================================
   SERVIDOR HTTP: enrutador, CORS, archivos estáticos y manejo de errores
   Archivo: api/app.py
   Propósito: Recibe peticiones HTTP, aplica CORS, sirve archivos estáticos,
              valida JWT y enruta a los controladores.
================================================================================ """

import json                    # Importa módulo json para trabajar con datos en formato JSON
import mimetypes               # Importa mimetypes para adivinar tipos de contenido por la extensión
import traceback               # Importa traceback para imprimir el seguimiento de pila en errores
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # Servidor HTTP con hilos
from pathlib import Path       # Path para manejar rutas del sistema de archivos
from urllib.parse import unquote, urlsplit  # Para decodificar URLs y separar componentes

from api.config import HOST, MAX_BODY_BYTES, PORT  # Importa configuración del proyecto
from api.errores import ApiError                   # Clase personalizada para errores con códigos HTTP
from api.rutas import resolver                     # Función que busca la ruta y parámetros en la tabla
from api.seguridad import autenticar               # Función que valida el JWT en el header Authorization

# ----------------------------------------------------------- Tipos de archivos estáticos
# Diccionario que mapea extensiones de archivo a sus respectivos MIME types
TIPOS_ESTATICOS = {
    ".html": "text/html; charset=utf-8",   # HTML con codificación UTF-8
    ".css": "text/css; charset=utf-8",     # Hojas de estilo CSS
    ".js": "text/javascript; charset=utf-8", # JavaScript
    ".json": "application/json; charset=utf-8", # Datos en formato JSON
    ".svg": "image/svg+xml",                # Gráficos vectoriales escalables
    ".png": "image/png",                    # Imágenes PNG
    ".jpg": "image/jpeg",                   # Imágenes JPEG
    ".jpeg": "image/jpeg",                  # JPEG alternativo
    ".ico": "image/x-icon",                 # Iconos de favicon
    ".webp": "image/webp",                  # Imágenes WebP
}

# ----------------------------------------------------------- Clase Manejador
class Manejador(BaseHTTPRequestHandler):
    """Clase que maneja cada petición HTTP entrante.
    
    Atributos:
        protocol_version: Versión HTTP a usar (HTTP/1.1)
        server_version: Versión del servidor que se muestra en los headers
    """
    protocol_version = "HTTP/1.1"   # Usar HTTP/1.1 para compatibilidad con proxies
    server_version = "CatalogoAPI/1.0"  # Versión identificadora del servidor

    # --------------------------------------------------------------- Verbos HTTP
    # Estos métodos simplemente redirigen al método _despachar correspondiente
    def do_GET(self) -> None:
        """Maneja peticiones GET. Llama a _despachar con 'GET'."""
        self._despachar("GET")

    def do_POST(self) -> None:
        """Maneja peticiones POST. Llama a _despachar con 'POST'."""
        self._despachar("POST")

    def do_PUT(self) -> None:
        """Maneja peticiones PUT. Llama a _despachar con 'PUT'."""
        self._despachar("PUT")

    def do_DELETE(self) -> None:
        """Maneja peticiones DELETE. Llama a _despachar con 'DELETE'."""
        self._despachar("DELETE")

    def do_OPTIONS(self) -> None:
        """Maneja peticiones OPTIONS (preflight CORS).
        
        Responde con código 204 (sin contenido) y las cabeceras CORS necesarias.
        """
        # Respuesta al preflight de CORS.
        self._responder_vacio(204)

    # --------------------------------------------------------------- Despacho de petición
    def _despachar(self, metodo: str) -> None:
        """Despacha la petición al manejador apropiado.
        
        Args:
            metodo: El verbo HTTP (GET, POST, PUT, DELETE)
        """
        # Decodifica la ruta y quita caracteres de escape
        camino = unquote(urlsplit(self.path).path)

        try:
            # Si el camino empieza con /api, se maneja como API REST
            if camino == "/api" or camino.startswith("/api/"):
                self._manejar_api(metodo, camino)
            # Si es un método GET y no es API, servir archivos estáticos
            elif metodo == "GET":
                self._servir_estatico(camino)
            # Si no coincide, devolver error 405 (Método no permitido)
            else:
                self._responder_json(
                    405,
                    {"error": "Método no permitido."},
                    {"Allow": "GET"},
                )
        except ApiError as error:
            # Si ocurre un error de negocio (validaciones, auth, etc.)
            headers = dict(error.headers)
            tiene_cuerpo = self.headers.get("Content-Length") not in (None, "0")
            # Para errores 401 o peticiones POST/PUT con cuerpo, cerrar conexión
            if error.estado == 401 or (
                self.command in ("POST", "PUT") and tiene_cuerpo
            ):
                self.close_connection = True
                headers["Connection"] = "close"
            self._responder_json(error.estado, error.a_diccionario(), headers)
        except (BrokenPipeError, ConnectionResetError):
            # Si la conexión se rompe inesperadamente, silenciar
            pass
        except Exception:
            # Si ocurre cualquier otro error inesperado
            traceback.print_exc()  # Imprimir la traza completa en la consola del servidor
            self._responder_json(500, {"error": "Error interno del servidor."})

    # --------------------------------------------------------------- Manejo de API
    def _manejar_api(self, metodo: str, camino: str) -> None:
        """Maneja las peticiones a la API REST.
        
        Args:
            metodo: El verbo HTTP
            camino: La ruta completa (ej. /api/productos/1)
        """
        # Busca la ruta en la tabla y obtiene los parámetros (ej. :id)
        ruta, params = resolver(metodo, camino)

        # Si la ruta requiere autenticación, validar el JWT
        if ruta.requiere_auth:
            autenticar(self.headers.get("Authorization"))

        # Leer y consumir el cuerpo de la petición antes de responder
        # Esto es importante para mantener la conexión viva
        cuerpo = self._leer_cuerpo() if metodo in ("POST", "PUT") else None

        # Ejecutar el manejador de la ruta y obtener la respuesta
        respuesta = ruta.manejador(params, cuerpo)

        # Si la respuesta es 204 (sin contenido), enviar vacío
        if respuesta.estado == 204:
            self._responder_vacio(204, respuesta.headers)
        else:
            # Enviar respuesta JSON con los datos y cabeceras correspondientes
            self._responder_json(respuesta.estado, respuesta.datos, respuesta.headers)

    # --------------------------------------------------------------- Leer cuerpo de petición
    def _leer_cuerpo(self) -> object:
        """Lee y valida el cuerpo de la petición HTTP.
        
        Returns:
            Los datos JSON parseados del cuerpo
            
        Raises:
            ApiError: Si el cuerpo está vacío, no es JSON o excede el límite
        """
        # Obtener la longitud del cuerpo desde el header Content-Length
        longitud_cruda = self.headers.get("Content-Length")
        if not longitud_cruda:
            raise ApiError(400, "El cuerpo de la solicitud es obligatorio.")

        try:
            # Convertir la longitud a entero
            longitud = int(longitud_cruda)
        except ValueError:
            raise ApiError(400, "El encabezado Content-Length no es válido.") from None

        # Validaciones del cuerpo
        if longitud <= 0:
            raise ApiError(400, "El cuerpo de la solicitud está vacío.")
        if longitud > MAX_BODY_BYTES:
            raise ApiError(413, "El cuerpo de la solicitud es demasiado grande.")

        # Leer los datos crudos del cuerpo
        crudo = self.rfile.read(longitud)

        try:
            # Parsear el JSON y devolver como objeto Python
            return json.loads(crudo.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ApiError(400, "El cuerpo debe ser JSON válido.") from None

    # --------------------------------------------------------------- Respuestas JSON
    def _responder_json(
        self,
        estado: int,
        datos: object = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Envía una respuesta formateada en JSON al cliente.
        
        Args:
            estado: Código HTTP de respuesta (200, 201, 404, etc.)
            datos: Los datos a enviar en el cuerpo (dict, list, etc.)
            headers: cabeceras HTTP adicionales
        """
        # Convertir los datos a string JSON codificado en UTF-8
        # Si datos es None, enviar cuerpo vacío
        cuerpo = b"" if datos is None else json.dumps(datos, ensure_ascii=False).encode("utf-8")

        # Enviar el código de estado HTTP
        self.send_response(estado)
        # Establecer el tipo de contenido como JSON con charset UTF-8
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # Informar el tamaño del cuerpo
        self.send_header("Content-Length", str(len(cuerpo)))
        # Evitar que el navegador cachee la respuesta
        self.send_header("Cache-Control", "no-store")
        # Agregar cualquier cabecera adicional (ej. Allow, WWW-Authenticate)
        for clave, valor in (headers or {}).items():
            self.send_header(clave, valor)

        # Finalizar el envío de headers y escribir el cuerpo
        self.end_headers()
        if cuerpo:
            self.wfile.write(cuerpo)

    # --------------------------------------------------------------- Respuesta vacía
    def _responder_vacio(
        self, estado: int, headers: dict[str, str] | None = None
    ) -> None:
        """Envía una respuesta HTTP sin cuerpo (código de estado solo).
        
        Común para respuestas 204 No Content o preflight OPTIONS.
        
        Args:
            estado: Código HTTP (generalmente 204)
            headers: cabeceras HTTP adicionales a incluir
        """
        # Enviar código de estado
        self.send_response(estado)
        # Establecer longitud 0 ya que no hay cuerpo
        self.send_header("Content-Length", "0")
        # Agregar cabeceras adicionales si las hay
        for clave, valor in (headers or {}).items():
            self.send_header(clave, valor)
        # Finalizar headers
        self.end_headers()

    # --------------------------------------------------------------- Respuesta de texto
    def _responder_texto(self, estado: int, texto: str) -> None:
        """Envía una respuesta HTTP con cuerpo de texto plano.
        
        Args:
            estado: Código HTTP
            texto: El mensaje de texto a enviar
        """
        # Codificar el texto a bytes UTF-8
        cuerpo = texto.encode("utf-8")
        # Enviar respuesta con tipo text/plain
        self.send_response(estado)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        # Escribir el cuerpo
        self.wfile.write(cuerpo)

    # --------------------------------------------------------------- Servir archivos estáticos
    def _servir_estatico(self, camino: str) -> None:
        """Sirve archivos estáticos (HTML, CSS, JS, imágenes) desde el directorio frontend.
        
        Args:
            camino: La ruta solicitada (ej. "/", "/styles.css", "/app.js")
        """
        # Determinar qué archivo servir basándose en la ruta
        # Si es la raíz o vacío, servir index.html
        if camino == "/" or camino == "":
            archivo_path = ROOT_DIR / "index.html"
        # Si empieza con css/, servir desde la carpeta css/
        elif camino.startswith("css/"):
            archivo_path = ROOT_DIR / "css" / camino[4:]  # Quitar "css/" del camino
        # Si empieza con js/, servir desde la carpeta js/
        elif camino.startswith("js/"):
            archivo_path = ROOT_DIR / "js" / camino[3:]  # Quitar "js/" del camino
        # Si empieza con favicon/, servir desde la carpeta favicon/
        elif camino.startswith("favicon/"):
            archivo_path = ROOT_DIR / "favicon" / camino[8:]  # Quitar "favicon/" del camino
        # Si no coincide con ninguno, archivo no encontrado
        else:
            self._responder_texto(404, "Archivo no encontrado")
            return

        # Validar que el archivo resida dentro del directorio raíz (seguridad)
        try:
            archivo_path.resolve().relative_to(ROOT_DIR)
        except (ValueError, OSError):
            # Si la ruta intenta escapar del directorio, devolver 404
            self._responder_texto(404, "Archivo no encontrado")
            return

        # Verificar que el archivo existe y es un archivo regular
        if not archivo_path.is_file():
            self._responder_texto(404, "Archivo no encontrado")
            return

        # Determinar el tipo MIME basándose en la extensión
        tipo = TIPOS_ESTATICOS.get(archivo_path.suffix.lower())
        if tipo is None:
            # Si no está en el diccionario, adivinar usando mimetypes
            tipo = mimetypes.guess_type(archivo_path.name)[0] or "application/octet-stream"

        # Leer el contenido del archivo como bytes
        contenido = archivo_path.read_bytes()

        # Enviar respuesta 200 OK con los datos
        self.send_response(200)
        # Establecer Content-Type según el tipo detectado
        self.send_header("Content-Type", tipo)
        # Informar el tamaño del contenido
        self.send_header("Content-Length", str(len(contenido)))
        # Evitar caching
        self.send_header("Cache-Control", "no-store")
        # Finalizar headers
        self.end_headers()
        # Escribir el contenido en la respuesta
        self.wfile.write(contenido)

    # ----------------------------------------------------------------- CORS headers
    def end_headers(self) -> None:
        """Añade cabeceras CORS a todas las respuestas.
        
        Esto habilita Cross-Origin Resource Sharing para que el frontend
        pueda consumir la API desde diferentes puertos/orígenes.
        """
        # Permitir solicitudes desde cualquier origen (*)
        self.send_header("Access-Control-Allow-Origin", "*")
        # Métodos HTTP permitidos en peticiones CORS preflight
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        # Cabeceras HTTP permitidas en la petición real
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        # Tiempo máximo que el navegador debe cachear la preflight request
        self.send_header("Access-Control-Max-Age", "86400")
        # Llamar al método padre para enviar los headers ya agregados
        super().end_headers()

    # ------------------------------------------------------------ Registro de actividades
    def log_message(self, formato: str, *args: object) -> None:
        """Imprime un log formateado en la consola cada vez que llega una petición.
        
        Args:
            formato: Formato de mensaje similar al printf
            args: Argumentos para el formato
        """
        # Formato: [fecha_hora] mensaje
        print(f"[{self.log_date_time_string()}] {formato % args}", flush=True)


# ----------------------------------------------------------- Función crear_servidor
def crear_servidor(host: str = HOST, puerto: int = PORT) -> ThreadingHTTPServer:
    """Crea e instancia el servidor HTTP con el manipulador definido.
    
    Args:
        host: Dirección IP en la que escuchará el servidor (0.0.0.0 para todas)
        puerto: Puerto donde escuchará el servidor (8000 por defecto)
    
    Returns:
        Una instancia de ThreadingHTTPServer configurada
    """
    # Crear el servidor atado a la clase Manejador
    return ThreadingHTTPServer((host, puerto), Manejador)


# ----------------------------------------------------------- Función ejecutar
def ejecutar() -> None:
    """Función principal que inicia el servidor y muestra información en consola.
    
    Intenta crear el servidor y si falla (por ejemplo, puerto ocupado),
    informa al usuario y sale del programa.
    """
    try:
        # Intentar crear el servidor
        servidor = crear_servidor()
    except OSError as error:
        # Si no puede iniciar (puerto ocupado, etc.)
        print(f"No se pudo iniciar el servidor en {HOST}:{PORT}: {error}")
        # Sugerir probar con otro puerto
        print("Prueba con otro puerto, por ejemplo:  $env:PORT=8001; py run.py")
        # Terminar el programa con código de error 1
        raise SystemExit(1) from None

    # Mostrar información de inicio en la consola (líneas decorativas)
    url = f"http://{'localhost' if HOST in ('0.0.0.0', '127.0.0.1') else HOST}:{PORT}"
    print()
    print("  Catalogo de productos - API REST")
    print(f"  Formulario: {url}")
    print(f"  API:        {url}/api/productos")
    print("  Detener:    Ctrl + C")
    print()

    try:
        # Iniciar el bucle principal del servidor (maneja peticiones infinitamente)
        servidor.serve_forever()
    except KeyboardInterrupt:
        # Si el usuario presiona Ctrl+C
        print("\nServidor detenido.")
    finally:
        # Siempre ejecutar al cerrar, detener el servidor gracefulmente
        servidor.server_close()