"""================================================================================
   CAPA DE SERVICIOS: AUTENTICACIÓN DEL ADMINISTRADOR
   Archivo: api/servicios/auth.py
   Propósito: Contiene la lógica para validar las credenciales del administrador
              (comparar email y password) y generar/retornar el token JWT firmado.
================================================================================ """

import hmac  # Para comparaciones seguras de strings (prevenir ataques de timing)
from typing import Any  # Tipos genéricos

# Importar configuración del administrador y la función de creación de tokens
from api.config import ADMIN_EMAIL, ADMIN_NOMBRE, ADMIN_PASSWORD
from api.errores import ApiError  # Para lanzar errores de validación
from api.seguridad import crear_token  # Función que firma los JWTs


# ============================================================================
# Clase AuthServicio
# ============================================================================

class AuthServicio:
    """Servicio de autenticación que valida credenciales y emite tokens JWT.
    
    Responsabilidades:
    - Recibir credenciales (email/password) en formato JSON
    - Validar que tengan el formato esperado
    - Comparar con las credenciales maestras configuradas en api/config.py
    - Si son correctas, generar y retornar un token JWT firmado con HS256
    - Si son incorrectas, lanzar ApiError con código 401
    """
    
    # ------------------------------------------------------- Método login
    def login(self, datos: Any) -> dict[str, Any]:
        """Validar credenciales de login y generar token de acceso.
        
        Este es el flujo completo de login:
        1. Verificar que el cuerpo sea un diccionario JSON válido
        2. Extraer email y password del cuerpo
        3. Validar formato de email (debe contener @ y tener longitud mínima)
        4. Validar que password no esté vacío
        5. Si hay errores de validación, lanzar ApiError 400 con detalles
        6. Comparar email y password con las credenciales maestras
        7. Si coinciden, generar token JWT con crear_token()
        8. Si no coinciden, lanzar ApiError 401 "Credenciales incorrectas"
        
        Args:
            datos: El cuerpo de la petición HTTP, se espera que sea un diccionario
                   con claves "email" y "password"
    
    Returns:
        Diccionario con los siguientes componentes:
        - "token": string JWT firmado para usar en cabeceras Authorization
        - "tipo": string "Bearer" (estándar para JWT)
        - "expira_en": entero segundos hasta que el token expira (1 hora = 3600)
        - "usuario": diccionario con {"email": "...", "nombre": "..."} del admin
    
    Raises:
        ApiError 400 si los datos de entrada son inválidos (campos faltantes, formato)
        ApiError 401 si el email o password son incorrectos
    """
    # --------------------------------------------------- Validación de tipo y estructura
    # El cuerpo debe ser un diccionario (objeto JSON), si no, error 400
    if not isinstance(datos, dict):
        raise ApiError(400, "El cuerpo debe ser un objeto JSON.")
    
    # Extraer email y password del cuerpo enviado
    errores: dict[str, str] = {}  # Diccionario para acumular errores de validación
    email = datos.get("email")    # Obtener email del cuerpo
    password = datos.get("password")  # Obtener password del cuerpo
    
    # --------------------------------------------------- Validación del email
    # Reglas: debe ser string, tener @ y tener al menos 5 caracteres
    if not isinstance(email, str) or "@" not in email or len(email.strip()) < 5:
        errores["email"] = "Ingresa un correo válido."
    
    # --------------------------------------------------- Validación de password
    # Reglas: password no puede estar vacío
    if not isinstance(password, str) or not password:
        errores["password"] = "Ingresa tu contraseña."
    
    # Si hay algún error de validación, devolver error 400 con todos los detalles
    if errores:
        raise ApiError(400, "Revisa los datos de acceso.", detalles=errores)
    
    # --------------------------------------------------- Comparación de credenciales
    # Normalizar el email: quitar espacios y poner minúsculas para comparación justa
    email_normalizado = email.strip().lower()
    
    # Usar hmac.compare_digest para comparar de forma segura (resistente a timing attacks)
    # Compara: el email normalizado vs el email maestro normalizado
    # Y el password vs el password maestro
    # hmac.compare_digest usa comparaciones en tiempo constante para seguridad
    coincide = hmac.compare_digest(
        email_normalizado, ADMIN_EMAIL.strip().lower()
    ) and hmac.compare_digest(password, ADMIN_PASSWORD)
    
    # --------------------------------------------------- Verificar si coinciden
    # Si las credenciales NO coinciden, lanzar error 401 de autenticación
    if not coincide:
        raise ApiError(401, "Correo o contraseña incorrectos.")
    
    # --------------------------------------------------- Generar token si todo está bien
    # Si llegamos aquí, las credenciales son correctas
    # Crear el usuario diccionario con email y nombre para el token
    usuario = {"email": ADMIN_EMAIL, "nombre": ADMIN_NOMBRE}
    
    # Llamar a crear_token() que firma el JWT y retorna (token, segundos_vigencia)
    token, expira_en = crear_token(usuario)
    
    # Retornar la estructura completa con token, tipo, expiración y datos del usuario
    return {
        "token": token,                       # El JWT firmado para usar en headers
        "tipo": "Bearer",                     # Tipo de esquema de autenticación
        "expira_en": expira_en,               # Cuántos segundos es válido el token
        "usuario": usuario,                   # Datos del usuario logueado (email y nombre)
    }