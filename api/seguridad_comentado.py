"""================================================================================
   CREACIÓN Y VALIDACIÓN DE TOKENS JWT (HS256)
   Archivo: api/seguridad.py
   Propósito: Implementar firma y verificación de tokens JSON Web Token usando
              el algoritmo HMAC-SHA256 (HS256) sin dependencias externas.
================================================================================ """

import base64                  # Codificación y decodificación Base64
import hashlib                 # Funciones hash (SHA256 entre otras)
import hmac                    # Codificación HMAC (código de autenticación de mensaje hashado)
import json                    # Para parsear y generar JSON en el payload del token
import time                    # Para timestamps (tiempo de expiración del token)
from typing import Any        # Tipos para anotaciones de tipo

from api.config import JWT_ISSUER, JWT_SECRET, JWT_TTL_SEGUNDOS  # Configuración JWT
from api.errores import ApiError                         # Excepciones con códigos HTTP


# ----------------------------------------------------------- Codificación Base64URL
def _b64url_codificar(datos: bytes) -> str:
    """Codifica bytes usando Base64URL (sin relleno y seguros para URLs).
    
    Base6URL es una variante de Base64 que:
    - Usa caracteres seguros para URLs (en lugar de + y / usa - y _)
    - Elimina los caracteres de relleno (=) al final
    
    Args:
        datos: Los bytes a codificar
    
    Returns:
        String codificado en Base64URL sin caracteres de relleno
    """
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _b64url_decodificar(segmento: str) -> bytes:
    """Decodifica un segmento Base6URL de vuelta a bytes.
    
    Como Base6URL omite el relleno, hay que agregarlo según la regla:
    - La cantidad de caracteres de relleno necesarios es: 4 - (long % 4)
    - Donde % es el módulo (resto de la división)
    
    Args:
        segmento: String Base64URL para decodificar
    
    Returns:
        Los bytes originales decodificados
    """
    # Calcular cuánto relleno (=) agregar para que la longitud sea múltiplo de 4
    relleno = "=" * (-len(segmento) % 4)
    # Agregar el relleno y decodificar usando base64 estándar
    return base64.urlsafe_b64decode(segmento + relleno)


# ----------------------------------------------------------- Función _firmar
def _firmar(contenido: str) -> str:
    """Firma el contenido usando HMAC-SHA256 con el secreto configurado.
    
    Este es el paso que garantiza la integridad del token: cualquiera que no conozca
    el JWT_SECRET no podrá crear un token con una firma válida.
    
    Args:
        contenido: La cadena header.payload que se va a firmar
    
    Returns:
        String con la firma en Base64URL (sin relleno)
    """
    # Crear la firma usando HMAC-SHA256
    # key: JWT_SECRET.encode() - la clave secreta
    # msg: contenido.encode("ascii") - el mensaje (header.payload)
    # digestmod: hashlib.sha256 - el algoritmo hash
    firma = hmac.new(
        JWT_SECRET.encode("utf-8"),
        contenido.encode("ascii"),
        hashlib.sha256,
    ).digest()
    # Retornar la firma codificada en Base64URL (sin los = finales)
    return _b64url_codificar(firma)


# ----------------------------------------------------------- Función crear_token
def crear_token(usuario: dict[str, Any]) -> tuple[str, int]:
    """Crea un nuevo token JWT firmado para el usuario dado.
    
    Este token contendrá:
    - header: información sobre el algoritmo y tipo
    - payload: los datos del usuario (email, nombre, emisión, expiración)
    - firma: firma HMAC-SHA256 del header.payload
    
    El token tiene la estructura: header.payload.firma (todos separados por punto)
    
    Args:
        usuario: Diccionario con los datos del usuario (mínimo: email y nombre)
    
    Returns:
        Tupla de (token_completo, segundos_de_vigencia)
        Ejemplo: ("eyJhbGci... .eyJzdWI... .firma", 3600)
    """
    # Obtener el tiempo actual en segundos (epoch Unix)
    ahora = int(time.time())
    # Calcular la fecha de expiración: ahora + TTL configurado
    expira = ahora + JWT_TTL_SEGUNDOS

    # ------------------------------------------------------- Construir header JWT
    # El header indica el algoritmo y tipo de token
    header = {"alg": "HS256", "typ": "JWT"}  # HS256 = HMAC con SHA-256, tipo JWT
    
    # Codificar el header a Base64URL
    header_codificado = _b64url_codificar(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )

    # ------------------------------------------------------- Construir payload (datos)
    # El payload contiene los datos relevantes del usuario y metadatos
    payload = {
        "sub": usuario["email"],           # Subject: típicamente el email del usuario
        "nombre": usuario["nombre"],       # Nombre completo del usuario
        "iss": JWT_ISSUER,                 # Issuer: quién firmó este token
        "iat": ahora,                      # Issued At: cuándo se emitió el token (timestamp)
        "exp": expira,                     # Expiration: cuándo expira el token (timestamp)
    }
    
    # Codificar el payload a Base64URL
    # ensure_ascii=False permite caracteres no ASCII en el nombre, etc.
    payload_codificado = _b64url_codificar(
        json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )

    # ------------------------------------------------------- Componer el token completo
    # Unir header y payload con un punto en medio: "header.payload"
    contenido = ".".join([header_codificado, payload_codificado])

    # Firmar el contenido concatenado usando HMAC-SHA256 con el secreto
    # Esto produce la tercera parte del token
    firma = _firmar(contenido)

    # Retornar el token completo (tres partes separadas por puntos) y el TTL
    return f"{contenido}.{firma}", JWT_TTL_SEGUNDOS


# ----------------------------------------------------------- Función verificar_token
def verificar_token(token: str) -> dict[str, Any]:
    """Verifica y decodifica un token JWT, validando su integridad y vigencia.
    
    Este es el paso crítico de seguridad: si cualquier validación falla,
    se lanza ApiError(401, "Token inválido o expirado.") con header WWW-Authenticate.
    
    Validaciones realizadas:
    1. El token tiene exactamente 3 partes separadas por puntos
    2. Se recalcula la firma y se compara con la firma original (evita ataques de tiempo)
    3. El algoritmo debe ser HS256
    4. El emisor (iss) debe ser "catalogo-api"
    5. El token no debe haber expirado (comparar exp con tiempo actual)
    6. Debe existir el subject (sub - típicamente el email)
    7. El payload debe ser un diccionario válido
    
    Args:
        token: String completo del JWT (header.payload.firma)
    
    Returns:
        Diccionario con los datos del payload decodificado si todo es correcto
    
    Raises:
        ApiError 401 con header WWW-Authenticate si falla alguna validación
    """
    mensaje = "Token inválido o expirado."  # Mensaje de error por defecto
    
    try:
        # --- Paso 1: Dividir el token en sus 3 partes ---
        # El token debe tener exactamente 2 puntos separando 3 segmentos
        header_b64, payload_b64, firma = token.split(".")
        
        # --- Paso 2: Reconstruir el contenido firmado ---
        # Para verificar la firma, necesitamos el header.payload sin la firma original
        contenido = f"{header_b64}.{payload_b64}"
        
        # --- Paso 3: Verificar que la firma sea válida ---
        # _firmar() recalcula la firma y hmac.compare_digest compara de forma segura
        # (resistente a ataques de medición de tiempo)
        if not hmac.compare_digest(_firmar(contenido), firma):
            raise ValueError("Firma inválida")
        
        # --- Paso 4: Decodificar header y validar algoritmo ---
        header = json.loads(_b64url_decodificar(header_b64))
        # Verificar que el header sea un diccionario y que el algoritmo sea HS256
        if not isinstance(header, dict) or header.get("alg") != "HS256":
            raise ValueError("Algoritmo no permitido")
        
        # --- Paso 5: Decodificar payload y validar estructura ---
        payload = json.loads(_b64url_decodificar(payload_b64))
        # Verificar que el payload sea un diccionario
        if not isinstance(payload, dict):
            raise ValueError("Payload inválido")
        
        # --- Paso 6: Validar emisor (issuer) ---
        # El token debe haber sido emitido por este servicio específicamente
        if payload.get("iss") != JWT_ISSUER:
            raise ValueError("Emisor inválido")
        
        # --- Paso 7: Validar tiempo de expiración ---
        # Si el tiempo actual es mayor que 'exp', el token ha caducado
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("Token expirado")
        
        # --- Paso 8: Validar subject (sub) ---
        # El token debe tener un sujeto (email del usuario)
        if not payload.get("sub"):
            raise ValueError("Token sin sujeto")
        
        # Si todas las validaciones pasaron, retornar el payload decodificado
        return payload
        
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as e:
        # Cualquier error en las validaciones arriba lanza excección
        # Y se transforma en un ApiError 401 apropiado
        raise ApiError(
            401,
            mensaje,
            headers={"WWW-Authenticate": "Bearer"},
        ) from None