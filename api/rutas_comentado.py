"""================================================================================
   TABLA DE RUTAS DE LA API
   Archivo: api/rutas.py
   Propósito: Define todos los endpoints disponibles, sus métodos HTTP,
              si requieren autenticación y los patrones de URL con parámetros.
================================================================================ """

import re                      # Expresiones regulares para compilar patrones de ruta
from dataclasses import dataclass, field  # Para definir la estructura de datos de una Ruta
from typing import Any, Callable  # Tipos genéricos para type hints

# Importar controladores (módulos que manejan la lógica de cada ruta)
from api.controladores import auth as auth_controller   # Controlador de autenticación/login
from api.controladores import productos as productos_controller  # Controlador de productos
from api.errores import ApiError                     # Excepción personalizada para errores HTTP
from api.respuestas import Respuesta                 # Clase base para respuestas estructuradas


# ----------------------------------------------------------- Función _compilar
def _compilar(ruta: str) -> re.Pattern[str]:
    """Compila una cadena de ruta en un patrón de expresión regular.
    
    Convierte partes de la ruta que empiezen dos puntos (:id) en grupos de captura
    que coinciden con cualquier carácter excepto barra forward.
    
    Args:
        ruta: String de ruta literal (ej. "/api/productos/:id")
    
    Returns:
        Un objeto compiled regex que se usará para matching de URLs
    """
    partes: list[str] = []  # Lista para ir acumulando las partes procesadas
    for parte in ruta.strip("/").split("/"):  # Dividir la ruta por "/" y quitar barras inicial/ final
        if parte.startswith(":"):  # Si la parte empieza dos puntos, es un parámetro dinámico
            # Convertir :nombre a (?P<nombre>[^/]+) - captura cualquier cosa menos /
            partes.append(f"(?P<{parte[1:].strip()}>[^/]+)")
        else:
            # Si no es parámetro, escapar el texto para que sea literal en regex
            partes.append(re.escape(parte))
    # Unir todas las partes con "/" y añadir ancla de inicio "^/" y final "$/?"
    return re.compile("^/" + "/".join(partes) + "/?$")


# ----------------------------------------------------------- Clase Ruta (dataclass)
@dataclass
class Ruta:
    """Dataclass que representa una sola ruta de la API.
    
    Atributos:
        metodo: El verbo HTTP necesario (GET, POST, PUT, DELETE)
        ruta: La plantilla de URL (puede contener :parametro)
        manejador: La función que se ejecutará cuando coincida esta ruta
        requiere_auth: Si el usuario necesita estar logueado para acceder
        patron: Patrón regex compilado (generado en __post_init__)
    """
    metodo: str                      # Verbo HTTP requerido (ej. "GET", "POST")
    ruta: str                        # Plantilla de URL (ej. "/api/productos/:id")
    manejador: Callable[[dict, Any], Respuesta]  # Función que maneja la petición
    requiere_auth: bool = False     # Si requiere autenticación JWT por defecto False
    patron: re.Pattern[str] = field(init=False)  # Se llenará automáticamente en __post_init__

    # ------------------------------------------------------- Método post-init
    def __post_init__(self) -> None:
        """Se ejecuta automáticamente después de crear la instancia."""
        # Compilar el patrón de ruta y almacenarlo en el atributo 'patron'
        self.patron = _compilar(self.ruta)


# ----------------------------------------------------------- Lista global de rutas(RUTAS)
# Esta es la tabla maestra de todos los endpoints disponibles en la API
RUTAS: list[Ruta] = [
    # Ruta de login: acceso público, POST a /api/auth/login
    Ruta("POST", "/api/auth/login", auth_controller.login),
    
    # Listar productos: acceso público, GET a /api/productos
    Ruta("GET", "/api/productos", productos_controller.listar),
    
    # Crear producto: requiere JWT, POST a /api/productos
    Ruta("POST", "/api/productos", productos_controller.crear, requiere_auth=True),
    
    # Obtener un producto por ID: acceso público, GET a /api/productos/:id
    Ruta("GET", "/api/productos/:id", productos_controller.obtener),
    
    # Actualizar producto: requiere JWT, PUT a /api/productos/:id
    Ruta("PUT", "/api/productos/:id", productos_controller.actualizar, requiere_auth=True),
    
    # Eliminar producto: requiere JWT, DELETE a /api/productos/:id
    Ruta("DELETE", "/api/productos/:id", productos_controller.eliminar, requiere_auth=True),
    
    # Health check: acceso público, GET a /api/salud
    Ruta("GET", "/api/salud", productos_controller.salud),
]


# ----------------------------------------------------------- Función resolver
def resolver(metodo: str, camino: str) -> tuple[Ruta, dict[str, str]]:
    """Busca la ruta correcta en la tabla RUTAS y devuelve el objeto Ruta + parámetros.
    
    Lógica:
    1. Filtrar rutas que coincidan con el patrón de URL (usando el regex compilado)
    2. Verificar que el método HTTP coincida
    3. Si encuentra coincidencia, devolver la Ruta y los parámetros capturados (:id, etc.)
    4. Si no hay coincidencia, lanzar error 404 (ruta no encontrada)
    5. Si el método no es el permitido para esa ruta, lanzar error 405 (método no permitido)
    
    Args:
        metodo: El verbo HTTP de la petición entrante
        camino: La ruta completa solicitada (ej. "/api/productos/5")
    
    Returns:
        Tupla de (objeto Ruta, diccionario de parámetros capturados)
    
    Raises:
        ApiError 404 si no encuentra ninguna ruta matching
        ApiError 405 si la ruta existe pero con método distinto
    """
    # Filtrar todas las rutas cuyo patrón regex coincida con el camino solicitado
    coincidencias = [ruta for ruta in RUTAS if ruta.patron.match(camino)]

    # Si no hay ninguna coincidencia, lanzar error 404
    if not coincidencias:
        raise ApiError(404, "Ruta no encontrada.")

    # Buscar entre las coincidencias una que tenga el método HTTP correcto
    for ruta in coincidencias:
        if ruta.metodo == metodo:
            # Si encontró la ruta y método correcto, extraer los parámetros del match
            coincidencia = ruta.patron.match(camino)
            return ruta, (coincidencia.groupdict() if coincidencia else {})

    # Si la ruta existe pero con un método diferente (ej. GET en una de POST)
    # Obtener los métodos permitidos para el mensaje de error
    permitidos = sorted({ruta.metodo for ruta in coincidencias})
    # Lanzar error 405 con cabecera Allow indicando qué métodos sí están permitidos
    raise ApiError(
        405,
        "Método no permitido para esta ruta.",
        headers={"Allow": ", ".join(permitidos)},
    )