"""================================================================================
   PAQUETE SERVICIOS (INIT.PY)
   Archivo: api/servicios/__init__.py
   Propósito: Marcador de paquete que agrupa los módulos de servicios (auth.py, productos.py)
              Permite imports como "from api.servicios import auth, productos"
================================================================================ """

# Este archivo vacío agrupa los módulos de servicios del paquete.
# Permite imports relativos e absolutos desde el paquete api.servicios:
# - from api.servicios import auth
# - from api.servicios import productos
# - from api.servicios.auth import AuthServicio, login
# - from api.servicios.productos import ProductoServicio, _precio, _stock, etc.