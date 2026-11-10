"""Objetos de respuesta que devuelven los controladores."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Respuesta:
    estado: int
    datos: Any = None
    headers: dict[str, str] = field(default_factory=dict)


def ok(datos: Any = None) -> Respuesta:
    return Respuesta(200, datos)


def creado(datos: Any, location: str) -> Respuesta:
    return Respuesta(201, datos, {"Location": location})


def sin_contenido() -> Respuesta:
    return Respuesta(204)
