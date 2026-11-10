#!/usr/bin/env python3
"""Pruebas de humo de la API del catálogo.

Con el servidor en ejecución:
    py pruebas/probar_api.py
"""

import json
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"
RESULTADOS: list[tuple[str, bool]] = []


def peticion(metodo: str, ruta: str, cuerpo=None, token: str | None = None):
    datos = None if cuerpo is None else json.dumps(cuerpo).encode("utf-8")
    headers: dict[str, str] = {}
    if datos is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    solicitud = urllib.request.Request(
        BASE_URL + ruta,
        data=datos,
        headers=headers,
        method=metodo,
    )

    try:
        with urllib.request.urlopen(solicitud, timeout=10) as respuesta:
            return respuesta.status, respuesta.headers, _json(respuesta.read())
    except urllib.error.HTTPError as error:
        return error.code, error.headers, _json(error.read())


def _json(crudo: bytes):
    if not crudo:
        return None
    try:
        return json.loads(crudo.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return crudo.decode("utf-8", "replace")


def comprobar(nombre: str, condicion: bool, detalle: str = "") -> None:
    RESULTADOS.append((nombre, bool(condicion)))
    marca = "OK   " if condicion else "FALLO"
    extra = f" ({detalle})" if detalle and not condicion else ""
    print(f"[{marca}] {nombre}{extra}")


def main() -> int:
    try:
        estado, _, datos = peticion("GET", "/api/salud")
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        print("No se pudo conectar con el servidor.")
        print("Inicia primero la aplicación con:  py run.py")
        return 1

    comprobar("GET /api/salud responde 200", estado == 200, str(estado))
    comprobar(
        "El servicio se identifica como catalogo-api",
        isinstance(datos, dict) and datos.get("estado") == "ok",
        str(datos),
    )

    estado, _, datos = peticion("GET", "/api/productos")
    comprobar("GET /api/productos responde 200", estado == 200, str(estado))
    comprobar(
        "El listado tiene el formato esperado",
        isinstance(datos, dict)
        and isinstance(datos.get("productos"), list)
        and isinstance(datos.get("total"), int),
        str(datos),
    )

    estado, _, _ = peticion(
        "POST",
        "/api/productos",
        {
            "nombre": "Producto sin token",
            "descripcion": "No debe crearse",
            "precio": 10,
            "stock": 1,
            "categoria": "Pruebas",
        },
    )
    comprobar("POST sin JWT responde 401", estado == 401, str(estado))

    estado, _, _ = peticion(
        "POST",
        "/api/auth/login",
        {"email": "admin@catalogo.com", "password": "incorrecta"},
    )
    comprobar("Login con clave incorrecta responde 401", estado == 401, str(estado))

    estado, _, datos = peticion(
        "POST",
        "/api/auth/login",
        {"email": "admin@catalogo.com", "password": "admin123"},
    )
    token = datos.get("token") if isinstance(datos, dict) else None
    comprobar("Login válido responde 200", estado == 200, str(estado))
    comprobar("Login devuelve un JWT", bool(token), str(datos))

    if not token:
        print("\nNo se puede continuar sin token.")
        return resumen()

    estado, headers, _ = peticion(
        "OPTIONS",
        "/api/productos",
    )
    comprobar("Preflight CORS responde 204", estado == 204, str(estado))
    comprobar(
        "CORS permite cualquier origen",
        headers.get("Access-Control-Allow-Origin") == "*",
        str(headers.get("Access-Control-Allow-Origin")),
    )

    estado, _, _ = peticion(
        "POST",
        "/api/salud",
        {},
    )
    comprobar("Método no permitido responde 405", estado == 405, str(estado))

    nombre = f"Producto de prueba {int(time.time())}"
    producto = {
        "nombre": nombre,
        "descripcion": "Creado por el script de pruebas.",
        "precio": 12.5,
        "stock": 3,
        "categoria": "Pruebas",
    }

    producto_id = None
    eliminado = False

    try:
        estado, headers, datos = peticion(
            "POST", "/api/productos", producto, token
        )
        producto_id = (
            datos.get("producto", {}).get("id") if isinstance(datos, dict) else None
        )
        comprobar("POST válido responde 201", estado == 201, str(estado))
        comprobar(
            "POST incluye la cabecera Location",
            headers.get("Location") == f"/api/productos/{producto_id}",
            str(headers.get("Location")),
        )

        estado, _, _ = peticion(
            "POST",
            "/api/productos",
            producto,
            token,
        )
        comprobar("Nombre duplicado responde 409", estado == 409, str(estado))

        estado, _, _ = peticion(
            "POST",
            "/api/productos",
            {
                "nombre": "X",
                "descripcion": "",
                "precio": -5,
                "stock": -1,
                "categoria": "",
            },
            token,
        )
        comprobar("Datos inválidos responden 400", estado == 400, str(estado))

        estado, _, datos = peticion("GET", f"/api/productos/{producto_id}")
        comprobar("GET por id responde 200", estado == 200, str(estado))
        comprobar(
            "GET por id devuelve el producto correcto",
            isinstance(datos, dict)
            and datos.get("producto", {}).get("nombre") == nombre,
            str(datos),
        )

        actualizado = {**producto, "precio": 19.99, "stock": 10}
        estado, _, _ = peticion(
            "PUT", f"/api/productos/{producto_id}", actualizado, token
        )
        comprobar("PUT responde 200", estado == 200, str(estado))

        estado, _, datos = peticion("GET", f"/api/productos/{producto_id}")
        comprobar(
            "PUT persistió los cambios",
            estado == 200
            and isinstance(datos, dict)
            and datos.get("producto", {}).get("precio") == 19.99
            and datos.get("producto", {}).get("stock") == 10,
            str(datos),
        )

        estado, _, _ = peticion("GET", "/api/productos/999999")
        comprobar("Producto inexistente responde 404", estado == 404, str(estado))

        estado, _, _ = peticion(
            "DELETE", f"/api/productos/{producto_id}", token=token
        )
        eliminado = estado == 204
        comprobar("DELETE responde 204", eliminado, str(estado))

        estado, _, _ = peticion("GET", f"/api/productos/{producto_id}")
        comprobar("Producto eliminado responde 404", estado == 404, str(estado))
    finally:
        if producto_id is not None and not eliminado:
            peticion("DELETE", f"/api/productos/{producto_id}", token=token)

    return resumen()


def resumen() -> int:
    correctas = sum(1 for _, resultado in RESULTADOS if resultado)
    total = len(RESULTADOS)
    print()
    print(f"Resultado: {correctas}/{total} pruebas correctas.")
    return 0 if correctas == total else 1


if __name__ == "__main__":
    sys.exit(main())
