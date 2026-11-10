"""Tabla de rutas de la API."""

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from api.controladores import auth as auth_controller
from api.controladores import productos as productos_controller
from api.errores import ApiError
from api.respuestas import Respuesta


def _compilar(ruta: str) -> re.Pattern[str]:
    partes: list[str] = []
    for parte in ruta.strip("/").split("/"):
        if parte.startswith(":"):
            partes.append(f"(?P<{parte[1:].strip()}>[^/]+)")
        else:
            partes.append(re.escape(parte))
    return re.compile("^/" + "/".join(partes) + "/?$")


@dataclass
class Ruta:
    metodo: str
    ruta: str
    manejador: Callable[[dict[str, str], Any], Respuesta]
    requiere_auth: bool = False
    patron: re.Pattern[str] = field(init=False)

    def __post_init__(self) -> None:
        self.patron = _compilar(self.ruta)


RUTAS: list[Ruta] = [
    Ruta("POST", "/api/auth/login", auth_controller.login),
    Ruta("GET", "/api/productos", productos_controller.listar),
    Ruta("POST", "/api/productos", productos_controller.crear, requiere_auth=True),
    Ruta("GET", "/api/productos/:id", productos_controller.obtener),
    Ruta("PUT", "/api/productos/:id", productos_controller.actualizar, requiere_auth=True),
    Ruta("DELETE", "/api/productos/:id", productos_controller.eliminar, requiere_auth=True),
    Ruta("GET", "/api/salud", productos_controller.salud),
]


def resolver(metodo: str, camino: str) -> tuple[Ruta, dict[str, str]]:
    """Busca la ruta y devuelve sus parámetros, o lanza 404/405."""
    coincidencias = [ruta for ruta in RUTAS if ruta.patron.match(camino)]

    if not coincidencias:
        raise ApiError(404, "Ruta no encontrada.")

    for ruta in coincidencias:
        if ruta.metodo == metodo:
            coincidencia = ruta.patron.match(camino)
            return ruta, (coincidencia.groupdict() if coincidencia else {})

    permitidos = sorted({ruta.metodo for ruta in coincidencias})
    raise ApiError(
        405,
        "Método no permitido para esta ruta.",
        headers={"Allow": ", ".join(permitidos)},
    )
