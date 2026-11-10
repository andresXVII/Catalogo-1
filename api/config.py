"""Configuración general de la aplicación."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "api" / "data"
PRODUCTOS_FILE = DATA_DIR / "productos.json"

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))

# En un entorno real usa una clave larga y secreta (variable de entorno).
JWT_SECRET = os.getenv("JWT_SECRET", "clave-de-desarrollo-cambiar-en-produccion")
JWT_TTL_SEGUNDOS = int(os.getenv("JWT_TTL_SEGUNDOS", "3600"))
JWT_ISSUER = "catalogo-api"

# Usuario de demostración para el taller.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@catalogo.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")

MAX_BODY_BYTES = 1_000_000
