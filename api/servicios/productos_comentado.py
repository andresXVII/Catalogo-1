"""================================================================================
   CAPA DE SERVICIOS: REGLAS DE NEGOCIO Y VALIDACIÓN DE PRODUCTOS
   Archivo: api/servicios/productos.py
   Propósito: Contiene la lógica de negocio validando entradas, reglas de
              negocio (nombre duplicado, precios/Stock válidos) y coordinando
              el acceso a los repositorios para persistir o leer datos.
================================================================================ """

import math  # Para validaciones de números finitos (isfinite)
from typing import Any  # Tipos genéricos

# Importar la excepción ApiError para lanzar errores con códigos HTTP
from api.errores import ApiError

# Importar el repositorio de productos para interactuar con los datos (JSON file)
from api.repositorios.productos import ProductoRepositorio


# ============================================================================
# Función _parsear_id
# ============================================================================

def _parsear_id(valor: str | int) -> int:
    """Validar y convertir un valor a entero para usarse como ID de producto.
    
    Esta función es llamada por casi todas las operaciones que necesitan un ID
    (obtener, actualizar, eliminar). Se asegura de que el ID sea un entero positivo.
    
    Validaciones:
    - Si no se puede convertir a entero, lanzar ApiError 400
    - Si el entero es 0 o negativo, lanzar ApiError 400
    
    Args:
        valor: Puede ser string o entero, proviene de la URL :id
    
    Returns:
        Entero positivo representando el ID del producto
    
    Raises:
        ApiError 400 si el ID no es válido
    """
    try:
        # Intentar convertir a entero pasando por string primero
        numero = int(str(valor))
    except (TypeError, ValueError):
        # Si falla el lanzamiento ApiError 400 con mensaje claro
        raise ApiError(400, "El id del producto debe ser un número entero.") from None
    
    # Validar que el número sea positivo (mayor que 0)
    if numero <= 0:
        raise ApiError(400, "El id del producto debe ser mayor que 0.")
    
    # Retornar el entero validado
    return numero


# ============================================================================
# Función _texto
# ============================================================================

def _texto(
    valor: Any,
    etiqueta: str,
    minimo: int,
    maximo: int,
    errores: dict[str, str],
    campo: str,
) -> str:
    """Validar y formatear un campo de tipo texto.
    
    Esta función es reutilizada por el servicio de productos para validar
    nombre, descripción y categoría. Centraliza las reglas de validación de texto.
    
    Validaciones aplicadas:
    - Si es None, convertir a cadena vacía ""
    - Si no es string, agregar error al diccionario y retornar ""
    - Quitar espacios en blanco al inicio y final (.strip())
    - Validar longitud mínima (len < minimo -> error)
    - Validar longitud máxima (len > maximo -> error)
    - Retornar el texto limpio si pasa todas las validaciones
    
    Args:
        valor: El valor a validar (puede venir del JSON body o None)
        etiqueta: Nombre descriptivo para el mensaje de error (ej. "El nombre")
        minimo: Longitud mínima permitida (ej. 2 para nombre)
        maximo: Longitud máxima permitida (ej. 80 para nombre)
        errores: Diccionario donde se irán agregando errores por campo
        campo: Nombre de la clave en el diccionario de errores (ej. "nombre")
    
    Returns:
        String limpio (sin espacios extra) si pasa validaciones, o cadena vacía si falla
    """
    # Si el valor es None, tratarlo como cadena vacía
    if valor is None:
        valor = ""
    
    # Si no es un string, registrar error y retornar vacío
    if not isinstance(valor, str):
        errores[campo] = f"{etiqueta} debe ser texto."
        return ""
    
    # Quitar espacios en blanco al inicio y al final
    valor = valor.strip()
    
    # Validar longitud mínima
    if len(valor) < minimo:
        errores[campo] = f"{etiqueta} debe tener al menos {minimo} caracteres."
    
    # Validar longitud máxima (solo si no hubo error de mínima, o acumular)
    elif len(valor) > maximo:
        errores[campo] = f"{etiqueta} no puede superar los {maximo} caracteres."
    
    # Si passed all validations, return the cleaned text
    return valor


# ============================================================================
# Función _precio
# ============================================================================

def _precio(valor: Any, errores: dict[str, str]) -> float | None:
    """Validar y convertir un valor a precio (float con 2 decimales).
    
    Validaciones aplicadas:
    - Si es None, bool vacío o string vacío -> error "precio es obligatorio"
    - Intentar convertir a float; si falla -> error "precio debe ser un número"
    - Verificar que sea un número finito (no NaN, no Infinity)
    - Verificar que sea mayor que 0
    - Verificar que no sea demasiado alto (mayor a 99,999,999)
    - Redondear a 2 decimales al final
    - Retornar None si hubo algún error (el diccionario errores tendrá el mensaje)
    
    Args:
        valor: El valor a validar (puede ser número, string, None, bool)
        errores: Diccionario donde se acumularán mensajes de error por campo
    
    Returns:
        Float redondeado a 2 decimales si es válido, None si hay error
    """
    # Si es None, booleano falso, o string vacío/blanco -> precio obligatorio
    if valor is None or isinstance(valor, bool) or (isinstance(valor, str) and not valor.strip()):
        errores["precio"] = "El precio es obligatorio."
        return None
    
    try:
        # Intentar convertir a número float
        numero = float(valor)
    except (TypeError, ValueError):
        # Si no se puede convertir, error
        errores["precio"] = "El precio debe ser un número."
        return None
    
    # Verificar que sea un número finito (no NaN, no Infinity positivo/negativo)
    if not math.isfinite(numero) or numero <= 0:
        errores["precio"] = "El precio debe ser mayor que 0."
        return None
    
    # Verificar límite máximo de precio (evitar valores absurdos)
    if numero > 99_999_999:
        errores["precio"] = "El precio es demasiado alto."
        return None
    
    # Si pasó todas las validaciones, redondear a 2 decimales y retornar
    return round(numero, 2)


# ============================================================================
# Función _stock
# ============================================================================

def _stock(valor: Any, errores: dict[str, str]) -> int | None:
    """Validar y convertir un valor a stock (entero no negativo).
    
    Validaciones aplicadas:
    - Si es None, bool o string vacío -> error "stock es obligatorio"
    - Si es float con decimales (ej. 5.5) -> error "stock debe ser entero"
    - Intentar convertir a entero; si falla -> error mensaje apropiado
    - Verificar que sea >= 0 (no negativo)
    - Verificar límite máximo (1,000,000)
    - Retornar entero validado si todo OK, None si hay error
    
    Args:
        valor: El valor a validar (puede venir de JSON body)
        errores: Diccionario donde acumular mensajes de error por campo
    
    Returns:
        Entero validado si es correcto, None si hay error de validación
    """
    # Si es None, booleano o string vacío -> stock obligatorio
    if valor is None or isinstance(valor, bool) or (isinstance(valor, str) and not valor.strip()):
        errores["stock"] = "El stock es obligatorio."
        return None
    
    # Si es float con parte decimal (ej. 5.5), rechazarlo
    if isinstance(valor, float) and not valor.is_integer():
        errores["stock"] = "El stock debe ser un número entero."
        return None
    
    try:
        # Intentar convertir a entero
        numero = int(valor)
    except (TypeError, ValueError):
        # Si falla, error mensaje apropiado
        errores["stock"] = "El stock debe ser un número entero."
        return None
    
    # Validar que no sea negativo
    if numero < 0:
        errores["stock"] = "El stock no puede ser negativo."
        return None
    
    # Validar límite máximo de stock (1 millón)
    if numero > 1_000_000:
        errores["stock"] = "El stock es demasiado alto."
        return None
    
    # Si pasó todo, retornar el entero validado
    return numero


# ============================================================================
# Clase ProductoServicio
# ============================================================================

class ProductoServicio:
    """Servicio de negocio para el catálogo de productos.
    
    Esta clase encapsula toda la lógica que no pertenece al repositorio (acceso a datos)
    ni al controlador (adaptación HTTP). Sus responsabilidades incluyen:
    
    1. Validación de entradas (campos, rangos, tipos de datos)
    2. Reglas de negocio (nombre duplicado, producto inexistente)
    3. Coordinar llamadas al repositorio para operaciones CRUD
    4. Retornar datos limpios o lanzar ApiError con códigos HTTP apropiados
    
    El repositorio se inyecta en el constructor o se usa una instancia global
    (ProductoRepositorio()) para simplicidad en este taller.
    """
    
    # ------------------------------------------------------- Inicializar con repositorio
    def __init__(self, repositorio=None) -> None:
        # Si se pasa un repositorio usarlo, otherwise crear uno nuevo
        # Esto permite pruebas con repositorios mock, pero por defecto usa el real
        self._repo = repositorio or ProductoRepositorio()
    
    # ------------------------------------------------------- Método listar
    def listar(self) -> list[dict[str, Any]]:
        """Obtener todos los productos del catálogo.
        
        Simplemente delega al repositorio y retorna la lista de productos.
        No tiene parámetros ni validaciones complejas.
        
        Returns:
            Lista de diccionarios, cada uno representa un producto con sus atributos
        """
        return self._repo.listar()
    
    # ------------------------------------------------------- Método obtener
    def obtener(self, id_crudo: str | int) -> dict[str, Any]:
        """Obtener un producto específico por su ID.
        
        Flujo:
        1. Parsear y validar el ID usando _parsear_id()
        2. Consultar el repositorio por ese ID
        3. Si no existe, lanzar ApiError 404 "Producto no encontrado."
        4. Si existe, retornar el producto (deepcopy para evitar mutaciones)
        
        Args:
            id_crudo: El ID venido de la URL, puede ser string o int
            
        Returns:
            Diccionario con los datos del producto
            
        Raises:
            ApiError 404 si no existe un producto con ese ID
        """
        # Paso 1: Parsear y validar el ID
        producto_id = _parsear_id(id_crudo)
        
        # Paso 2: Consultar el repositorio
        producto = self._repo.obtener(producto_id)
        
        # Paso 3: Verificar si existe, si no, lanzar error 404
        if producto is None:
            raise ApiError(404, "Producto no encontrado.")
        
        # Paso 4: Retornar el producto (deepcopy para protección)
        # Se usa copy.deepcopy para que el cliente no pueda modificar el repositorio
        # mediante la referencia devuelta
        import copy
        return copy.deepcopy(producto)
    
    # ------------------------------------------------------- Método crear
    def crear(self, datos: Any) -> dict[str, Any]:
        """Crear un nuevo producto en el catálogo.
        
        Flujo completo:
        1. Validar los datos de entrada usando _validar()
        2. Verificar que el nombre no sea duplicado (nombre_existe())
        3. Si es duplicado, lanzar ApiError 409 "Ya existe un producto con ese nombre."
        4. Si no, asignar ID nuevo, fechas y guardar en repositorio
        5. Retornar el producto creado con sus datos completos
        
        Args:
            datos: Diccionario con los campos del producto (nombre, descripcion, precio, stock, categoria)
            
        Returns:
            Diccionario con el producto creado incluyendo su nuevo ID y fechas
            
        Raises:
            ApiError 400 si los datos son inválidos (validación _validar)
            ApiError 409 si ya existe un producto con ese nombre
        """
        # Paso 1: Validar los datos y obtener diccionario limpio
        # _validar() retorna un diccionario limpio o lanza ApiError 400
        limpio = self._validar(datos)
        
        # Paso 2: Verificar que el nombre no exista ya en el catálogo
        # nombre_existe(excepto_id=None) revisa todos los productos
        # Si el nombre ya existe, error 409 Conflict
        if self._repo.nombre_existe(limpio["nombre"]):
            raise ApiError(409, "Ya existe un producto con ese nombre.")
        
        # Paso 3: Si no es duplicado, crear el producto en el repositorio
        # Esto asigna ID, fechas y guarda el JSON
        return self._repo.crear(limpio)
    
    # ------------------------------------------------------- Método actualizar
    def actualizar(self, id_crudo: str | int, datos: Any) -> dict[str, Any]:
        """Actualizar un producto existente en el catálogo.
        
        Flujo:
        1. Parsear y validar el ID del producto a actualizar
        2. Verificar que el producto exista (sino, 404)
        3. Validar los datos de actualización
        4. Verificar que el nuevo nombre no sea duplicado (excluyendo el ID actual)
        5. Si es duplicado, error 409
        6. Si todo OK, actualizar en repositorio y retornar el producto actualizado
        
        Args:
            id_crudo: ID del producto a actualizar (viene de URL :id)
            datos: Diccionario con los nuevos valores a actualizar
            
        Returns:
            Diccionario con el producto ya actualizado
            
        Raises:
            ApiError 404 si no existe el producto
            ApiError 409 si el nuevo nombre ya pertenece a otro producto
        """
        # Paso 1: Parsear y validar el ID
        producto_id = _parsear_id(id_crudo)
        
        # Paso 2: Verificar que el producto exista antes de actualizar
        # Si no existe, lanzar 404
        if self._repo.obtener(producto_id) is None:
            raise ApiError(404, "Producto no encontrado.")
        
        # Paso 3: Validar los datos de la actualización
        limpio = self._validar(datos)
        
        # Paso 4: Verificar nombre duplicado, pero EXCLuyendo el ID que se está actualizando
        # El parámetro excepto_id=producto_id evita false positivo si el nombre
        # es el mismo que ya tiene este producto (no es "duplicado", es el mismo)
        if self._repo.nombre_existe(limpio["nombre"], excepto_id=producto_id):
            raise ApiError(409, "Ya existe otro producto con ese nombre.")
        
        # Paso 5: Actualizar en el repositorio y retornar el resultado
        return self._repo.actualizar(producto_id, limpio)
    
    # ------------------------------------------------------- Método eliminar
    def eliminar(self, id_crudo: str | int) -> None:
        """Eliminar un producto del catálogo.
        
        Flujo:
        1. Parsear y validar el ID
        2. Verificar que existe (sino, 404)
        3. Llamar al repositorio para eliminarlo (pop de la lista)
        
        Args:
            id_crudo: ID del producto a eliminar
            
        Raises:
            ApiError 404 si no existe el producto
        """
        # Paso 1: Validar ID
        producto_id = _parsear_id(id_crudo)
        
        # Paso 2: Verificar existencia
        if self._repo.obtener(producto_id) is None:
            raise ApiError(404, "Producto no encontrado.")
        
        # Paso 3: Eliminar del repositorio (el repositorio se encarga de guardar el JSON actualizado)
        self._repo.eliminar(producto_id)
    
    # ------------------------------------------------------- Método _validar
    def _validar(self, datos: Any) -> dict[str, Any]:
        """Validación completa de los datos de un producto.
        
        Esta es la función maestra de validación que llama a _texto, _precio y _stock
        para validar todos los campos requeridos en un producto.
        
        Validaciones realizadas:
        - Verificar que datos sea un diccionario (sino error 400)
        - Validar nombre usando _texto() (2-80 caracteres, reglas de formato)
        - Validar descripción usando _texto() (0-300 caracteres, opcional)
        - Validar categoría usando _texto() (2-40 caracteres)
        - Validar precio usando _precio() (mayor a 0, máximo 99M, número finito)
        - Validar stock usando _stock() (entero >= 0, máximo 1M)
        - Si hay errores en alguno, lanzar ApiError 400 con todos los detalles
        - Si todo OK, retornar un diccionario limpio con solo los campos válidos
        
        Args:
            datos: Diccionario con los campos del producto desde el body JSON
            
        Returns:
            Diccionario con solo los campos que pasaron validación, listo para guardar
            
        Raises:
            ApiError 400 con detalles de qué campos fallaron
        """
        # Paso 1: Verificar que los datos sean un diccionario
        if not isinstance(datos, dict):
            raise ApiError(400, "El cuerpo debe ser un objeto JSON.")
        
        # Paso 2: Inicializar diccionario de errores vacío
        errores: dict[str, str] = {}
        
        # Paso 3: Validar cada campo usando las funciones auxiliares
        # Nombre: obligatorio, 2-80 caracteres
        nombre = _texto(datos.get("nombre"), "El nombre", 2, 80, errores, "nombre")
        
        # Descripción: opcional, máximo 300 caracteres
        descripcion = _texto(
            datos.get("descripcion"), "La descripción", 0, 300, errores, "descripcion"
        )
        
        # Categoría: obligatoria, 2-40 caracteres
        categoria = _texto(datos.get("categoria"), "La categoría", 2, 40, errores, "categoria")
        
        # Precio: obligatorio, número > 0, máximo 99M
        precio = _precio(datos.get("precio"), errores)
        
        # Stock: obligatorio, entero >= 0, máximo 1M
        stock = _stock(datos.get("stock"), errores)
        
        # Paso 3: Si hay algún error en el diccionario, lanzar ApiError 400
        if errores:
            # Retornar error 400 con todos los mensajes de validación agrupados
            raise ApiError(400, "Revisa los datos del producto.", detalles=errores)
        
        # Paso 4: Si todo es válido, retornar un diccionario limpio con solo los datos OK
        return {
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio,
            "stock": stock,
            "categoria": categoria,
        }