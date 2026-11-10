"""Capa de servicios: autenticación del administrador."""

import hmac
from typing import Any

from api.config import ADMIN_EMAIL, ADMIN_NOMBRE, ADMIN_PASSWORD
from api.errores import ApiError
from api.seguridad import crear_token


class AuthServicio:
    def login(self, datos: Any) -> dict[str, Any]:
        if not isinstance(datos, dict):
            raise ApiError(400, "El cuerpo debe ser un objeto JSON.")

        errores: dict[str, str] = {}
        email = datos.get("email")
        password = datos.get("password")

        if not isinstance(email, str) or "@" not in email or len(email.strip()) < 5:
            errores["email"] = "Ingresa un correo válido."
        if not isinstance(password, str) or not password:
            errores["password"] = "Ingresa tu contraseña."

        if errores:
            raise ApiError(400, "Revisa los datos de acceso.", detalles=errores)

        email_normalizado = email.strip().lower()
        coincide = hmac.compare_digest(
            email_normalizado, ADMIN_EMAIL.strip().lower()
        ) and hmac.compare_digest(password, ADMIN_PASSWORD)

        if not coincide:
            raise ApiError(401, "Correo o contraseña incorrectos.")

        usuario = {"email": ADMIN_EMAIL, "nombre": ADMIN_NOMBRE}
        token, expira_en = crear_token(usuario)

        return {
            "token": token,
            "tipo": "Bearer",
            "expira_en": expira_en,
            "usuario": usuario,
        }
