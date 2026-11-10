"""================================================================================
   PAQUETE CONTROLADORES (INIT.PY)
   Archivo: api/controladores/__init__.py
   Propósito: Marcador de paquete. Agrupa los controladores (auth.py, productos.py)
              para que sean importables como "from api.controladores import auth" etc.
================================================================================ """

# Este archivo vacío agrupa los módulos de controladores del paquete.
# Permite imports relativos e absolutos desde el paquete api.controladores:
# - from api.controladores import auth
# - from api.controladores import productos
# - from api.controladores.auth import login
# - from api.controladores.productos import listar, crear, etc.