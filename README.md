# Catálogo de productos · API REST + formulario CRUD

Actividad práctica del Módulo 3. Incluye una **API REST** para el catálogo de productos y un **formulario web** sencillo para administrarlo.

🟢 **Desplegado en la nube:** https://catalogo-productos-6xh7.onrender.com

El backend está hecho con Python y la biblioteca estándar, así que **no requiere instalar dependencias**. Los datos se guardan en un archivo JSON.

---

## Cómo ejecutar

Requisito: Python 3.10 o superior.

```powershell
py run.py
```

También funciona con `python run.py`. Luego abre:

**http://localhost:8000**

Credenciales de demostración:

| Correo | Contraseña |
| --- | --- |
| `admin@catalogo.com` | `admin123` |

Si el puerto 8000 está ocupado:

```powershell
$env:PORT=8001; py run.py
```

> **Nota:** En Render el servicio puede tardar 30–60 segundos en responder la primera vez si está dormido. La URL pública es `https://catalogo-productos-6xh7.onrender.com`.

---

## Funcionalidades

- **CRUD completo** de productos con búsqueda en el listado.
- **Login con JWT** (HS256) para las rutas protegidas.
- **CORS** habilitado, con respuesta al preflight `OPTIONS`.
- **Validación** de nombre, descripción, precio, stock y categoría.
- **Códigos HTTP** correctos: `200`, `201`, `204`, `400`, `401`, `404`, `405`, `409`, `413` y `500`.
- **Estructura por capas**: rutas → controladores → servicios → repositorios.
- **Persistencia** en `api/data/productos.json` con escritura atómica.
- **Interfaz responsive** con estados vacíos, avisos y confirmación de borrado.

---

## Endpoints

| Método | Ruta | Acceso | Respuesta correcta |
| --- | --- | --- | --- |
| `POST` | `/api/auth/login` | Pública | `200` + token JWT |
| `GET` | `/api/productos` | Pública | `200` + listado |
| `GET` | `/api/productos/:id` | Pública | `200` + producto |
| `POST` | `/api/productos` | JWT | `201` + `Location` |
| `PUT` | `/api/productos/:id` | JWT | `200` + producto actualizado |
| `DELETE` | `/api/productos/:id` | JWT | `204` sin cuerpo |
| `GET` | `/api/salud` | Pública | `200` (verificación del servicio) |

Las rutas protegidas necesitan la cabecera:

```http
Authorization: Bearer <token>
```

### Ejemplo rápido

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/auth/login `
  -ContentType "application/json" `
  -Body '{"email":"admin@catalogo.com","password":"admin123"}'

$headers = @{ Authorization = "Bearer $($login.token)" }

Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/productos `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"nombre":"Mouse inalámbrico","descripcion":"Mouse óptico USB","precio":15.90,"stock":10,"categoria":"Electrónica"}'
```

---

## Estructura del proyecto

```text
.
├── run.py                       # Punto de entrada
├── api/
│   ├── app.py                   # Servidor HTTP, CORS y archivos estáticos
│   ├── rutas.py                 # Tabla de rutas y resolución de parámetros
│   ├── config.py                # Configuración y variables de entorno
│   ├── seguridad.py             # Creación y verificación de JWT
│   ├── errores.py               # Errores de negocio → códigos HTTP
│   ├── respuestas.py            # Respuestas de los controladores
│   ├── controladores/           # Adaptan HTTP a los servicios
│   ├── servicios/               # Reglas de negocio y validaciones
│   ├── repositorios/            # Acceso y persistencia de datos
│   └── data/productos.json      # Datos del catálogo
├── frontend/
│   ├── index.html               # Formulario CRUD
│   ├── styles.css               # Diseño responsive
│   ├── app.js                   # Consumo de la API
│   └── favicon.svg
├── pruebas/
│   ├── postman_collection.json  # Colección de Postman
│   ├── api.http                 # Pruebas con VS Code REST Client
│   └── probar_api.py            # Pruebas automáticas de humo
└── README.md
```

### Capas

- **Rutas / presentación:** `api/rutas.py` y `api/app.py`. Reciben la petición, aplican CORS y autenticación, y devuelven JSON.
- **Controladores:** `api/controladores/`. Traducen la petición HTTP a llamadas al servicio y eligen el código de respuesta.
- **Servicios:** `api/servicios/`. Contienen la validación y las reglas de negocio (por ejemplo, nombre duplicado).
- **Repositorios:** `api/repositorios/`. Solo se encargan de leer y escribir los datos.

---

## Pruebas

Con el servidor en ejecución:

### Opción 1 · Script automático

```powershell
py pruebas/probar_api.py
```

Comprueba login, CRUD, validaciones, `401`, `404`, `405`, `409`, CORS y limpieza del producto de prueba.

### Opción 2 · Colección de Postman

1. Importa `pruebas/postman_collection.json`.
2. Verifica que la variable `base_url` sea `http://localhost:8000`.
3. Ejecuta la colección con **Run collection** (el orden importa).

El login guarda el token automáticamente y el producto de prueba se elimina al final.

### Opción 3 · VS Code REST Client

Abre `pruebas/api.http` y ejecuta las peticiones en orden. El login y la creación guardan su respuesta para reutilizar automáticamente el token y el id del producto.

---

## Autenticación

- Algoritmo: **HS256**.
- Vigencia del token: **1 hora** (configurable).
- El token se genera en `POST /api/auth/login` y se valida en las rutas protegidas.
- Sin token o con token inválido/expirado: `401` + `WWW-Authenticate: Bearer`.

Este proyecto es una demostración académica. Para producción habría que usar una base de datos real, contraseñas con hash, HTTPS y una clave JWT secreta robusta.

---

## Variables de entorno

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Dirección del servidor |
| `PORT` | `8000` | Puerto |
| `JWT_SECRET` | clave de desarrollo | Firma de los tokens |
| `JWT_TTL_SEGUNDOS` | `3600` | Vigencia del token |
| `ADMIN_EMAIL` | `admin@catalogo.com` | Usuario demo |
| `ADMIN_PASSWORD` | `admin123` | Contraseña demo |
| `ADMIN_NOMBRE` | `Administrador` | Nombre mostrado en el panel |

Ejemplo:

```powershell
$env:JWT_SECRET="una-clave-larga-y-secreta"; $env:PORT=8001; py run.py
```

---

## Notas

- Los cambios se guardan en `api/data/productos.json`; puedes editar ese archivo para reiniciar el catálogo.
- El formulario y la API se sirven desde el mismo origen, pero CORS está habilitado para que puedas probar la API desde Postman, REST Client u otro puerto.
- Códigos de error habituales:
  - `400`: datos inválidos o JSON mal formado.
  - `401`: falta el JWT, es inválido o expiró.
  - `404`: producto o ruta inexistente.
  - `405`: método no permitido para la ruta.
  - `409`: nombre de producto duplicado.
