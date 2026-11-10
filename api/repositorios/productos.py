"""Capa de acceso a datos: persistencia del catálogo en JSON."""

import copy
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.config import PRODUCTOS_FILE


def _ahora() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


class ProductoRepositorio:
    """Repositorio thread-safe con escritura atómica."""

    def __init__(self, ruta: Path = PRODUCTOS_FILE) -> None:
        self._ruta = ruta
        self._candado = threading.RLock()
        self._datos = self._cargar()

    def _cargar(self) -> dict[str, Any]:
        self._ruta.parent.mkdir(parents=True, exist_ok=True)

        if not self._ruta.exists():
            datos: dict[str, Any] = {"siguiente_id": 1, "productos": []}
            self._guardar(datos)
            return datos

        with self._ruta.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, dict) or not isinstance(datos.get("productos"), list):
            raise ValueError("El archivo de productos tiene un formato inválido.")

        maximo = max((p.get("id", 0) for p in datos["productos"]), default=0)
        datos.setdefault("siguiente_id", maximo + 1)
        return datos

    def _guardar(self, datos: dict[str, Any]) -> None:
        temporal = self._ruta.with_suffix(".tmp")
        with temporal.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
            archivo.write("\n")
        os.replace(temporal, self._ruta)

    def listar(self) -> list[dict[str, Any]]:
        with self._candado:
            return copy.deepcopy(self._datos["productos"])

    def obtener(self, producto_id: int) -> dict[str, Any] | None:
        with self._candado:
            for producto in self._datos["productos"]:
                if producto.get("id") == producto_id:
                    return copy.deepcopy(producto)
        return None

    def nombre_existe(self, nombre: str, excepto_id: int | None = None) -> bool:
        buscado = nombre.strip().casefold()
        with self._candado:
            for producto in self._datos["productos"]:
                if producto.get("id") == excepto_id:
                    continue
                if str(producto.get("nombre", "")).strip().casefold() == buscado:
                    return True
        return False

    def crear(self, datos: dict[str, Any]) -> dict[str, Any]:
        with self._candado:
            producto = {
                "id": int(self._datos["siguiente_id"]),
                **datos,
                "creado_en": _ahora(),
                "actualizado_en": _ahora(),
            }
            self._datos["siguiente_id"] = producto["id"] + 1
            self._datos["productos"].append(producto)
            self._guardar(self._datos)
            return copy.deepcopy(producto)

    def actualizar(self, producto_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        with self._candado:
            for indice, producto in enumerate(self._datos["productos"]):
                if producto.get("id") != producto_id:
                    continue

                actualizado = {
                    **producto,
                    **datos,
                    "id": producto_id,
                    "creado_en": producto.get("creado_en", _ahora()),
                    "actualizado_en": _ahora(),
                }
                self._datos["productos"][indice] = actualizado
                self._guardar(self._datos)
                return copy.deepcopy(actualizado)
        return None

    def eliminar(self, producto_id: int) -> bool:
        with self._candado:
            productos = self._datos["productos"]
            for indice, producto in enumerate(productos):
                if producto.get("id") == producto_id:
                    productos.pop(indice)
                    self._guardar(self._datos)
                    return True
        return False
