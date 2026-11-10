"""================================================================================
   CAPA DE ACCESO A DATOS: PERSISTENCIA DEL CATÁLOGO EN JSON
   Archivo: api/repositorios/productos.py
   Propósito: Capa más baja del sistema. Solo se encarga de leer y escribir el archivo
              JSON que funciona como "base de datos". Implementa thread-safety con
              candado (lock) y escritura atómica para evitar corrupción del archivo.
================================================================================ """

import copy  # Para hacer deepcopy de los datos y evitar mutaciones no deseadas
import json  # Para leer y escribir archivos JSON
import os  # Para operaciones del sistema de archivos (rename atómico)
import threading  # Para el candado de thread-safety
from datetime import datetime, timezone  # Para marcas de tiempo (created_en, updated_en)
from pathlib import Path  # Para manejo de rutas del sistema de archivos
from typing import Any  # Tipos genéricos

from api.config import PRODUCTOS_FILE  # Ruta al archivo productos.json


# ----------------------------------------------------------- Función _ahora
def _ahora() -> str:
    """Generar una marca de tiempo en formato ISO 8601 con formato de fecha/hora.
    
    Formato de salida: "2026-11-10T10:30:00Z" (con reemplazos de +00:00 a "Z")
    
    Usa UTC para consistencia independientemente de la zona horaria del servidor.
    
    Returns:
        String con la fecha y hora actual formateada
    """
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")  # Incluye segundos, no fracciones de segundo
        .replace("+00:00", "Z")  # Reemplazar el sufijo +00:00 por notación Z (UTC)
    )


# ============================================================================
# Clase ProductoRepositorio
# ============================================================================

class ProductoRepositorio:
    """Repositorio de datos para el catálogo de productos.
    
    Esta clase es la capa más baja del patrón de capas. Sus únicas responsabilidades:
    - Leer el archivo productos.json y parsearlo
    - Escribir datos al archivo JSON con escritura atómica (para no corromper)
    - Gestionar el siguiente ID disponible
    - Operaciones CRUD básicas sobre la lista de productos
    
    Características importantes:
    - Thread-safe: usa threading.RLock para operaciones concurrentes
    - Escritura atómica: escribe a un archivo temporal y luego usa os.replace()
    - Persistencia en JSON: los datos se guardan en disco pero son efímeros
    - Deep copy: retorna copias profundas para proteger el estado interno
    """
    
    # ------------------------------------------------------- Constructor __init__
    def __init__(self, ruta: Path = PRODUCTOS_FILE) -> None:
        """Inicializar el repositorio.
        
        Args:
            ruta: Ruta Path object pointing al archivo productos.json
                   Default usa la configuración desde api/config.py
        """
        # Guardar la ruta del archivo de productos
        self._ruta = ruta
        
        # Candado de solo lectura/escritura para threading (RLock permite mismo hilo múltiples veces)
        self._candado = threading.RLock()
        
        # Cargar los datos existentes (o crear estructura vacía si no existe)
        self._datos = self._cargar()
    
    # ------------------------------------------------------- Método _cargar
    def _cargar(self) -> dict[str, Any]:
        """Cargar los datos desde el archivo JSON.
        
        Flujo:
        1. Asegurar que el directorio padre existe (mkdir padres si necesario)
        2. Si el archivo no existe, crear estructura vacía con siguiente_id=1 y productos=[]
        3. Si existe, leer y parsear el JSON
        4. Validar que tenga la estructura esperada (dict con 'productos' lista)
        5. Calcular el siguiente ID disponible basado en los existentes
        5. Retornar el diccionario de datos cargados
        
        Returns:
            Diccionario {"siguiente_id": int, "productos": list} listo para usar
        """
        # Paso 1: Garantizar que el directorio padre existe
        # Si la ruta es api/data/productos.json, asegurarse de que existe api/data/
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        
        # Paso 2: Si el archivo no existe, crear estructura por defecto
        if not self._ruta.exists():
            # Crear estructura vacía: un producto inicial con id=1 y siguiente_id=1
            datos: dict[str, Any] = {"siguiente_id": 1, "productos": []}
            # Guardar esta estructura vacía (escritura atómica)
            self._guardar(datos)
            return datos
        
        # Paso 3: Si el archivo existe, leer su contenido
        try:
            with self._ruta.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)  # Parsear JSON a objeto Python
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Si el archivo está corrupto o tiene encoding error, reiniciar vacío
            datos = {"siguiente_id": 1, "productos": []}
            self._guardar(datos)  # Sobrescribir con estructura válida
            return datos
        except Exception:
            # Cualquier otro error, reiniciar vacío
            datos = {"siguiente_id": 1, "productos": []}
            self._guardar(datos)
            return datos
        
        # Paso 4: Validar estructura básica
        # El JSON debe ser un dict y tener la clave "productos" que sea lista
        if not isinstance(datos, dict) or not isinstance(datos.get("productos"), list):
            raise ValueError("El archivo de productos tiene un formato inválido.")
        
        # Paso 5: Calcular el siguiente ID disponible
        # Tomar el máximo ID existente entre todos los productos y sumar 1
        # Si la lista está vacía, el máximo es 0, entonces siguiente_id = 1
        maximo = max((p.get("id", 0) for p in datos["productos"]), default=0)
        datos.setdefault("siguiente_id", maximo + 1)
        
        # Retornar los datos cargados y validados
        return datos
    
    # ------------------------------------------------------- Método _guardar
    def _guardar(self, datos: dict[str, Any]) -> None:
        """Guardar los datos al archivo JSON de forma atómica.
        
        Este es el método más importante para la integridad de los datos. El proceso:
        1. Escribir los datos en un archivo temporal (.tmp)
        2. Cerrar y flush el archivo temporal
        3. Usar os.replace() para reemplazar el archivo original con el temporal
        
        Por qué es atómica: os.replace() es una operación a nivel de sistema de archivos
        que es atómica en la mayoría de los SO: o el archivo viejo sigue existiendo,
        o el nuevo reemplaza el viejo, nunca se queda en un estado medio corrupto.
        
        Además, si el proceso se corta en medio, el archivo original sigue intacto
        porque el temporal no se movió todavía.
        
        Args:
            datos: Diccionario con la estructura {"siguiente_id": int, "productos": list}
        """
        # Crear un nombre de archivo temporal añadiendo .tmp a la extensión actual
        temporal = self._ruta.with_suffix(".tmp")
        
        try:
            # Escribir los datos en el archivo temporal
            with temporal.open("w", encoding="utf-8") as archivo:
                # Serializar a JSON con ensure_ascii=False para acentos/ñ correctos
                # indent=2 para formateo legible, y add un newline al final
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
                archivo.write("\n")
            
            # Reemplazar el archivo original con el temporal de forma atómica
            # Esto es casi instantáneo y no deja estado medio
            os.replace(temporal, self._ruta)
        except Exception:
            # Si falla cualquier cosa durante el guardar, es mejor que fallen los datos
            # que dejen el archivo corrupto. El error será propagado al llamante.
            raise
    
    # ------------------------------------------------------- Método listar
    def listar(self) -> list[dict[str, Any]]:
        """Retornar una copia profunda de todos los productos.
        
        Usa copy.deepcopy para retornar una copia completa del arreglo de productos,
        nunca la referencia directa. Esto protege el repositorio de que el cliente
        modifique sus datos internos a través de la referencia devuelta.
        
        Returns:
            Lista profunda de diccionarios de productos
        """
        # Adquirir el candado para thread-safety mientras se lee el estado
        with self._candado:
            # Retornar deep copy de la lista de productos
            return copy.deepcopy(self._datos["productos"])
    
    # ------------------------------------------------------- Método obtener
    def obtener(self, producto_id: int) -> dict[str, Any] | None:
        """Buscar y retornar un producto específico por su ID.
        
        Flujo:
        1. Adquirir candado para thread-safety
        2. Recorrer la lista de productos buscando coincidencia por ID
        3. Si encontrado, retornar deep copy del producto
        4. Si no encontrado, retornar None
        
        Args:
            producto_id: Entero identificador único del producto
            
        Returns:
            Diccionario deep copy del producto si existe, None si no se encontró
        """
        # Adquirir el lock mientras se busca
        with self._candado:
            # Recorrer todos los productos de la lista
            for producto in self._datos["productos"]:
                # Si el ID coincide, retornar deep copy
                if producto.get("id") == producto_id:
                    return copy.deepcopy(producto)
            
            # Si el bucle termina sin encontrar, retornar None
            return None
    
    # ------------------------------------------------------- Método nombre_existe
    def nombre_existe(self, nombre: str, excepto_id: int | None = None) -> bool:
        """Verificar si ya existe un producto con ese nombre en el catálogo.
        
        Esta función es llamada antes de crear o actualizar un producto para
        evitar nombres duplicados. La comparación es sin distinguir mayúsculas/minúsculas
        y ignora espacios extra al inicio/final.
        
        Args:
            nombre: El nombre a verificar (ya debería estar limpio/validado)
            excepto_id: ID opcional para excluir al producto actual de la verificación
                       (usado al actualizar para no flaggear que el nombre es el mismo)
            
        Returns:
            True si ya existe un producto con ese nombre, False si es único
        """
        # Adquirir lock para consistencia durante la verificación
        with self._candado:
            # Recorrer todos los productos
            for producto in self._datos["productos"]:
                # Si se especificó un ID para excluir (caso de actualización),
                # saltarse ese producto en la verificación
                if producto.get("id") == excepto_id:
                    continue  # Skip this product, it's the one being updated
                
                # Comparar nombres normalizados (strip + casefold para Unicode apoyo)
                # .strip() quita espacios, .casefold() es más robusto que .lower() para Unicode
                if str(producto.get("nombre", "")).strip().casefold() == nombre.strip().casefold():
                    return True  # Ya existe un producto con ese nombre
            
            # Si recorrió todos y no encontró ninguno, retornar False
            return False
    
    # ------------------------------------------------------- Método crear
    def crear(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Crear un nuevo producto y guardar en el repositorio.
        
        Flujo:
        1. Asignar un nuevo ID único usando siguiente_id
        2. Agregar marcas de tiempo (created_en y updated_en en ISO format)
        3. Agregar el nuevo producto a la lista
        4. Incrementar siguiente_id para el próximo producto
        5. Guardar todo el estado en el archivo JSON (escritura atómica)
        6. Retornar deep copy del producto creado
        
        Args:
            datos: Diccionario con los campos del producto (nombre, descripcion, precio, stock, categoria)
                   Sin incluir "id", "created_en", "updated_en" (estos los asigna el repositorio)
            
        Returns:
            Deep copy del producto creado con todos sus campos incluidos
        """
        # Adquirir lock para operaciones concurrentes seguras
        with self._candado:
            # Paso 1: Asignar el próximo ID disponible
            nuevo_id = self._datos["siguiente_id"]
            
            # Paso 2: Agregar marcas de tiempo al producto
            # created_en: cuándo se creó (fecha ISO en UTC)
            # updated_en: cuándo fue actualizado por última vez (mismo momento al crear)
            tiempo_actual = _ahora()
            
            # Paso 3: Construir el nuevo producto completo
            # El ID se asigna, los timestamps se agregan, y los datos van junto
            producto = {
                "id": int(nuevo_id),  # Asegurar que sea int
                **datos,  # Esparcir todos los datos venidos (nombre, precio, etc.)
                "creado_en": tiempo_actual,
                "actualizado_en": tiempo_actual,
            }
            
            # Paso 4: Agregar a la lista de productos
            self._datos["productos"].append(producto)
            
            # Paso 5: Incrementar el contador para el próximo producto
            self._datos["siguiente_id"] = nuevo_id + 1
            
            # Paso 6: Guardar todo el estado en archivo JSON (atómico)
            self._guardar(self._datos)
            
            # Paso 7: Retornar deep copy del producto creado
            return copy.deepcopy(producto)
    
    # ------------------------------------------------------- Método actualizar
    def actualizar(self, producto_id: int, datos: dict[str, Any]) -> dict[str, Any] | None:
        """Actualizar un producto existente en el repositorio.
        
        Flujo:
        1. Buscar el producto en la lista por ID
        2. Si no existe, retornar None
        3. Actualizar los campos del producto con los nuevos datos
        4. Mantener el ID, created_en (original), actualizar updated_en a ahora
        5. Guardar el estado en archivo JSON
        6. Retornar deep copy del producto actualizado
        
        Args:
            producto_id: ID entero del producto a actualizar
            datos: Diccionario con los campos a actualizar (solo los que se cambiarán)
            
        Returns:
            Deep copy del producto actualizado, o None si no se encontró
            
        Raises:
            Este método asume que la validación ya se hizo en el servicio (producto existe)
        """
        # Adquirir lock para consistencia
        with self._candado:
            # Recorrer la lista para encontrar el producto por ID
            for indice, producto in enumerate(self._datos["productos"]):
                # Si encontramos el producto con el ID correcto
                if producto.get("id") == producto_id:
                    # Actualizar los campos: los datos venidos reemplazan los campos existentes
                    # Pero mantener el ID original y created_en original
                    actualizado = {
                        **producto,        # Todos los campos actuales del producto
                        **datos,         # Los nuevos valores sobrestescriben los actuales
                        "id": producto_id,  # Asegurar que el ID se mantenga igual
                        "creado_en": producto.get("creado_en", _ahora()),  # Mantener creado_en
                        "actualizado_en": _ahora(),  # Actualizar a la fecha actual
                    }
                    
                    # Reemplazar el producto en la posición actual de la lista
                    self._datos["productos"][indice] = actualizado
                    
                    # Guardar el estado actualizado en archivo JSON
                    self._guardar(self._datos)
                    
                    # Retornar deep copy para protección
                    return copy.deepcopy(actualizado)
            
            # Si el bucle termina sin encontrar el producto, retornar None
            return None
    
    # ------------------------------------------------------- Método eliminar
    def eliminar(self, producto_id: int) -> bool:
        """Eliminar un producto del repositorio y del archivo JSON.
        
        Flujo:
        1. Adquirir lock
        2. Buscar el producto en la lista
        3. Si lo encuentra, quitarlo de la lista con pop(indice)
        4. Guardar el estado actualizado en archivo JSON
        5. Retornar True para indicar éxito
        
        Si no encuentra el producto, simplemente retorna False (aunque el servicio
        válida antes y lanza ApiError 404).
        
        Args:
            producto_id: ID entero del producto a eliminar
            
        Returns:
            True si se eliminó correctamente, False si no se encontró
        """
        # Adquirir lock para operación segura
        with self._candado:
            # Recorrer la lista con enumerate para tener tanto el índice como el producto
            for indice, producto in enumerate(self._datos["productos"]):
                # Si encontramos el producto con el ID correcto
                if producto.get("id") == producto_id:
                    # Eliminarlo de la lista usando pop con el índice
                    self._datos["productos"].pop(indice)
                    
                    # Guardar el estado actualizado en archivo JSON
                    self._guardar(self._datos)
                    
                    # Retornar True para indicar éxito
                    return True
            
            # Si el bucle termina sin encontrar el producto, retornar False
            return False