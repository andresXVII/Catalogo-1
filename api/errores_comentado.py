"""================================================================================
   ERRORES CONTROLADOS QUE SE TRADUCEN A RESPUESTAS HTTP
   Archivo: api/errores.py
   Propósito: Definir la clase ApiError que encapsula un código HTTP, mensaje
              y opcionalmente detalles por campo. Todos los errores del sistema
              deben instanciar esta clase para tener una respuesta consistente.
================================================================================ """

from typing import Any  # Para tipos de datos genéricos en los parámetros


# ============================================================================
# Clase ApiError
# ============================================================================

class ApiError(Exception):
    """Excepción de negocio que se traduce automáticamente a una respuesta HTTP.
    
    Esta es la clase base para todos los errores que la API puede devolver.
    A diferencia de un Exception común, ApiError lleva la información necesaria
    para responder al cliente con el código HTTP correcto y un cuerpo JSON estructurado.
    
    Atributos:
        estado: Código HTTP (400, 401, 404, 409, 500, etc.)
        mensaje: Mensaje descriptivo que se enviará al cliente
        detalles: Diccionario opcional con errores por campo (ej. {"nombre": "muy corto"})
        headers: Diccionario opcional con cabeceras HTTP adicionales (ej. WWW-Authenticate)
    """
    def __init__(
        self,
        estado: int,              # Código HTTP de respuesta
        mensaje: str,             # Mensaje que verá el cliente en el JSON
        detalles: dict[str, str] | None = None,  # Errores por campo (opcional)
        headers: dict[str, str] | None = None,  # Cabeceras HTTP adicionales (opcional)
    ) -> None:
        # Llamar al constructor de la clase padre (Exception)
        super().__init__(mensaje)
        
        # Almacenar el código HTTP
        self.estado = estado
        
        # Guardar el mensaje al cliente
        self.mensaje = mensaje
        
        # Almacenar detalles por campo si fueron proporcionados
        self.detalles = detalles or {}
        
        # Almacenar cabeceras HTTP adicionales si fueron proporcionadas
        self.headers = headers or {}

    # ------------------------------------------------------- Método a_diccionario
    def a_diccionario(self) -> dict[str, Any]:
        """Convierte el error a un diccionario listo para ser serializado a JSON.
        
        Este es el formato que se enviará al cliente en el cuerpo de la respuesta.
        
        Estructura del diccionario:
        {
            "error": "Mensaje principal",           # Siempre presente
            "detalles": {
                "campo": "Motivo del error"         # Solo si hay detalles por campo
            }
        }
        
        Returns:
            Diccionario listo para json.dumps()
        """
        # Cuerpo base del error: siempre incluye el mensaje principal
        cuerpo: dict[str, Any] = {"error": self.mensaje}
        
        # Si hay detalles por campo (ej. validaciones de formulario), agrégarlos
        if self.detalles:
            cuerpo["detalles"] = self.detalles
        
        # Retornar el diccionario completo
        return cuerpo