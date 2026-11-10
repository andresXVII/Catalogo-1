"""================================================================================
   CONTROLADORES HTTP DE PRODUCTOS
   Archivo: api/controladores/productos.py
   Propósito: Adaptadores que traducen las peticiones HTTP a llamadas a los servicios.
              Contienen la lógica mínima necesaria para formatear respuestas; la
              lógica de negocio real reside en los servicios (api/servicios/).
================================================================================ """

from typing import Any  # Para type hints de "cualquier tipo"

# Importar las respuestas estándar (ok, creado, sin_contenido)
from api.respuestas import ok, creado, sin_contenido

# Importar el servicio de productos que contiene la lógica de negocio
from api.servicios.productos import ProductoServicio

# Crear una instancia del servicio para reutilizar en todas las funciones
# Nota: En un patrón más avanzado se inyectaría el servicio, pero para este taller
# mantener una instancia global es suficiente y más sencillo.
servicio = ProductoServicio()


# ----------------------------------------------------------- Función listar
def listar(params: dict[str, str], cuerpo: Any) -> Any:
    """Maneja petición GET /api/productos - Listar todos los productos.
    
    Args:
        params: Diccionario de parámetros de la URL (vacío para listar todos)
        cuerpo: Cuerpo de la petición (no usado en listado, pero necesario por la firma)
    
    Returns:
        Diccionario {"total": <número>, "productos": <lista>} listo para convertir a JSON
    """
    # Llamar al servicio para obtener todos los productos
    productos = servicio.listar()
    
    # Retornar estructura estandarizada con total y la lista
    return ok({"total": len(productos), "productos": productos})


# ----------------------------------------------------------- Función obtener
def obtener(params: dict[str, str], cuerpo: Any) -> Any:
    """Maneja GET /api/productos/:id - Obtener un producto específico por su ID.
    
    Args:
        params: Diccionario con los parámetros extraídos de la URL (debería tener "id")
        cuerpo: Cuerpo de la petición (no usado aquí)
    
    Returns:
        Diccionario {"producto": <objeto_producto>} o lanza ApiError 404 si no existe
    """
    # Obtener el ID de la URL y llamar al servicio
    # params["id"] viene del patrón :id en la ruta
    return ok({"producto": servicio.obtener(params["id"])})


# ----------------------------------------------------------- Función crear
def crear(params: dict[str, str], cuerpo: Any) -> Any:
    """Maneja POST /api/productos - Crear un nuevo producto.
    
    Args:
        params: Diccionario de parámetros de URL (no usado en creación, el ID lo asigna el repo)
        cuerpo: Los datos del nuevo producto venidos en el body de la petición JSON
    
    Returns:
        Estructura de respuesta 201 Created con mensaje, producto y cabecera Location
    """
    # Llamar al servicio para crear el producto (valida reglas de negocio)
    # 'cuerpo' contiene los datos validados por el servicio
    producto = servicio.crear(cuerpo)
    
    # Retornar respuesta de creación con:
    # - Mensaje de confirmación
    # - Los datos del producto creado
    # - Location: URL del nuevo recurso (f"/api/productos/{producto['id']}")
    return creado(
        {"mensaje": "Producto creado.", "producto": producto},
        f"/api/productos/{producto['id']}",
    )


# ----------------------------------------------------------- Función actualizar
def actualizar(params: dict[str, str], cuerpo: Any) -> Any:
    """Maneja PUT /api/productos/:id - Actualizar un producto existente.
    
    Args:
        params: Diccionario con parámetros de URL, debe contener "id" del producto
        cuerpo: Los datos actualizados venidos en el body JSON
    
    Returns:
        Estructura con los datos actualizados o ApiError si el producto no existe
    """
    # Llamar al servicio para actualizar, pasando el ID y los nuevos datos
    # El servicio verificará que el producto exista antes de actualizar
    producto = servicio.actualizar(params["id"], cuerpo)
    
    # Si el producto fue actualizado exitosamente, retornarlo
    return ok({"mensaje": "Producto actualizado.", "producto": producto})


# ----------------------------------------------------------- Función eliminar
def eliminar(params: dict[str, str], cuerpo: Any) -> Any:
    """Maneja DELETE /api/productos/:id - Eliminar un producto.
    
    Args:
        params: Diccionario con parámetros de URL, debe contener "id" del producto
        cuerpo: No utilizado en eliminaciones
    
    Returns:
        Indica respuesta 204 No Content (sin cuerpo)
    """
    # Llamar al servicio para eliminar el producto por ID
    servicio.eliminar(params["id"])
    
    # Retornar None que el servidor interpretará como respuesta 204 No Content
    return sin_contenido()


# ----------------------------------------------------------- Función salud
def salud(params: dict[str, str], cuerpo: Any) -> Any:
    """Maneja GET /api/salud - Endpoint de verificación de salud del servicio.
    
    Este es el endpoint que usa Render para su health check y también sirve para
    probar que el servidor está corriendo correctamente.
    
    Args:
        params: Parámetros de URL (vacíos para este endpoint)
        cuerpo: Cuerpo de la petición (vacío)
    
    Returns:
        Diccionario {"estado": "ok", "servicio": "catalogo-api"} para health check
    """
    # Retornar un objeto simple de verificación
    return ok({"estado": "ok", "servicio": "catalogo-api"})