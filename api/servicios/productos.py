"""Capa de servicios: reglas de negocio y validación de productos."""

import math
from typing import Any

from api.errores import ApiError
from api.repositorios.productos import ProductoRepositorio


def _parsear_id(valor: str | int) -> int:
    try:
        numero = int(str(valor))
    except (TypeError, ValueError):
        raise ApiError(400, "El id del producto debe ser un número entero.") from None

    if numero <= 0:
        raise ApiError(400, "El id del producto debe ser mayor que 0.")
    return numero


def _texto(
    valor: Any,
    etiqueta: str,
    minimo: int,
    maximo: int,
    errores: dict[str, str],
    campo: str,
) -> str:
    if valor is None:
        valor = ""
    if not isinstance(valor, str):
        errores[campo] = f"{etiqueta} debe ser texto."
        return ""

    valor = valor.strip()
    if len(valor) < minimo:
        errores[campo] = f"{etiqueta} debe tener al menos {minimo} caracteres."
    elif len(valor) > maximo:
        errores[campo] = f"{etiqueta} no puede superar los {maximo} caracteres."
    return valor


def _precio(valor: Any, errores: dict[str, str]) -> float | None:
    if valor is None or isinstance(valor, bool) or (isinstance(valor, str) and not valor.strip()):
        errores["precio"] = "El precio es obligatorio."
        return None

    try:
        numero = float(valor)
    except (TypeError, ValueError):
        errores["precio"] = "El precio debe ser un número."
        return None

    if not math.isfinite(numero) or numero <= 0:
        errores["precio"] = "El precio debe ser mayor que 0."
        return None
    if numero > 99_999_999:
        errores["precio"] = "El precio es demasiado alto."
        return None
    return round(numero, 2)


def _stock(valor: Any, errores: dict[str, str]) -> int | None:
    if valor is None or isinstance(valor, bool) or (isinstance(valor, str) and not valor.strip()):
        errores["stock"] = "El stock es obligatorio."
        return None

    if isinstance(valor, float) and not valor.is_integer():
        errores["stock"] = "El stock debe ser un número entero."
        return None

    try:
        numero = int(valor)
    except (TypeError, ValueError):
        errores["stock"] = "El stock debe ser un número entero."
        return None

    if numero < 0:
        errores["stock"] = "El stock no puede ser negativo."
        return None
    if numero > 1_000_000:
        errores["stock"] = "El stock es demasiado alto."
        return None
    return numero


class ProductoServicio:
    def __init__(self, repositorio: ProductoRepositorio | None = None) -> None:
        self._repo = repositorio or ProductoRepositorio()

    def listar(self) -> list[dict[str, Any]]:
        return self._repo.listar()

    def obtener(self, id_crudo: str | int) -> dict[str, Any]:
        producto_id = _parsear_id(id_crudo)
        producto = self._repo.obtener(producto_id)
        if producto is None:
            raise ApiError(404, "Producto no encontrado.")
        return producto

    def crear(self, datos: Any) -> dict[str, Any]:
        limpio = self._validar(datos)
        if self._repo.nombre_existe(limpio["nombre"]):
            raise ApiError(409, "Ya existe un producto con ese nombre.")
        return self._repo.crear(limpio)

    def actualizar(self, id_crudo: str | int, datos: Any) -> dict[str, Any]:
        producto_id = _parsear_id(id_crudo)
        if self._repo.obtener(producto_id) is None:
            raise ApiError(404, "Producto no encontrado.")

        limpio = self._validar(datos)
        if self._repo.nombre_existe(limpio["nombre"], excepto_id=producto_id):
            raise ApiError(409, "Ya existe otro producto con ese nombre.")

        actualizado = self._repo.actualizar(producto_id, limpio)
        if actualizado is None:
            raise ApiError(404, "Producto no encontrado.")
        return actualizado

    def eliminar(self, id_crudo: str | int) -> None:
        producto_id = _parsear_id(id_crudo)
        if not self._repo.eliminar(producto_id):
            raise ApiError(404, "Producto no encontrado.")

    def _validar(self, datos: Any) -> dict[str, Any]:
        if not isinstance(datos, dict):
            raise ApiError(400, "El cuerpo debe ser un objeto JSON.")

        errores: dict[str, str] = {}
        nombre = _texto(datos.get("nombre"), "El nombre", 2, 80, errores, "nombre")
        descripcion = _texto(
            datos.get("descripcion"), "La descripción", 0, 300, errores, "descripcion"
        )
        categoria = _texto(
            datos.get("categoria"), "La categoría", 2, 40, errores, "categoria"
        )
        precio = _precio(datos.get("precio"), errores)
        stock = _stock(datos.get("stock"), errores)

        if errores:
            raise ApiError(400, "Revisa los datos del producto.", detalles=errores)

        return {
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio,
            "stock": stock,
            "categoria": categoria,
        }
