"""Controladores HTTP de productos (sin lógica de negocio)."""

from typing import Any

from api.respuestas import Respuesta, creado, ok, sin_contenido
from api.servicios.productos import ProductoServicio

servicio = ProductoServicio()


def listar(params: dict[str, str], cuerpo: Any) -> Respuesta:
    productos = servicio.listar()
    return ok({"total": len(productos), "productos": productos})


def obtener(params: dict[str, str], cuerpo: Any) -> Respuesta:
    return ok({"producto": servicio.obtener(params["id"])})


def crear(params: dict[str, str], cuerpo: Any) -> Respuesta:
    producto = servicio.crear(cuerpo)
    return creado(
        {"mensaje": "Producto creado.", "producto": producto},
        f"/api/productos/{producto['id']}",
    )


def actualizar(params: dict[str, str], cuerpo: Any) -> Respuesta:
    producto = servicio.actualizar(params["id"], cuerpo)
    return ok({"mensaje": "Producto actualizado.", "producto": producto})


def eliminar(params: dict[str, str], cuerpo: Any) -> Respuesta:
    servicio.eliminar(params["id"])
    return sin_contenido()


def salud(params: dict[str, str], cuerpo: Any) -> Respuesta:
    return ok({"estado": "ok", "servicio": "catalogo-api"})
