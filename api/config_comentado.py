"""================================================================================
   CONFIGURACIÓN GENERAL DE LA APLICACIÓN
   Archivo: api/config.py
   Propósito: Cargar variables de entorno y configurar valores por defecto.
================================================================================ """

import os                      # Importa sistema operativo para leer variables de entorno
from pathlib import Path       # Path para rutas del sistema

# ----------------------------------------------------------- Rutas del proyecto
# Directio base: padre del directorio donde está este archivo config.py
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorio del frontend (paralelo a api/, en la raíz del proyecto)
FRONTEND_DIR = BASE_DIR / "frontend"

# Directorio de datos dentro de api/
DATA_DIR = BASE_DIR / "api" / "data"

# Archivo de productos JSON que actúa como "base de datos"
PRODUCTOS_FILE = DATA_DIR / "productos.json"

# ----------------------------------------------------------- Configuración del servidor
# HOST: Dirección IP en la que escucha el servidor
# Por defecto 127.0.0.1 (localhost), pero en Render debe ser 0.0.0.0
HOST = os.getenv("HOST", "127.0.0.1")

# PORT: Puerto en el que escucha el servidor
# Se lee del entorno, default 8000; Render inyecta su propio PORT automáticamente
PORT = int(os.getenv("PORT", "8000"))

# ----------------------------------------------------------- Configuración JWT (JSON Web Token)
# JWT_SECRET: Secreto único para firmar y verificar los tokens
# En producción DEBE ser una clave larga y segura configurada por variable de entorno
# El default "clave-de-desarrollo-cambiar-en-produccion" es solo para desarrollo
JWT_SECRET = os.getenv("JWT_SECRET", "clave-de-desarrollo-cambiar-en-produccion")

# JWT_TTL_SEGUNDOS: Tiempo de vida del token en segundos (1 hora = 3600 por defecto)
# Se puede configurar mediante variable de entorno JWT_TTL_SEGUNDOS
JWT_TTL_SEGUNDOS = int(os.getenv("JWT_TTL_SEGUNDOS", "3600")

# JWT_ISSUER: Identificador quién emite el token (quién lo firma)
JWT_ISSUER = "catalogo-api"

# ----------------------------------------------------------- Credenciales de administrador
# Estas credenciales se pueden sobrescribir con variables de entorno al desplegar
# En Render se configuran en las Environment Variables del servicio

# ADMIN_EMAIL: Correo del usuario administrador para login
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@catalogo.com")

# ADMIN_PASSWORD: Contraseña del usuario administrador para login
# Ojo: En producción nunca usar contraseñas por defecto, configurar siempre via env
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ADMIN_NOMBRE: Nombre que se muestra en la interfaz al usuario logueado
ADMIN_NOMBRE = os.getenv("ADMIN_NOMBRE", "Administrador")

# ----------------------------------------------------------- Límites de seguridad
# MAX_BODY_BYTES: Tamaño máximo permitido para el cuerpo de una petición HTTP
# Protege contra ataques de subida de archivos masivos o JSONs gigantes
MAX_BODY_BYTES = 1_000_000  # 1 MB máximo