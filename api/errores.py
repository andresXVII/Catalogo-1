"""Errores controlados que se traducen a respuestas HTTP."""

from typing import Any


class ApiError(Exception):
    """Error de negocio con su código HTTP correspondiente."""

    def __init__(
        self,
        estado: int,
        mensaje: str,
        detalles: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.estado = estado
        self.mensaje = mensaje
        self.detalles = detalles
        self.headers = headers or {}

    def a_diccionario(self) -> dict[str, Any]:
        cuerpo: dict[str, Any] = {"error": self.mensaje}
        if self.detalles:
            cuerpo["detalles"] = self.detalles
        return cuerpo
