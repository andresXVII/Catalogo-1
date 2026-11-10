"""================================================================================
   CONTROLADOR DE AUTENTICACIÓN
   Archivo: api/controladores/auth.py
   Propósito: Maneja el flujo de login del administrador.
   
   Flujo:
   1. Recibe email y password en formato JSON
   2. Valida que tengan el formato correcto
   3. Compara con las credenciales maestras (api/config.py)
   4. Si son correctas, genera y retorna token JWT
   5. Si son incorrectas, retorna error 401
================================================================================ """

from typing import Any  # Para type hints

# Importar el servicio de autenticación que contiene la lógica de validación
# y generación de tokens. Este controlador es el "adapter" HTTP ↔ Servicio.
from api.servicios.auth import AuthServicio

# Crear una instancia global del servicio para reutilizar en las peticiones
# Al igual que en productos.py, se mantiene una instancia simple para el taller
servicio = AuthServicio()


# ----------------------------------------------------------- Función login
def login(cuerpo: Any) -> Any:
    """Procesar login de administrador y retornar credenciales + token.
    
    Este es el endpoint público de la API. Cualquier persona puede POST a
    /api/auth/login con email y password para obtener un token JWT.
    
    Args:
        cuerpo: Diccionario con las claves "email" y "password" venidas del body
                de la petición HTTP POST.
    
    Returns:
        Retorna el resultado de servicio.login(cuerpo), que es un diccionario
       conteniendo:
        - token: string JWT firmado con HS256
        - tipo: "Bearer" (estándar para autorización HTTP)
        - expira_en: entero segundos de vigencia (1 hora = 3600)
        - usuario: diccionario {"email": "...", "nombre": "Administrador"}
    
    Raises:
        ApiError 400 si el cuerpo no es un diccionario o datos inválidos
        ApiError 401 si correo o contraseña son incorrectos
    """
    # Devolver la respuesta del servicio, que ya valida y genera el token
    return servicio.login(cuerpo)