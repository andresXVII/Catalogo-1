"""================================================================================
   RESPUESTAS DE LOS CONTROLADORES
   Archivo: api/respuestas.py
   Propósito: Funciones auxiliares que construyen respuestas HTTP estandarizadas
              (éxitos, creación de recursos, contenido nulo) para usar en los
              controladores. Evitan repetir la lógica de formateo de respuestas JSON.
================================================================================ """

from typing import Any  # Para tipos de datos genéricos

from api.errores import ApiError  # Importar para poder lanzar errores si es necesario


# ----------------------------------------------------------- Función ok
def ok(datos: object = None) -> Any:
    """Construye una respuesta HTTP 200 OK con datos opcionales.
    
    Esta es la respuesta estándar para peticiones GET exitosas y operaciones
    que no modifican el estado o devuelven información.
    
    Args:
        datos: Los datos a incluir en la respuesta (puede ser dict, list, objeto, None)
        Si es None, se enviará {"error": ...} o un objeto vacío dependiendo del controlador.
    
    Returns:
        Un diccionario con la estructura {"datos": <lo_que_se_pase>} listo para
        ser retornado por el controlador y convertido a JSON por el servidor.
    """
    # Retornar un diccionario con la clave "datos"
    # Si datos es None, aún así retornará {"datos": None} que los controladores
    # suelen sobrescribir con una estructura apropiada
    return {"datos": datos}


# ----------------------------------------------------------- Función creado
def creado(datos: object, location: str) -> Any:
    """Construye una respuesta HTTP 201 Created.
    
    Esta respuesta se usa cuando se crea un nuevo recurso. Incluye:
    - Código de estado HTTP 201
    - Un mensaje indicando que el recurso fue creado
    - Los datos del recurso creado
    - Una cabecera 'Location' con la URL donde se puede acceder al nuevo recurso
    
    Args:
        datos: Los datos del recurso recién creado (generalmente el objeto completo)
        location: La URL donde el cliente puede acceder al nuevo recurso (ej.
                  "/api/productos/5" o "http://example.com/api/productos/5")
    
    Returns:
        Diccionario listo para ser retornado por el controlador, contendrá:
        - mensaje: "Producto creado." o similar
        - producto: los datos del recurso
        - Location: la URL para acceder al recurso
    """
    # Retornar la estructura estándar de creación
    return {
        "mensaje": "Producto creado.",  # Mensaje genérico, los controladores pueden sobrescribir
        "producto": datos,              # Los datos del recurso creado
        "Location": location              # URL donde el cliente debe dirigir su próxima petición
    }


# ----------------------------------------------------------- Función sin_contenido
def sin_contenido() -> Any:
    """Construye una respuesta HTTP 204 No Content.
    
    Esta respuesta indica que la operación fue exitosa, pero no se devuelve ningún
    cuerpo en la respuesta. Comúnmente usada para:
    - Peticiones DELETE exitosas (el producto fue borrado)
    - Respuestas preflight OPTIONS (CORS)
    - Cualquier operación donde el cliente no necesite información adicional
    
    Returns:
        Un marcador/indicador que el servidor interpretará como "responder 204 sin cuerpo"
    """
    # Retornar None o un indicador especial que el manejador de servidor sabe interpretar
    # como "responder 204 No Content"
    return None