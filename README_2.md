# README 2 · Catálogo de productos: explicación completa, Git y despliegue en Render

> Documento de apoyo para la exposición del proyecto.
> Explica **qué se construyó**, **cómo funciona**, **cómo se prueba**, **cómo se sube a Git** y **cómo se despliega en Render**, además de las preguntas que suele hacer el profesor.

---

## Índice

1. [Resumen del proyecto](#1-resumen-del-proyecto)
2. [Requisitos de la actividad y cómo se cumplen](#2-requisitos-de-la-actividad-y-cómo-se-cumplen)
3. [Tecnologías utilizadas](#3-tecnologías-utilizadas)
4. [Arquitectura por capas](#4-arquitectura-por-capas)
5. [Estructura de archivos](#5-estructura-de-archivos)
6. [Ejecución local paso a paso](#6-ejecución-local-paso-a-paso)
7. [Configuración y variables de entorno](#7-configuración-y-variables-de-entorno)
8. [Endpoints de la API](#8-endpoints-de-la-api)
9. [Autenticación con JWT](#9-autenticación-con-jwt)
10. [CORS explicado](#10-cors-explicado)
11. [Validaciones y códigos HTTP](#11-validaciones-y-códigos-http)
12. [Persistencia de datos](#12-persistencia-de-datos)
13. [Pruebas](#13-pruebas)
14. [Git paso a paso](#14-git-paso-a-paso)
15. [Publicación en GitHub](#15-publicación-en-github)
16. [Despliegue en Render](#16-despliegue-en-render)
17. [Verificación después del despliegue](#17-verificación-después-del-despliegue)
18. [Actualizaciones, ramas y rollback](#18-actualizaciones-ramas-y-rollback)
19. [Problemas frecuentes y soluciones](#19-problemas-frecuentes-y-soluciones)
20. [Limitaciones y mejoras para producción](#20-limitaciones-y-mejoras-para-producción)
21. [Guion para la exposición](#21-guion-para-la-exposición)
22. [Preguntas probables del profesor (con respuestas)](#22-preguntas-probables-del-profesor-con-respuestas)
23. [Glosario](#23-glosario)
24. [Chuleta de comandos](#24-chuleta-de-comandos)
25. [Checklist final](#25-checklist-final)

---

## 1. Resumen del proyecto

Este proyecto es una **aplicación web con API REST** para administrar un catálogo de productos. Permite:

- Iniciar sesión con correo y contraseña.
- Consultar todos los productos.
- Buscar productos por nombre, descripción o categoría.
- Crear productos.
- Editar productos.
- Eliminar productos con confirmación.
- Ver estadísticas básicas: cantidad de productos, unidades en stock y valor del inventario.

Tiene dos partes que se sirven desde **el mismo servidor**:

| Parte | Qué es | Dónde está |
| --- | --- | --- |
| Backend / API | Recibe peticiones HTTP, valida datos, autentica con JWT y guarda en JSON | `api/` |
| Frontend | Página web que consume la API y muestra el formulario CRUD | `frontend/` |

El backend usa **solo la biblioteca estándar de Python**. No necesita Flask, Django, FastAPI ni paquetes externos. Esto simplifica la instalación y el despliegue.

### URLs locales

- Formulario: `http://localhost:8000`
- API: `http://localhost:8000/api/productos`
- Salud del servicio: `http://localhost:8000/api/salud`

### Credenciales de demostración locales

| Correo | Contraseña |
| --- | --- |
| `admin@catalogo.com` | `admin123` |

> En Render se pueden conservar estas credenciales para la demostración o cambiarlas con las variables `ADMIN_EMAIL` y `ADMIN_PASSWORD`. Para un sitio público real, cámbialas.

---

## 2. Requisitos de la actividad y cómo se cumplen

| Requisito | Dónde se cumple | Explicación breve |
| --- | --- | --- |
| CRUD completo | `api/controladores/productos.py` | Crear, listar, obtener, actualizar y eliminar. |
| API REST | `api/rutas.py` | Rutas con sustantivos y métodos HTTP estándar. |
| JWT | `api/seguridad.py` | Token firmado con HS256 y fecha de expiración. |
| CORS | `api/app.py` | Cabeceras CORS y respuesta a `OPTIONS`. |
| Validaciones | `api/servicios/productos.py` | Reglas de nombre, precio, stock y categoría. |
| Códigos HTTP correctos | `api/errores.py` y controladores | `200`, `201`, `204`, `400`, `401`, `404`, `405`, `409`, `413`, `500`. |
| Estructura por capas | `api/rutas.py` → `controladores` → `servicios` → `repositorios` | Cada capa tiene una responsabilidad. |
| Base de datos o persistencia | `api/repositorios/productos.py` | Persistencia en `api/data/productos.json` con escritura atómica. |
| Pruebas | `pruebas/` | Script automático, colección de Postman y archivo `api.http`. |
| Frontend funcional | `frontend/` | Login, tabla, búsqueda, formulario y confirmación de borrado. |
| Documentación | `README.md` y este `README_2.md` | Ejecución, endpoints, despliegue y preguntas. |
| Despliegue en la nube | Render | Servicio web gratuito con URL pública. |

---

## 3. Tecnologías utilizadas

| Tecnología | Uso |
| --- | --- |
| **Python 3.10+** | Lenguaje del backend. |
| **`http.server` / `ThreadingHTTPServer`** | Servidor HTTP sin frameworks. |
| **`hmac`, `hashlib`, `base64`, `json`** | Creación y verificación de JWT HS256. |
| **HTML5** | Estructura del formulario. |
| **CSS3** | Diseño responsive, tarjetas, tabla y diálogo de confirmación. |
| **JavaScript moderno** | Consumo de la API con `fetch`, renderizado y validación en el navegador. |
| **JSON** | Formato de intercambio y persistencia. |
| **Git** | Control de versiones. |
| **GitHub** | Repositorio remoto. |
| **Render** | Plataforma de despliegue en la nube. |

### ¿Por qué no se usó Flask, Django o FastAPI?

Porque la actividad permite implementar el servidor con la biblioteca estándar y así se demuestra el funcionamiento interno de HTTP, el enrutamiento, CORS y JWT sin ocultarlo detrás de un framework. Además, el despliegue queda más simple: no hay dependencias que instalar.

> En un proyecto real, usar Flask/FastAPI/Django sería más cómodo y seguro. Aquí la prioridad es **entender** el proceso.

---

## 4. Arquitectura por capas

El backend sigue un flujo de cuatro capas:

```text
Navegador / Postman
        │
        ▼
┌──────────────────────────────┐
│  Rutas y servidor HTTP       │  api/rutas.py · api/app.py
│  - Recibe la petición        │
│  - Aplica CORS               │
│  - Valida el JWT             │
│  - Sirve archivos estáticos  │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Controladores               │  api/controladores/
│  - Traducen HTTP a servicio  │
│  - Eligen el código HTTP     │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Servicios                   │  api/servicios/
│  - Reglas de negocio         │
│  - Validaciones              │
│  - Nombre duplicado          │
└──────────────┬───────────────┘
               ▼
┌──────────────────────────────┐
│  Repositorios                │  api/repositorios/
│  - Leen y escriben el JSON   │
│  - Candado y escritura atómica│
└──────────────────────────────┘
```

### Responsabilidad de cada capa

| Capa | Archivos | Responsabilidad | No debería hacer |
| --- | --- | --- | --- |
| Servidor / rutas | `api/app.py`, `api/rutas.py` | Recibir HTTP, CORS, autenticación, enrutar, servir estáticos | Reglas de negocio |
| Controladores | `api/controladores/*.py` | Adaptar la petición y elegir la respuesta HTTP | Validar precios o escribir archivos |
| Servicios | `api/servicios/*.py` | Validar y aplicar reglas del catálogo | Saber de HTTP o de archivos |
| Repositorios | `api/repositorios/*.py` | Persistir y recuperar datos | Validar nombres o precios |

### Flujo de una petición `POST /api/productos`

1. `api/app.py` recibe la petición.
2. `api/rutas.py` busca la ruta `POST /api/productos`.
3. Como la ruta requiere autenticación, `api/seguridad.py` valida el encabezado `Authorization: Bearer <token>`.
4. Se lee y parsea el cuerpo JSON.
5. `api/controladores/productos.py` llama al servicio.
6. `api/servicios/productos.py` valida los datos y comprueba que el nombre no exista.
7. `api/repositorios/productos.py` asigna un id, guarda en JSON y devuelve el producto.
8. El controlador responde `201 Created` con la cabecera `Location`.

---

## 5. Estructura de archivos

```text
Taller de harlinton/
├── run.py                        # Punto de entrada: py run.py
├── requirements.txt              # Sin dependencias externas (lo usa Render)
├── render.yaml                   # Blueprint de despliegue en Render
├── .python-version               # Versión de Python para Render (3.12.8)
├── .gitignore                    # Archivos que no se suben a Git
├── Abrir catalogo.bat            # Lanzador para Windows
├── README.md                     # Documentación breve
├── README_2.md                   # Esta guía detallada
├── api/
│   ├── __init__.py
│   ├── app.py                    # Servidor HTTP, CORS, estáticos y errores
│   ├── config.py                 # Variables de entorno y rutas
│   ├── errores.py                # ApiError → respuesta HTTP
│   ├── respuestas.py             # Constructores ok/creado/sin_contenido
│   ├── rutas.py                  # Tabla de rutas y parámetros
│   ├── seguridad.py              # JWT HS256
│   ├── controladores/
│   │   ├── __init__.py
│   │   ├── auth.py               # Login
│   │   └── productos.py          # CRUD y salud
│   ├── servicios/
│   │   ├── __init__.py
│   │   ├── auth.py               # Validación de credenciales
│   │   └── productos.py          # Validaciones y reglas
│   ├── repositorios/
│   │   ├── __init__.py
│   │   └── productos.py          # Persistencia JSON
│   └── data/
│       └── productos.json        # Datos del catálogo
├── frontend/
│   ├── index.html                # Estructura y formularios
│   ├── styles.css                # Diseño responsive
│   ├── app.js                    # Login, fetch, CRUD y avisos
│   └── favicon.svg
└── pruebas/
    ├── probar_api.py             # 22 comprobaciones automáticas
    ├── postman_collection.json   # Colección de Postman
    └── api.http                  # VS Code REST Client
```

### Archivos nuevos para el despliegue

| Archivo | Para qué sirve |
| --- | --- |
| `requirements.txt` | Render ejecuta `pip install -r requirements.txt`. Está vacío de dependencias porque todo es biblioteca estándar. |
| `render.yaml` | Describe el servicio web: comando de build, comando de inicio, health check y variables. |
| `.python-version` | Indica la versión de Python que debe usar Render (`3.12.8`). |

---

## 6. Ejecución local paso a paso

### Requisito

- Python 3.10 o superior.
- Comprobar la versión:

```powershell
py --version
```

Si `py` no funciona en Windows, prueba:

```powershell
python --version
```

### Opción A: desde la terminal

```powershell
cd "C:\Users\Usuario\Downloads\Taller de harlinton"
py run.py
```

Luego abre en el navegador:

```text
http://localhost:8000
```

Para detener el servidor: `Ctrl + C`.

### Opción B: doble clic

Abre `Abrir catalogo.bat`. El archivo inicia el servidor y abre el navegador automáticamente.

### Si el puerto 8000 está ocupado

```powershell
$env:PORT=8001
py run.py
```

Y abre `http://localhost:8001`.

### Qué debe verse

1. Pantalla de inicio de sesión.
2. Al entrar con `admin@catalogo.com` / `admin123`, aparece el panel.
3. Tabla con productos de ejemplo.
4. Formulario para crear un producto.
5. Botones **Editar** y **Eliminar** en cada fila.

### Flujo de prueba manual

1. Inicia sesión con las credenciales demo.
2. Crea un producto con nombre, precio, stock y categoría.
3. Verifica que aparezca en la tabla y en las estadísticas.
4. Edita el producto y guarda.
5. Busca por nombre o categoría.
6. Elimina el producto y confirma.
7. Prueba un precio negativo o un stock vacío para ver las validaciones.
8. Cierra sesión y comprueba que vuelve al login.

---

## 7. Configuración y variables de entorno

La configuración está en `api/config.py`. Se lee con `os.getenv`, por lo que funciona igual en local y en Render.

| Variable | Valor por defecto | Uso |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Dirección en la que escucha el servidor. En Render debe ser `0.0.0.0`. |
| `PORT` | `8000` | Puerto. Render lo asigna automáticamente; no lo fijes en el panel. |
| `JWT_SECRET` | Clave de desarrollo | Secreto para firmar los tokens. En Render debe ser largo y aleatorio. |
| `JWT_TTL_SEGUNDOS` | `3600` | Vigencia del token en segundos (1 hora). |
| `ADMIN_EMAIL` | `admin@catalogo.com` | Correo del administrador. |
| `ADMIN_PASSWORD` | `admin123` | Contraseña del administrador. |
| `ADMIN_NOMBRE` | `Administrador` | Nombre que se muestra en el panel. |

### Ejemplo local con variables

PowerShell:

```powershell
$env:HOST="127.0.0.1"
$env:PORT="8001"
$env:JWT_SECRET="una-clave-larga-y-secreta-para-desarrollo"
$env:ADMIN_EMAIL="admin@catalogo.com"
$env:ADMIN_PASSWORD="admin123"
py run.py
```

Bash / macOS / Linux:

```bash
HOST=127.0.0.1 PORT=8001 JWT_SECRET="una-clave-larga" python3 run.py
```

> El proyecto **no** carga archivos `.env` automáticamente. En local se usan variables de la terminal; en Render se configuran en el panel. No subas secretos a Git.

### Generar un `JWT_SECRET` seguro

PowerShell:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Bash:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

OpenSSL:

```bash
openssl rand -base64 48
```

Copia el resultado y pégalo en la variable `JWT_SECRET` de Render.

---

## 8. Endpoints de la API

URL base local: `http://localhost:8000`
URL base en Render: `https://TU-SERVICIO.onrender.com`

| Método | Ruta | Acceso | Éxito | Descripción |
| --- | --- | --- | --- | --- |
| `POST` | `/api/auth/login` | Público | `200` | Devuelve un token JWT. |
| `GET` | `/api/productos` | Público | `200` | Lista todos los productos. |
| `GET` | `/api/productos/:id` | Público | `200` | Obtiene un producto por id. |
| `POST` | `/api/productos` | JWT | `201` | Crea un producto. Devuelve `Location`. |
| `PUT` | `/api/productos/:id` | JWT | `200` | Actualiza un producto completo. |
| `DELETE` | `/api/productos/:id` | JWT | `204` | Elimina un producto. Sin cuerpo. |
| `GET` | `/api/salud` | Público | `200` | Verifica que el servicio esté vivo. |

### 8.1 Login

```http
POST /api/auth/login
Content-Type: application/json
```

```json
{
  "email": "admin@catalogo.com",
  "password": "admin123"
}
```

Respuesta `200`:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tipo": "Bearer",
  "expira_en": 3600,
  "usuario": {
    "email": "admin@catalogo.com",
    "nombre": "Administrador"
  }
}
```

### 8.2 Listar productos

```http
GET /api/productos
```

Respuesta `200`:

```json
{
  "total": 4,
  "productos": [
    {
      "id": 1,
      "nombre": "Audífonos inalámbricos",
      "descripcion": "Bluetooth 5.3, estuche de carga y hasta 24 horas de batería.",
      "precio": 59.9,
      "stock": 25,
      "categoria": "Electrónica",
      "creado_en": "2026-01-15T10:00:00Z",
      "actualizado_en": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### 8.3 Obtener un producto

```http
GET /api/productos/1
```

Respuesta `200`:

```json
{
  "producto": {
    "id": 1,
    "nombre": "Audífonos inalámbricos",
    "precio": 59.9,
    "stock": 25,
    "categoria": "Electrónica"
  }
}
```

Si no existe: `404` con `{"error": "Producto no encontrado."}`.

### 8.4 Crear producto

```http
POST /api/productos
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "nombre": "Mouse inalámbrico",
  "descripcion": "Mouse óptico USB con receptor nano.",
  "precio": 15.9,
  "stock": 10,
  "categoria": "Electrónica"
}
```

Respuesta `201`:

```json
{
  "mensaje": "Producto creado.",
  "producto": {
    "id": 11,
    "nombre": "Mouse inalámbrico",
    "descripcion": "Mouse óptico USB con receptor nano.",
    "precio": 15.9,
    "stock": 10,
    "categoria": "Electrónica",
    "creado_en": "2026-11-09T12:00:00Z",
    "actualizado_en": "2026-11-09T12:00:00Z"
  }
}
```

Cabecera importante:

```http
Location: /api/productos/11
```

### 8.5 Actualizar producto

```http
PUT /api/productos/11
Authorization: Bearer <token>
Content-Type: application/json
```

```json
{
  "nombre": "Mouse inalámbrico",
  "descripcion": "Versión actualizada.",
  "precio": 19.99,
  "stock": 8,
  "categoria": "Electrónica"
}
```

Respuesta `200` con el producto actualizado. `PUT` reemplaza todos los campos editables, por eso se envían todos.

### 8.6 Eliminar producto

```http
DELETE /api/productos/11
Authorization: Bearer <token>
```

Respuesta `204 No Content`, sin cuerpo.

### 8.7 Salud del servicio

```http
GET /api/salud
```

```json
{
  "estado": "ok",
  "servicio": "catalogo-api"
}
```

Render usa esta ruta como **health check**.

### 8.8 Ejemplo completo con PowerShell

```powershell
$base = "http://localhost:8000"

$login = Invoke-RestMethod -Method Post `
  -Uri "$base/api/auth/login" `
  -ContentType "application/json" `
  -Body '{"email":"admin@catalogo.com","password":"admin123"}'

$headers = @{ Authorization = "Bearer $($login.token)" }

Invoke-RestMethod -Method Post `
  -Uri "$base/api/productos" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body '{"nombre":"Mouse inalámbrico","descripcion":"Mouse óptico USB","precio":15.90,"stock":10,"categoria":"Electrónica"}'
```

### 8.9 Ejemplo con `curl`

```bash
curl -X POST https://TU-SERVICIO.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@catalogo.com","password":"admin123"}'
```

```bash
curl -X POST https://TU-SERVICIO.onrender.com/api/productos \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Mouse","descripcion":"USB","precio":15.9,"stock":10,"categoria":"Electrónica"}'
```

---

## 9. Autenticación con JWT

### ¿Qué es un JWT?

Un **JWT** (JSON Web Token) es una cadena con tres partes separadas por puntos:

```text
header.payload.signature
```

Ejemplo:

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
.
eyJzdWIiOiJhZG1pbkBjYXRhbG9nby5jb20iLCJleHAiOjE3NjI3MDQwMDB9
.
firma-hmac-sha256
```

| Parte | Contenido en este proyecto |
| --- | --- |
| Header | `{"alg":"HS256","typ":"JWT"}` |
| Payload | `sub` (correo), `nombre`, `iss` (emisor), `iat` (emitido en), `exp` (expiración) |
| Signature | HMAC-SHA256 del header y payload usando `JWT_SECRET` |

### ¿Cómo se genera?

1. El usuario envía correo y contraseña a `POST /api/auth/login`.
2. `api/servicios/auth.py` compara las credenciales con `ADMIN_EMAIL` y `ADMIN_PASSWORD`.
3. Si coinciden, `api/seguridad.py` crea el header y el payload.
4. Codifica header y payload en Base64URL.
5. Firma `header.payload` con HMAC-SHA256 y el secreto.
6. Devuelve el token y su vigencia.

### ¿Cómo se valida?

En cada ruta protegida:

1. Se lee `Authorization: Bearer <token>`.
2. Se separa el token en sus tres partes.
3. Se recalcula la firma y se compara con `hmac.compare_digest`.
4. Se comprueba que el algoritmo sea `HS256`.
5. Se comprueba el emisor (`iss`).
6. Se comprueba que `exp` no haya pasado.
7. Se comprueba que exista `sub`.

Si algo falla: `401 Unauthorized` y cabecera `WWW-Authenticate: Bearer`.

### Preguntas clave sobre JWT

**¿El token está cifrado?**
No. Base64URL solo codifica; cualquiera puede leer el payload. Por eso no se guardan contraseñas ni datos sensibles dentro. La firma sirve para detectar alteraciones, no para ocultar información.

**¿Por qué HS256?**
Porque es simétrico: el mismo secreto firma y verifica. Es sencillo y adecuado para un servidor único. En sistemas con varios servicios se suele usar RS256 (clave pública/privada).

**¿Qué pasa si cambia `JWT_SECRET`?**
Todos los tokens anteriores dejan de ser válidos y los usuarios deben iniciar sesión otra vez.

**¿Dónde se guarda el token en el frontend?**
En `sessionStorage`, no en `localStorage`. Se borra al cerrar la pestaña y el código lo elimina al cerrar sesión o al detectar expiración.

**¿Por qué `hmac.compare_digest`?**
Para comparar en tiempo constante y reducir ataques de temporización.

**¿JWT es mejor que cookies de sesión?**
Depende. JWT es útil para APIs y clientes desacoplados. Las cookies `HttpOnly` protegen mejor contra XSS en aplicaciones web tradicionales. En este proyecto se usa JWT porque lo pide la actividad.

---

## 10. CORS explicado

**CORS** (Cross-Origin Resource Sharing) es un mecanismo del navegador que controla qué orígenes pueden llamar a una API.

### ¿Qué es un origen?

Es la combinación de **protocolo + dominio + puerto**. Por ejemplo:

- `http://localhost:8000` y `http://localhost:8001` son orígenes distintos.
- `https://mi-app.onrender.com` y `https://otra-app.onrender.com` son orígenes distintos.

### ¿Cómo se implementa aquí?

En `api/app.py`, el método `end_headers` agrega a **todas** las respuestas:

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

Además, `do_OPTIONS` responde `204` al **preflight**.

### ¿Qué es el preflight?

Antes de una petición `POST`, `PUT` o `DELETE` con `Content-Type: application/json` o `Authorization`, el navegador envía primero una petición `OPTIONS` para preguntar si está permitida. El servidor responde con las cabeceras CORS y el navegador decide si continúa.

### ¿Por qué `*`?

Porque es una demostración académica y permite probar desde Postman, VS Code REST Client, otro puerto o un frontend separado. En producción se recomienda restringirlo:

```http
Access-Control-Allow-Origin: https://mi-frontend.com
```

> `*` no permite cookies de sesión, pero sí permite que cualquier sitio llame a la API. Para un CRUD público no es crítico, pero es una buena práctica restringirlo.

---

## 11. Validaciones y códigos HTTP

### Reglas de validación del servicio

Se aplican en `api/servicios/productos.py`, no solo en el navegador. Esto es importante: **el frontend puede ser saltado con Postman o curl**, así que el backend siempre valida.

| Campo | Regla |
| --- | --- |
| `nombre` | Texto obligatorio, entre 2 y 80 caracteres, sin duplicados (comparación sin distinguir mayúsculas). |
| `descripcion` | Texto opcional, máximo 300 caracteres. Puede ir vacío. |
| `precio` | Número finito mayor que 0 y menor o igual a 99,999,999. Se redondea a 2 decimales. |
| `stock` | Entero mayor o igual a 0 y menor o igual a 1,000,000. No acepta decimales. |
| `categoria` | Texto obligatorio, entre 2 y 40 caracteres. |
| `id` | Entero mayor que 0. Si no es numérico: `400`. Si no existe: `404`. |

### Códigos HTTP usados

| Código | Cuándo se usa | Ejemplo |
| --- | --- | --- |
| `200 OK` | Petición exitosa con cuerpo | Listar, obtener, actualizar, login. |
| `201 Created` | Recurso creado | `POST /api/productos`. |
| `204 No Content` | Éxito sin cuerpo | `DELETE`, preflight `OPTIONS`. |
| `400 Bad Request` | Datos inválidos o JSON mal formado | Precio negativo, falta un campo, id no numérico. |
| `401 Unauthorized` | Falta token, token inválido, expirado o credenciales incorrectas | `POST` sin `Authorization`. |
| `404 Not Found` | Producto o ruta inexistente | `/api/productos/999999`. |
| `405 Method Not Allowed` | Método no permitido para una ruta | `POST /api/salud`. |
| `409 Conflict` | Nombre de producto duplicado | Crear dos veces el mismo nombre. |
| `413 Payload Too Large` | Cuerpo mayor a 1 MB | JSON gigante. |
| `500 Internal Server Error` | Error inesperado del servidor | Fallo de disco, excepción no controlada. |

### Formato de error

```json
{
  "error": "Revisa los datos del producto.",
  "detalles": {
    "nombre": "El nombre debe tener al menos 2 caracteres.",
    "precio": "El precio debe ser mayor que 0."
  }
}
```

El frontend muestra esos detalles junto a cada campo.

### Seguridad de la validación

- No se confía en la validación HTML5 (`required`, `min`, etc.).
- No se confía en la validación de JavaScript.
- El backend repite todas las reglas.
- El cuerpo máximo es de 1 MB para evitar abusos.
- Los errores inesperados no revelan la traza al cliente; solo se imprime en el servidor.

---

## 12. Persistencia de datos

### ¿Dónde se guardan los datos?

En `api/data/productos.json`, con esta forma:

```json
{
  "siguiente_id": 11,
  "productos": [
    {
      "id": 1,
      "nombre": "Audífonos inalámbricos",
      "descripcion": "Bluetooth 5.3...",
      "precio": 59.9,
      "stock": 25,
      "categoria": "Electrónica",
      "creado_en": "2026-01-15T10:00:00Z",
      "actualizado_en": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### ¿Cómo se escribe sin corromper el archivo?

`api/repositorios/productos.py` usa **escritura atómica**:

1. Escribe los datos en un archivo temporal `productos.tmp`.
2. Cierra el archivo.
3. Reemplaza `productos.json` con `os.replace`.
4. Si algo falla antes del reemplazo, el archivo original sigue intacto.

Además, usa un `threading.RLock` para que dos peticiones simultáneas no modifiquen el estado al mismo tiempo. El servidor es `ThreadingHTTPServer`, así que puede atender varias peticiones en paralelo.

### ¿Qué pasa si se borra `productos.json`?

El repositorio crea uno nuevo vacío con `siguiente_id: 1`. Para volver a los datos de ejemplo, restaura el archivo desde Git:

```powershell
git checkout -- api/data/productos.json
```

### Persistencia en Render (importante)

En el **plan free de Render**, el sistema de archivos es **efímero**:

- Los cambios se guardan mientras el servicio está despierto.
- Si el servicio se reinicia, se redespliega o se duerme por inactividad, el archivo vuelve a la versión del repositorio.
- Render free no incluye discos persistentes.

Para la demostración de la actividad es suficiente. Para producción real hay que usar una base de datos (PostgreSQL, MySQL, MongoDB) o un disco persistente de pago.

### ¿Por qué no SQLite?

Se podría usar SQLite, pero el sistema de archivos de Render free sigue siendo efímero: el archivo `.db` también se perdería al reiniciar. La solución real es una base de datos externa. Para el taller, JSON es simple y didáctico.

---

## 13. Pruebas

### 13.1 Script automático (22 comprobaciones)

Con el servidor local en ejecución:

```powershell
py run.py
```

En otra terminal:

```powershell
py pruebas/probar_api.py
```

El script comprueba:

1. `GET /api/salud` responde `200`.
2. El servicio se identifica como `catalogo-api`.
3. `GET /api/productos` responde `200`.
4. El listado tiene `productos` y `total`.
5. `POST` sin JWT responde `401`.
6. Login con contraseña incorrecta responde `401`.
7. Login válido responde `200`.
8. El login devuelve un JWT.
9. El preflight `OPTIONS` responde `204`.
10. CORS permite cualquier origen (`*`).
11. Un método no permitido responde `405`.
12. `POST` válido responde `201`.
13. `POST` incluye `Location`.
14. Nombre duplicado responde `409`.
15. Datos inválidos responden `400`.
16. `GET` por id responde `200`.
17. `GET` por id devuelve el producto correcto.
18. `PUT` responde `200`.
19. `PUT` persistió los cambios.
20. Producto inexistente responde `404`.
21. `DELETE` responde `204`.
22. El producto eliminado responde `404`.

Resultado esperado:

```text
Resultado: 22/22 pruebas correctas.
```

### 13.2 Postman

1. Abre Postman.
2. Importa `pruebas/postman_collection.json`.
3. Verifica la variable `base_url`:
   - Local: `http://localhost:8000`
   - Render: `https://TU-SERVICIO.onrender.com`
4. Ejecuta la colección con **Run collection**.
5. El login guarda el token y el producto de prueba se elimina al final.

### 13.3 VS Code REST Client

1. Instala la extensión **REST Client**.
2. Abre `pruebas/api.http`.
3. Ejecuta las peticiones en orden con **Send Request**.
4. El login y la creación guardan su respuesta para reutilizar token e id.

### 13.4 Pruebas manuales recomendadas

- Login correcto e incorrecto.
- Crear producto con todos los campos.
- Crear producto sin token (debe fallar).
- Crear producto con precio `0`, negativo o texto (debe fallar).
- Crear producto con stock negativo o decimal (debe fallar).
- Crear dos productos con el mismo nombre (debe dar `409`).
- Editar un producto y comprobar el cambio.
- Eliminar y comprobar que ya no aparece.
- Probar un id inexistente y uno no numérico.
- Probar `POST /api/salud` (debe dar `405`).

### 13.5 ¿Qué no cubren las pruebas?

Las pruebas de humo no son unitarias ni de carga. No comprueban concurrencia masiva, ataques de seguridad, navegadores específicos ni persistencia real en la nube. Para eso se necesitarían pruebas unitarias, de integración y de carga.

---

## 14. Git paso a paso

### ¿Qué es Git?

Git es un **sistema de control de versiones distribuido**. Guarda la historia de los cambios del proyecto en commits, permite volver atrás y trabajar en ramas.

### ¿Git y GitHub son lo mismo?

No.

- **Git** es la herramienta local que crea commits.
- **GitHub** es un servicio en la nube que aloja repositorios Git.

### 14.1 Verificar que Git está instalado

```powershell
git --version
```

Si no aparece, instala Git desde <https://git-scm.com/download/win>.

### 14.2 Configurar identidad

Se hace una vez. Puede ser global o solo para este repositorio:

```powershell
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"
```

Comprobar:

```powershell
git config --global --list
```

> Usa el mismo correo que tienes en GitHub para que los commits se vinculen a tu perfil. No es obligatorio, pero es recomendable.

### 14.3 Inicializar el repositorio

Dentro de la carpeta del proyecto:

```powershell
cd "C:\Users\Usuario\Downloads\Taller de harlinton"
git init
git branch -M main
```

- `git init` crea la carpeta oculta `.git`.
- `git branch -M main` renombra la rama principal a `main`, el nombre que usa GitHub por defecto.

### 14.4 Revisar qué se va a subir

```powershell
git status
```

Antes del primer commit, asegúrate de que:

- No aparezcan `.env`, contraseñas ni claves.
- No aparezcan `__pycache__`, `.venv` ni archivos temporales.
- Sí aparezcan `api/`, `frontend/`, `pruebas/`, `README.md`, `README_2.md`, `render.yaml`, `requirements.txt` y `.python-version`.

El archivo `.gitignore` evita subir basura y secretos:

```gitignore
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
.env
.env.*
!.env.example
api/data/*.tmp
*.log
.DS_Store
Thumbs.db
```

### 14.5 Primer commit

```powershell
git add .
git commit -m "Proyecto CRUD de catálogo con API REST, JWT y despliegue en Render"
```

- `git add .` prepara los archivos.
- `git commit` guarda una instantánea con un mensaje.

Comprobar:

```powershell
git log --oneline
```

### 14.6 ¿Qué es un commit?

Un commit es una **fotografía** del proyecto en un momento dado. Tiene:

- Un identificador único (hash).
- Autor y fecha.
- Mensaje.
- Referencia al commit anterior.

Si un cambio está mal, se puede revertir o corregir con otro commit.

### 14.7 Ramas

Una rama permite trabajar sin afectar `main`:

```powershell
git switch -c feature/nuevo-campo
# hacer cambios...
git add .
git commit -m "Agrega nuevo campo"
git switch main
git merge feature/nuevo-campo
```

Para este taller no es obligatorio, pero demuestra buenas prácticas.

---

## 15. Publicación en GitHub

### 15.1 Crear el repositorio remoto

1. Entra a <https://github.com>.
2. Inicia sesión.
3. Haz clic en **New repository**.
4. Nombre sugerido: `catalogo-productos`.
5. Visibilidad: **Public** (Render free permite repositorios privados, pero público es más fácil para la entrega).
6. **No** marques “Add a README”, “Add .gitignore” ni “Choose a license”, porque el proyecto ya los tiene.
7. Crea el repositorio.

GitHub mostrará una URL como:

```text
https://github.com/USUARIO/catalogo-productos.git
```

### 15.2 Conectar el remoto y subir

```powershell
git remote add origin https://github.com/USUARIO/catalogo-productos.git
git remote -v
git push -u origin main
```

- `git remote add origin` guarda la URL del repositorio remoto.
- `git push -u origin main` sube la rama `main` y la marca como seguimiento.
- Las siguientes veces basta con `git push`.

### 15.3 Autenticación con GitHub

GitHub ya no acepta la contraseña normal por HTTPS. Opciones:

**Opción A: Git Credential Manager**

Al ejecutar `git push`, se abre una ventana del navegador para iniciar sesión. Es lo más sencillo en Windows.

**Opción B: Personal Access Token (PAT)**

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
2. **Generate new token**.
3. Permiso mínimo: `repo`.
4. Copia el token.
5. Cuando `git push` pida contraseña, pega el token (no la contraseña de GitHub).

**Opción C: GitHub CLI**

Si tienes `gh` instalado:

```powershell
gh auth login
gh repo create catalogo-productos --public --source=. --remote=origin --push
```

### 15.4 Verificar en GitHub

- Abre la URL del repositorio.
- Deben aparecer todos los archivos.
- El commit debe tener tu nombre.
- No debe aparecer ningún secreto.

### 15.5 Actualizar el repositorio

Cada vez que cambies algo:

```powershell
git status
git add .
git commit -m "Describe el cambio"
git push
```

Render puede redesplegar automáticamente si `autoDeployTrigger` está en `commit`.

---

## 16. Despliegue en Render

### ¿Qué es Render?

Render es una plataforma en la nube (PaaS) que ejecuta aplicaciones web. Se conecta a un repositorio de GitHub y, cada vez que haces push, construye y publica la nueva versión.

### ¿Por qué Render para este proyecto?

- Acepta un servidor HTTP propio hecho con Python estándar.
- Tiene plan gratuito.
- Se conecta directamente a GitHub.
- Permite variables de entorno y health checks.
- Asigna HTTPS y una URL pública.

### Requisitos previos

1. Cuenta en GitHub con el proyecto subido.
2. Cuenta en Render: <https://render.com>.
3. El archivo `render.yaml` en la raíz del repositorio.
4. El archivo `requirements.txt`.
5. El archivo `.python-version`.

### 16.1 Opción A: Blueprint (recomendada)

El archivo `render.yaml` describe el servicio. Render lo lee y crea todo automáticamente.

1. Entra a <https://dashboard.render.com>.
2. Haz clic en **New +** → **Blueprint**.
3. Conecta tu cuenta de GitHub si es la primera vez.
4. Selecciona el repositorio `catalogo-productos`.
5. Render detecta `render.yaml` y muestra el servicio `catalogo-productos`.
6. Cuando pida `ADMIN_PASSWORD`, escribe la contraseña que quieras para el administrador.
   - Para la demo puedes usar `admin123`.
   - Para un sitio real, usa una contraseña larga y única.
7. Haz clic en **Apply**.
8. Espera el build y el deploy.

Render creará:

- Un **Web Service** llamado `catalogo-productos`.
- Región: Oregón (definida en `render.yaml`).
- Plan: Free.
- Build: `pip install -r requirements.txt`.
- Start: `python run.py`.
- Health check: `/api/salud`.
- Variables: `HOST=0.0.0.0`, `PYTHON_VERSION=3.12.8`, `JWT_SECRET` generado, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_NOMBRE`, `JWT_TTL_SEGUNDOS`.

> Si no quieres la región de Oregón, cambia `region` en `render.yaml` antes de aplicar el Blueprint o crea el servicio manualmente.

### 16.2 Opción B: crear el Web Service a mano

Si prefieres no usar el Blueprint:

1. Render Dashboard → **New +** → **Web Service**.
2. Conecta el repositorio de GitHub.
3. Configura:

| Campo | Valor |
| --- | --- |
| Name | `catalogo-productos` |
| Language | `Python 3` |
| Branch | `main` |
| Root Directory | *(vacío)* |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python run.py` |
| Instance Type | `Free` |
| Health Check Path | `/api/salud` |
| Auto-Deploy | `Yes` |

4. En **Environment Variables**, agrega:

| Variable | Valor |
| --- | --- |
| `HOST` | `0.0.0.0` |
| `PYTHON_VERSION` | `3.12.8` |
| `JWT_SECRET` | Un valor aleatorio largo (generado con `secrets.token_urlsafe(48)`) |
| `ADMIN_EMAIL` | `admin@catalogo.com` |
| `ADMIN_PASSWORD` | Tu contraseña de administrador |
| `ADMIN_NOMBRE` | `Administrador` |
| `JWT_TTL_SEGUNDOS` | `3600` |

5. Haz clic en **Create Web Service**.

> No agregues `PORT`. Render lo inyecta automáticamente y el código ya lo lee con `os.getenv("PORT")`.

### 16.3 ¿Por qué `HOST=0.0.0.0`?

`127.0.0.1` significa “solo escucha conexiones desde la misma máquina”. Dentro de Render, el proxy que recibe el tráfico externo necesita conectarse al contenedor; si el servidor escucha solo en `127.0.0.1`, el proxy no puede alcanzarlo y el sitio falla.

`0.0.0.0` significa “escucha en todas las interfaces de red”, que es lo que necesita un contenedor en la nube.

### 16.4 ¿Por qué no fijar `PORT`?

Render asigna un puerto dinámico a cada servicio y lo pasa como variable `PORT`. El código hace:

```python
PORT = int(os.getenv("PORT", "8000"))
```

Si fijas `PORT=8000` en el panel, puedes chocar con el puerto que Render espera. Deja que Render lo asigne.

### 16.5 ¿Qué hace el health check?

Render hace peticiones periódicas a `/api/salud`. Si responde `200`, considera que el servicio está sano. Si falla repetidamente, puede reiniciar o marcar el deploy como fallido.

La ruta devuelve:

```json
{"estado": "ok", "servicio": "catalogo-api"}
```

### 16.6 Build y start

| Comando | Qué hace |
| --- | --- |
| `pip install -r requirements.txt` | Instala dependencias. Como no hay, termina correctamente. |
| `python run.py` | Inicia el servidor en el puerto que Render asigna. |

### 16.7 Primer despliegue

En la página del servicio, pestaña **Logs**, verás algo similar a:

```text
==> Running build command 'pip install -r requirements.txt'...
==> Running 'python run.py'
  Catalogo de productos - API REST
  Formulario: http://localhost:10000
  API:        http://localhost:10000/api/productos
```

Render mostrará un estado **Live** cuando el health check pase.

La URL será:

```text
https://catalogo-productos.onrender.com
```

Si el nombre ya está ocupado, Render agregará un sufijo, por ejemplo:

```text
https://catalogo-productos-abc1.onrender.com
```

Copia la URL real desde el panel.

### 16.8 Variables de entorno en Render

Se configuran en:

**Dashboard → tu servicio → Environment → Environment Variables**

Reglas:

- `JWT_SECRET`: secreto, nunca en Git.
- `ADMIN_PASSWORD`: secreto, nunca en Git.
- `ADMIN_EMAIL` y `ADMIN_NOMBRE`: pueden ser públicos.
- Al cambiar una variable, Render pide **Save changes** y hace un nuevo deploy.
- Si cambias `JWT_SECRET`, todos los tokens emitidos antes dejan de funcionar.
- Si cambias `ADMIN_PASSWORD`, el login cambia; actualiza la nota de demostración del frontend si corresponde.

### 16.9 Plan free: comportamiento

| Característica | Plan free |
| --- | --- |
| Precio | $0 |
| HTTPS | Sí |
| Duerme por inactividad | Sí, tras ~15 minutos sin tráfico |
| Tiempo de despertar | ~30–60 segundos |
| Disco persistente | No |
| Sistema de archivos | Efímero |
| Ancho de banda | Limitado |
| Ideal para | Demos, tareas, portafolio |

Si el profesor entra después de un rato, la primera carga puede tardar. Es normal: el servicio está despertando.

---

## 17. Verificación después del despliegue

### 17.1 Verificar salud

Abre en el navegador:

```text
https://TU-SERVICIO.onrender.com/api/salud
```

Debe responder:

```json
{"estado":"ok","servicio":"catalogo-api"}
```

### 17.2 Verificar el frontend

Abre:

```text
https://TU-SERVICIO.onrender.com
```

Debe cargar la pantalla de login.

### 17.3 Verificar login

Usa las credenciales configuradas en Render.

### 17.4 Verificar CRUD

1. Crea un producto.
2. Edita el producto.
3. Búscalo.
4. Elimínalo.
5. Recarga la página y comprueba que los cambios siguen mientras el servicio está despierto.

### 17.5 Verificar con el script de pruebas

El script usa `http://127.0.0.1:8000` por defecto. Para probar Render, cambia `BASE_URL` en `pruebas/probar_api.py` o crea una copia. Ten en cuenta que el script **crea y elimina** un producto; no afecta a los demás.

También puedes importar la colección de Postman y cambiar `base_url` por la URL de Render.

### 17.6 Verificar CORS desde otro origen

Abre la consola del navegador en otra página y ejecuta:

```javascript
fetch("https://TU-SERVICIO.onrender.com/api/salud")
  .then((r) => r.json())
  .then(console.log);
```

Debe responder sin errores de CORS.

---

## 18. Actualizaciones, ramas y rollback

### Flujo normal de actualización

```powershell
# 1. Hacer cambios en local
# 2. Probar
py run.py
py pruebas/probar_api.py

# 3. Guardar en Git
git status
git add .
git commit -m "Mejora: describe el cambio"
git push

# 4. Render detecta el push y redespliega
```

### Si el deploy falla

1. Revisa **Logs** en Render.
2. Corrige el error en local.
3. Vuelve a probar.
4. Haz commit y push.

### Rollback

En Render, abre **Deploys** y selecciona un deploy anterior → **Redeploy**. También puedes revertir en Git:

```powershell
git revert <hash-del-commit>
git push
```

`git revert` crea un commit nuevo que deshace otro; no borra la historia.

### Ramas y previews

Render puede crear **Preview Environments** para ramas o pull requests en planes de pago. En free, trabaja con `main` y verifica en local antes de subir.

---

## 19. Problemas frecuentes y soluciones

| Problema | Causa probable | Solución |
| --- | --- | --- |
| `No se pudo iniciar el servidor en 127.0.0.1:8000` | Puerto ocupado | Usa `$env:PORT=8001; py run.py` o cierra el proceso. |
| Render muestra `502 Bad Gateway` | El servidor no escucha en `0.0.0.0` o no usa `PORT` | Configura `HOST=0.0.0.0` y no fijes `PORT`. |
| Render muestra `Application failed to respond` | El proceso terminó o el puerto es incorrecto | Revisa Logs y el comando de inicio. |
| El deploy falla en build | `requirements.txt` mal formado o versión de Python no disponible | Revisa logs; usa `3.12.8` o cambia `.python-version`. |
| La página carga pero el login falla | `ADMIN_EMAIL`/`ADMIN_PASSWORD` distintos | Revisa Environment en Render. |
| El login funcionaba y dejó de funcionar | Cambió `JWT_SECRET` o expiró el token | Vuelve a iniciar sesión; no cambies el secreto sin motivo. |
| Los productos desaparecen | El servicio se reinició y el JSON volvió a la versión de Git | Es el comportamiento del plan free; usa base de datos para persistencia real. |
| Primera carga muy lenta | El servicio free estaba dormido | Espera 30–60 segundos; es normal. |
| `403` al hacer push | Credenciales o permisos de GitHub | Usa Git Credential Manager o un PAT con permiso `repo`. |
| `remote origin already exists` | Ya hay un remoto configurado | `git remote set-url origin <nueva-url>` o `git remote remove origin`. |
| `fatal: not a git repository` | Estás fuera de la carpeta o no hiciste `git init` | `cd` a la carpeta correcta y ejecuta `git init`. |
| `Updates were rejected` | El remoto tiene commits que no tienes | `git pull --rebase origin main` y luego `git push`. |
| `Permission denied (publickey)` | SSH sin clave configurada | Usa HTTPS o configura una clave SSH en GitHub. |
| El frontend no encuentra la API | Ruta base incorrecta | El frontend usa `/api`, mismo origen; no cambies `RUTA_API` sin motivo. |
| `python` no se reconoce en Render | Comando de inicio incorrecto | Usa `python run.py`; Render ya tiene Python en el PATH. |
| Error de CORS | Faltan cabeceras o el preflight falla | Verifica `OPTIONS` y las cabeceras en `api/app.py`. |

### Cómo leer los logs de Render

1. Dashboard → servicio → **Logs**.
2. Busca `==> Running 'python run.py'`.
3. Si hay un traceback, la última línea suele indicar el error.
4. Si no hay logs nuevos, el servicio no está recibiendo tráfico o está dormido.

### Cómo saber si el servicio está dormido

- La primera petición tarda.
- En Render aparece el estado **Suspended** o el log muestra un arranque nuevo.
- Al entrar a `/api/salud`, responde después de unos segundos.

---

## 20. Limitaciones y mejoras para producción

Este proyecto es **académico**. Para un sistema real habría que mejorar:

| Área | Mejora recomendada |
| --- | --- |
| Persistencia | PostgreSQL/MySQL/MongoDB en lugar de JSON. |
| Contraseñas | Hash con `bcrypt` o `argon2`, nunca texto plano. |
| Secretos | Gestor de secretos (Render Environment, Vault, AWS Secrets Manager). |
| CORS | Restringir a los dominios reales del frontend. |
| HTTPS | Render ya lo da; en local usar solo para desarrollo. |
| Rate limiting | Limitar intentos de login y peticiones por IP. |
| Validación | Esquemas formales (Pydantic, Marshmallow) y sanitización. |
| Logs | Logs estructurados, sin datos sensibles, con niveles. |
| Backups | Copias automáticas de la base de datos. |
| Tests | Unitarios, integración, carga y seguridad. |
| Frontend | Framework, accesibilidad avanzada, manejo de estados. |
| Autenticación | Usuarios reales, refresh tokens, roles y permisos. |
| Observabilidad | Métricas, trazas y alertas. |
| Escalabilidad | Varias instancias y almacenamiento compartido. |

### ¿Por qué no guardar contraseñas en texto plano?

Porque si alguien accede al servidor o a las variables de entorno, obtiene las contraseñas. En producción se guarda un **hash** con sal (bcrypt, argon2, scrypt) y se compara el hash, no la contraseña.

En este taller, `ADMIN_PASSWORD` es una variable de entorno y se compara con `hmac.compare_digest`. Es aceptable para una demo de un solo usuario, pero no para un sistema real.

### ¿Por qué no usar `localStorage` para el token?

`localStorage` persiste aunque se cierre el navegador y es accesible desde JavaScript, lo que aumenta el impacto de un XSS. `sessionStorage` se borra al cerrar la pestaña y reduce la exposición. Ninguna de las dos es perfecta; para producción se prefieren cookies `HttpOnly` + `Secure` + `SameSite`.

### ¿Qué pasa con los datos en Render free?

Se pierden al reiniciar. Si el profesor crea productos y el servicio se duerme, al volver a despertar verá los datos iniciales del repositorio. Es una limitación del plan gratuito, no un error del CRUD. Explícalo en la exposición.

---

## 21. Guion para la exposición

Puedes seguir este orden (5–8 minutos):

1. **Presentación**: “Es un catálogo de productos con API REST, JWT, CORS y frontend responsive”.
2. **Demostración local o en Render**: abre la URL, inicia sesión y muestra la tabla.
3. **CRUD**: crea un producto, edítalo, búscalo y elimínalo.
4. **Validaciones**: intenta precio negativo o nombre duplicado.
5. **JWT**: muestra el login, explica header/payload/firma y que las rutas de escritura están protegidas.
6. **Arquitectura**: muestra las carpetas y explica rutas → controladores → servicios → repositorios.
7. **CORS**: explica el preflight y por qué el frontend puede consumir la API.
8. **Persistencia**: explica el JSON, la escritura atómica y la limitación de Render free.
9. **Pruebas**: muestra `22/22` y la colección de Postman.
10. **Git y Render**: muestra el repositorio, el commit, `render.yaml`, el health check y la URL pública.
11. **Cierre**: menciona mejoras futuras (base de datos, hash de contraseñas, CORS restringido).

### Frases útiles

- “El backend no usa frameworks; implementa HTTP, routing, CORS y JWT con la biblioteca estándar para demostrar cómo funcionan por dentro.”
- “La validación está en el servicio, no solo en el formulario, porque cualquiera puede saltarse el frontend con Postman.”
- “El token no está cifrado; está firmado. Por eso no incluyo datos sensibles en el payload.”
- “En Render free el disco es efímero; por eso los datos vuelven al estado inicial cuando el servicio se reinicia.”
- “Render asigna el puerto y yo solo lo leo; lo único que debo forzar es `HOST=0.0.0.0`.”

---

## 22. Preguntas probables del profesor (con respuestas)

### Sobre el proyecto y la arquitectura

**1. ¿Qué hace tu proyecto?**
Es un CRUD de productos con API REST y frontend web. Permite iniciar sesión, listar, buscar, crear, editar y eliminar productos, con validaciones y persistencia en JSON.

**2. ¿Qué significa CRUD?**
Create, Read, Update, Delete: crear, leer, actualizar y eliminar. En el proyecto se ve en `POST`, `GET`, `PUT` y `DELETE`.

**3. ¿Por qué usaste Python estándar y no Flask?**
Para demostrar el funcionamiento interno del protocolo HTTP, el enrutamiento, CORS y JWT sin depender de un framework. Además, el despliegue no requiere dependencias.

**4. ¿Qué es una API REST?**
Una interfaz HTTP que expone recursos mediante URLs y usa los métodos HTTP con su semántica: `GET` para leer, `POST` para crear, `PUT` para actualizar y `DELETE` para borrar.

**5. ¿Qué diferencia hay entre el frontend y el backend?**
El frontend es la interfaz que ve el usuario (`frontend/`); el backend es la API que valida, autentica y guarda (`api/`). Se comunican por HTTP/JSON.

**6. ¿Cómo se sirve el frontend?**
El mismo servidor de `api/app.py` sirve los archivos de `frontend/` en `/`, `/styles.css`, `/app.js` y `/favicon.svg`. Por eso frontend y API comparten origen.

**7. ¿Por qué separaste en capas?**
Para que cada parte tenga una responsabilidad: rutas (HTTP), controladores (adaptación), servicios (negocio) y repositorios (datos). Así el código es más fácil de probar, mantener y explicar.

**8. ¿Qué hace `api/rutas.py`?**
Define la tabla de rutas, compila los patrones con parámetros `:id`, resuelve el método y devuelve `404` o `405` cuando corresponde.

**9. ¿Dónde están las validaciones?**
En `api/servicios/productos.py`. El frontend también valida, pero el backend repite las reglas porque es la fuente de verdad.

**10. ¿Qué hace `api/errores.py`?**
Define `ApiError`, que lleva un código HTTP, un mensaje, detalles por campo y cabeceras opcionales. El servidor lo captura y lo convierte en JSON.

**11. ¿Qué pasa si ocurre un error inesperado?**
`api/app.py` captura la excepción, imprime la traza en el servidor y responde `500` con un mensaje genérico, sin filtrar detalles internos al cliente.

**12. ¿Por qué usaste `ThreadingHTTPServer`?**
Para atender varias peticiones concurrentes. El repositorio protege el JSON con un `RLock` y escritura atómica.

**13. ¿Cómo evitas que alguien lea archivos fuera de `frontend/`?**
Se resuelve la ruta y se comprueba con `relative_to(raiz)`. Si la ruta intenta salir de la carpeta, se responde `404`.

### Sobre HTTP y REST

**14. ¿Por qué `POST` devuelve `201` y no `200`?**
Porque `201 Created` indica que se creó un recurso nuevo. Además se envía `Location` con la URL del producto creado.

**15. ¿Por qué `DELETE` devuelve `204`?**
Porque la operación fue exitosa y no hay cuerpo que devolver. `204 No Content` es el código estándar para ese caso.

**16. ¿Qué significa `400`, `401`, `404`, `405`, `409` y `500`?**
- `400`: petición mal formada o datos inválidos.
- `401`: no autenticado o credenciales incorrectas.
- `404`: recurso o ruta inexistente.
- `405`: método no permitido para esa ruta.
- `409`: conflicto, por ejemplo nombre duplicado.
- `500`: error interno inesperado.

**17. ¿Por qué un id no numérico devuelve `400` y no `404`?**
Porque el formato del id es inválido; la petición está mal construida. `404` se reserva para un id válido que no existe.

**18. ¿Qué pasa si se hace `PUT` sin un campo?**
El servicio valida el objeto completo y responde `400` con los detalles de los campos faltantes. `PUT` reemplaza el recurso completo.

**19. ¿Qué pasa si se hace `POST /api/salud`?**
La ruta existe solo para `GET`, así que el resolvedor responde `405` con la cabecera `Allow`.

**20. ¿Cómo se responde al preflight?**
`do_OPTIONS` responde `204` y `end_headers` agrega las cabeceras CORS a todas las respuestas.

### Sobre JWT y seguridad

**21. ¿Qué es un JWT?**
Un token firmado con tres partes: header, payload y firma. Permite demostrar que el usuario se autenticó sin guardar sesión en el servidor.

**22. ¿Cómo se construye el token?**
Se codifican header y payload en Base64URL, se unen con un punto y se firma con HMAC-SHA256 usando `JWT_SECRET`.

**23. ¿Qué algoritmo usas y por qué?**
HS256, HMAC con SHA-256. Es simétrico, sencillo y suficiente para un servidor único.

**24. ¿Dónde se guarda el secreto?**
En la variable de entorno `JWT_SECRET`. En local se pasa por terminal; en Render se configura en el panel. Nunca se sube a Git.

**25. ¿Qué pasa si cambia el secreto?**
Los tokens anteriores dejan de ser válidos porque la firma ya no coincide. Todos deben iniciar sesión de nuevo.

**26. ¿Cómo validas la expiración?**
El payload incluye `exp` (timestamp Unix). `verificar_token` compara `exp` con `time.time()` y rechaza si ya pasó.

**27. ¿Cómo evitas que alteren el payload?**
La firma HMAC cubre header y payload. Si cambia un solo carácter, la firma recalculada no coincide y se responde `401`.

**28. ¿El token está cifrado?**
No. Base64URL no cifra; solo codifica. Cualquiera puede leer el payload. La firma garantiza integridad, no confidencialidad.

**29. ¿Por qué no guardas la contraseña en el token?**
Porque el payload es legible. Solo se guarda el correo, el nombre, el emisor y las fechas.

**30. ¿Dónde guarda el token el frontend?**
En `sessionStorage`. Se borra al cerrar la pestaña, al cerrar sesión o cuando el código detecta que expiró.

**31. ¿Qué pasa si expira el token mientras uso la app?**
La API responde `401`; el frontend limpia la sesión, muestra el login y avisa “Tu sesión expiró”.

**32. ¿Cómo cierras sesión?**
El botón **Salir** elimina el token y el usuario de `sessionStorage`, limpia el estado y vuelve al login. El token sigue siendo válido hasta expirar, pero el cliente ya no lo usa.

**33. ¿Por qué usas `compare_digest`?**
Para comparar credenciales y firmas en tiempo constante y reducir ataques de temporización.

**34. ¿Cómo almacenas las contraseñas?**
En esta demo, `ADMIN_PASSWORD` es una variable de entorno y se compara directamente. En producción se debe guardar un hash con bcrypt o argon2.

**35. ¿Es seguro usar `admin123` en producción?**
No. Es una credencial de demostración. En un sitio público se debe cambiar por una contraseña larga y única.

**36. ¿JWT es mejor que una cookie de sesión?**
No siempre. JWT es cómodo para APIs; las cookies `HttpOnly` protegen mejor contra XSS en aplicaciones web tradicionales. La elección depende del caso.

### Sobre CORS

**37. ¿Qué es CORS?**
Un mecanismo del navegador que permite o bloquea peticiones entre orígenes distintos. El servidor indica con cabeceras qué orígenes, métodos y encabezados están permitidos.

**38. ¿Qué es un preflight?**
Una petición `OPTIONS` que el navegador envía antes de una petición “no simple” para comprobar si el servidor la permite.

**39. ¿Por qué pusiste `Access-Control-Allow-Origin: *`?**
Para facilitar las pruebas desde Postman, otro puerto o un frontend separado. En producción se debe restringir al dominio real.

**40. ¿`*` permite cookies?**
No. El comodín no es compatible con credenciales. Si se necesitan cookies, se debe indicar un origen exacto y `Access-Control-Allow-Credentials: true`.

**41. ¿Cómo restringirías CORS?**
Cambiando el valor por el origen del frontend, por ejemplo `https://mi-frontend.com`, y validando el encabezado `Origin` contra una lista blanca.

### Sobre validaciones y persistencia

**42. ¿Qué reglas tiene el nombre?**
Obligatorio, entre 2 y 80 caracteres, sin duplicados comparando sin mayúsculas ni espacios extra.

**43. ¿Qué reglas tiene el precio?**
Número finito mayor que 0, máximo 99,999,999, redondeado a 2 decimales. No acepta booleanos ni texto no numérico.

**44. ¿Qué reglas tiene el stock?**
Entero mayor o igual a 0, máximo 1,000,000. No acepta decimales.

**45. ¿Cómo evitas nombres duplicados?**
`nombre_existe` recorre los productos, normaliza con `strip().casefold()` y compara. En actualización excluye el id que se está editando.

**46. ¿Qué pasa con un JSON mal formado?**
`json.loads` lanza una excepción, se captura y se responde `400` con “El cuerpo debe ser JSON válido”.

**47. ¿Qué pasa con un cuerpo enorme?**
Si supera 1 MB (`MAX_BODY_BYTES`), se responde `413`.

**48. ¿Cómo se guardan los datos?**
En `api/data/productos.json`, con un objeto que contiene `siguiente_id` y la lista `productos`.

**49. ¿Por qué escritura atómica?**
Para evitar que un corte a mitad de escritura deje el JSON corrupto. Se escribe en `.tmp` y se reemplaza con `os.replace`.

**50. ¿Qué hace el candado?**
`threading.RLock` serializa el acceso al estado compartido para evitar condiciones de carrera entre peticiones concurrentes.

**51. ¿Qué pasa con los datos en Render free?**
Se pierden al reiniciar o redesplegar porque el sistema de archivos es efímero. Para persistencia real se necesita una base de datos o un disco de pago.

**52. ¿Cómo migrarías a una base de datos?**
Cambiaría el repositorio por uno que use SQL/ORM, manteniendo la interfaz `listar`, `obtener`, `crear`, `actualizar`, `eliminar`. Los servicios y controladores casi no cambiarían.

### Sobre pruebas

**53. ¿Qué pruebas hiciste?**
Un script de humo con 22 comprobaciones, una colección de Postman y un archivo `api.http` para VS Code REST Client. También probé el flujo completo en el navegador.

**54. ¿Qué es una prueba de humo?**
Una prueba rápida que verifica que lo esencial funciona: salud, login, CRUD, errores y CORS. No reemplaza pruebas unitarias profundas.

**55. ¿Qué no cubren tus pruebas?**
Concurrencia masiva, seguridad ofensiva, navegadores específicos, accesibilidad y persistencia real en la nube.

**56. ¿Cómo probaste el `409`?**
Creando dos veces un producto con el mismo nombre; el script lo hace y verifica el código.

**57. ¿Cómo probaste CORS?**
Con una petición `OPTIONS` y verificando `Access-Control-Allow-Origin: *`.

### Sobre Git y GitHub

**58. ¿Qué es Git?**
Un sistema de control de versiones que guarda commits y permite historial, ramas y reversión.

**59. ¿Git y GitHub son lo mismo?**
No. Git es local; GitHub aloja repositorios Git en la nube.

**60. ¿Qué hace `git init`?**
Crea la carpeta `.git` y convierte el directorio en un repositorio.

**61. ¿Qué hace `git add`?**
Mueve cambios al área de preparación (staging) para incluirlos en el próximo commit.

**62. ¿Qué hace `git commit`?**
Crea una instantánea con los cambios preparados y un mensaje.

**63. ¿Qué hace `git push`?**
Sube los commits locales al repositorio remoto.

**64. ¿Qué es `origin`?**
El nombre convencional del remoto principal, normalmente GitHub.

**65. ¿Qué es `.gitignore`?**
Una lista de archivos y carpetas que Git debe ignorar, como `__pycache__`, `.venv`, `.env` y temporales.

**66. ¿Por qué no subes `.env`?**
Porque contiene secretos. Se sube un `.env.example` sin valores reales o se documentan las variables.

**67. ¿Qué es una rama?**
Una línea de desarrollo independiente. Permite probar cambios sin afectar `main`.

**68. ¿Qué es un merge?**
La integración de los cambios de una rama en otra.

**69. ¿Qué es un conflicto?**
Cuando dos ramas modifican la misma parte de un archivo y Git no puede decidir automáticamente; se resuelve a mano.

**70. ¿Qué es un commit hash?**
El identificador único del commit, calculado a partir de su contenido y metadatos.

### Sobre Render y despliegue

**71. ¿Qué es Render?**
Una plataforma en la nube que ejecuta aplicaciones web, las conecta a GitHub y les asigna una URL pública con HTTPS.

**72. ¿Qué es un Web Service?**
Un servicio que ejecuta un proceso HTTP, en este caso `python run.py`.

**73. ¿Qué comando usa Render para iniciar?**
`python run.py`, definido en `render.yaml` y en el panel.

**74. ¿Qué comando usa para construir?**
`pip install -r requirements.txt`. Como no hay dependencias, termina correctamente.

**75. ¿Por qué `HOST=0.0.0.0`?**
Porque el proxy de Render necesita conectarse al contenedor desde otra interfaz. `127.0.0.1` solo acepta conexiones locales.

**76. ¿Por qué no fijas `PORT`?**
Porque Render lo asigna dinámicamente y el código lo lee con `os.getenv("PORT")`.

**77. ¿Qué es un health check?**
Una petición periódica a `/api/salud` para verificar que el servicio responde. Si falla, Render puede reiniciar o marcar el deploy como fallido.

**78. ¿Qué pasa cuando el servicio free duerme?**
Se suspende tras unos 15 minutos sin tráfico. La siguiente petición tarda 30–60 segundos en despertarlo.

**79. ¿Los datos persisten en Render?**
Solo mientras el servicio está despierto. Al reiniciar o redesplegar, el filesystem vuelve a la versión del repositorio. Para persistencia real se necesita una base de datos o un disco de pago.

**80. ¿Cómo actualizas la app en Render?**
Haces commit y push a `main`; si el auto-deploy está activo, Render reconstruye y despliega.

**81. ¿Cómo haces rollback?**
En Render → **Deploys** → seleccionas un deploy anterior → **Redeploy**. O reviertes el commit en Git.

**82. ¿Dónde configuras las variables de entorno?**
En Render → servicio → **Environment** → **Environment Variables**.

**83. ¿Por qué no subes secretos a Git?**
Porque el repositorio puede ser público o compartido; cualquiera con acceso podría usar la clave JWT o la contraseña. Los secretos van en variables de entorno.

**84. ¿Qué pasa si el build falla?**
El deploy no se publica; la versión anterior sigue activa. Se revisan los logs, se corrige y se vuelve a hacer push.

**85. ¿Cómo verificas que el despliegue funciona?**
Abro `/api/salud`, la página principal, inicio sesión y ejecuto el CRUD. También puedo usar Postman con la URL de Render.

**86. ¿Qué URL tiene tu proyecto?**
`https://TU-SERVICIO.onrender.com` (reemplaza por la URL real que muestra Render).

**87. ¿Qué pasa si dos personas usan la app a la vez?**
El servidor atiende peticiones concurrentes con hilos y el repositorio serializa las escrituras. Para cargas grandes se necesita una base de datos y más infraestructura.

**88. ¿Qué pasa si Render reinicia mientras alguien guarda?**
La escritura atómica evita dejar el JSON a medias, pero el cambio puede perderse si el filesystem se reinicia. Es una limitación del plan free.

**89. ¿Qué es el archivo `render.yaml`?**
Un blueprint que describe el servicio: tipo, runtime, plan, comandos, health check y variables. Render lo lee para crear el servicio automáticamente.

**90. ¿Qué es `.python-version`?**
Un archivo que indica la versión de Python que debe usar la plataforma, en este caso `3.12.8`.

### Preguntas “difíciles” o de análisis

**91. ¿Qué mejorarías de tu proyecto?**
Base de datos real, hash de contraseñas, CORS restringido, rate limiting, pruebas unitarias, logs estructurados y refresh tokens.

**92. ¿Qué parte fue la más difícil?**
Explicar la implementación de JWT sin librerías y manejar correctamente los códigos HTTP y CORS.

**93. ¿Qué aprendiste?**
Cómo funciona HTTP por dentro, la separación por capas, la firma de tokens, el preflight de CORS y el ciclo de vida de un despliegue en la nube.

**94. ¿Por qué el frontend no puede saltarse las validaciones?**
Porque la API valida de nuevo. Aunque alguien modifique el HTML o use Postman, el servicio rechaza datos inválidos.

**95. ¿Qué pasa si alguien modifica el token en el navegador?**
La firma deja de coincidir y la API responde `401`. No puede cambiar el correo o la expiración sin el secreto.

**96. ¿Qué pasa si alguien roba el token?**
Puede usarlo hasta que expire (1 hora). Por eso se usa HTTPS, se guarda en `sessionStorage` y se recomienda acortar la vigencia y usar refresh tokens en producción.

**97. ¿Por qué no usas `Access-Control-Allow-Origin` con el dominio de Render?**
Porque el frontend se sirve desde el mismo origen y también quiero permitir pruebas desde Postman u otros orígenes. En producción lo restringiría.

**98. ¿Cómo manejarías imágenes de productos?**
Agregaría un campo `imagen_url`, validaría la URL y, si se suben archivos, usaría un almacenamiento externo (S3, Cloudinary) porque el filesystem de Render es efímero.

**99. ¿Cómo manejarías usuarios y roles?**
Tendría una tabla de usuarios con hash de contraseña, roles (`admin`, `usuario`) y un middleware que verifique permisos además del JWT.

**100. Si tuvieras que defender una sola decisión, ¿cuál sería?**
La separación por capas: permite cambiar la persistencia o la interfaz sin reescribir las reglas de negocio.

---

## 23. Glosario

| Término | Significado |
| --- | --- |
| **API** | Interfaz de programación que permite comunicar sistemas. |
| **REST** | Estilo de arquitectura basado en recursos y métodos HTTP. |
| **CRUD** | Crear, leer, actualizar y eliminar. |
| **Endpoint** | URL con un método HTTP que expone una operación. |
| **JSON** | Formato de texto para intercambiar datos. |
| **JWT** | Token firmado con header, payload y firma. |
| **HS256** | HMAC con SHA-256; firma simétrica. |
| **CORS** | Mecanismo del navegador para peticiones entre orígenes. |
| **Preflight** | Petición `OPTIONS` previa a una petición CORS no simple. |
| **HTTP** | Protocolo de comunicación de la web. |
| **Status code** | Código numérico que indica el resultado de una petición. |
| **Repositorio** | Capa que accede a los datos. |
| **Servicio** | Capa con reglas de negocio y validaciones. |
| **Controlador** | Capa que adapta HTTP al servicio. |
| **Git** | Sistema de control de versiones. |
| **Commit** | Instantánea de cambios. |
| **Rama** | Línea independiente de desarrollo. |
| **Remoto** | Repositorio alojado en otro lugar (GitHub). |
| **Deploy** | Proceso de publicar una aplicación. |
| **Build** | Proceso de preparar la aplicación para ejecutarse. |
| **Health check** | Verificación periódica de que el servicio responde. |
| **Ephemeral filesystem** | Sistema de archivos que se reinicia y pierde cambios. |
| **Paas** | Plataforma como servicio (Render, Heroku, Railway). |

---

## 24. Chuleta de comandos

### Local

```powershell
# Ejecutar
py run.py

# Otro puerto
$env:PORT=8001; py run.py

# Pruebas
py pruebas/probar_api.py

# Generar secreto JWT
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Git

```powershell
git init
git branch -M main
git status
git add .
git commit -m "Mensaje"
git log --oneline
git remote add origin https://github.com/USUARIO/REPO.git
git remote -v
git push -u origin main
git pull --rebase origin main
git switch -c nombre-rama
git switch main
git merge nombre-rama
```

### Render

```text
New + → Blueprint → conectar repo → aplicar render.yaml
o
New + → Web Service → Python 3 → build/start → variables → Create
```

Variables mínimas:

```text
HOST=0.0.0.0
PYTHON_VERSION=3.12.8
JWT_SECRET=<aleatorio>
ADMIN_EMAIL=admin@catalogo.com
ADMIN_PASSWORD=<segura>
ADMIN_NOMBRE=Administrador
JWT_TTL_SEGUNDOS=3600
```

Verificación:

```text
https://TU-SERVICIO.onrender.com/api/salud
https://TU-SERVICIO.onrender.com
```

---

## 25. Checklist final

### Antes de subir a Git

- [ ] El proyecto corre con `py run.py`.
- [ ] Las pruebas dan `22/22`.
- [ ] El CRUD funciona en el navegador.
- [ ] `requirements.txt` existe.
- [ ] `render.yaml` existe y es válido.
- [ ] `.python-version` existe.
- [ ] `.gitignore` excluye `__pycache__`, `.venv`, `.env` y temporales.
- [ ] No hay contraseñas ni claves reales en el código.
- [ ] `README.md` y `README_2.md` están actualizados.

### Antes de desplegar

- [ ] El repositorio está en GitHub.
- [ ] La rama se llama `main`.
- [ ] `render.yaml` está en la raíz.
- [ ] `HOST=0.0.0.0` está configurado.
- [ ] `JWT_SECRET` es largo y aleatorio.
- [ ] `ADMIN_PASSWORD` es la contraseña correcta.
- [ ] El health check apunta a `/api/salud`.

### Después de desplegar

- [ ] `/api/salud` responde `200`.
- [ ] La página principal carga.
- [ ] El login funciona con las credenciales configuradas.
- [ ] Se puede crear, editar, buscar y eliminar.
- [ ] CORS funciona desde Postman.
- [ ] La URL pública está copiada en la entrega.
- [ ] Se explicó la limitación de persistencia del plan free.

---

## Nota final sobre la URL pública

Cuando Render termine el despliegue, copia la URL real y reemplaza todas las apariciones de:

```text
https://TU-SERVICIO.onrender.com
```

por tu URL, por ejemplo:

```text
https://catalogo-productos.onrender.com
```

También actualiza la variable `base_url` de Postman si vas a probar contra la nube.

---

**Autor:** Proyecto académico de API REST con Python, JWT, CORS y Render.
**Fecha:** Noviembre de 2026.
