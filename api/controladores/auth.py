"""Controlador HTTP de autenticación."""

from typing import Any

from api.respuestas import Respuesta, ok
from api.servicios.auth import AuthServicio

servicio = AuthServicio()


def login(params: dict[str, str], cuerpo: Any) -> Respuesta:
    return ok(servicio.login(cuerpo))
