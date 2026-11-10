"""Creación y validación de tokens JWT (HS256) sin dependencias externas."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from api.config import JWT_ISSUER, JWT_SECRET, JWT_TTL_SEGUNDOS
from api.errores import ApiError


def _b64url_codificar(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _b64url_decodificar(segmento: str) -> bytes:
    relleno = "=" * (-len(segmento) % 4)
    return base64.urlsafe_b64decode(segmento + relleno)


def _firmar(contenido: str) -> str:
    firma = hmac.new(
        JWT_SECRET.encode("utf-8"),
        contenido.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_codificar(firma)


def crear_token(usuario: dict[str, Any]) -> tuple[str, int]:
    """Devuelve (token, segundos_de_vigencia)."""
    ahora = int(time.time())
    expira = ahora + JWT_TTL_SEGUNDOS

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": usuario["email"],
        "nombre": usuario["nombre"],
        "iss": JWT_ISSUER,
        "iat": ahora,
        "exp": expira,
    }

    contenido = ".".join(
        [
            _b64url_codificar(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_codificar(
                json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ),
        ]
    )
    return f"{contenido}.{_firmar(contenido)}", JWT_TTL_SEGUNDOS


def verificar_token(token: str) -> dict[str, Any]:
    mensaje = "Token inválido o expirado."
    try:
        header_b64, payload_b64, firma = token.split(".")
        contenido = f"{header_b64}.{payload_b64}"

        if not hmac.compare_digest(_firmar(contenido), firma):
            raise ValueError("Firma inválida")

        header = json.loads(_b64url_decodificar(header_b64))
        if not isinstance(header, dict) or header.get("alg") != "HS256":
            raise ValueError("Algoritmo no permitido")

        payload = json.loads(_b64url_decodificar(payload_b64))
        if not isinstance(payload, dict):
            raise ValueError("Payload inválido")
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Emisor inválido")
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("Token expirado")
        if not payload.get("sub"):
            raise ValueError("Token sin sujeto")

        return payload
    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
        raise ApiError(
            401,
            mensaje,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def autenticar(autorizacion: str | None) -> dict[str, Any]:
    """Valida el encabezado Authorization y devuelve el payload del JWT."""
    if not autorizacion:
        raise ApiError(
            401,
            "Se requiere iniciar sesión.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    partes = autorizacion.split(None, 1)
    if len(partes) != 2 or partes[0].lower() != "bearer":
        raise ApiError(
            401,
            "El encabezado Authorization debe usar el esquema Bearer.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verificar_token(partes[1].strip())
