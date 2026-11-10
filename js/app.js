"use strict";

const RUTA_API = "/api";
const CLAVE_TOKEN = "catalogo.token";
const CLAVE_USUARIO = "catalogo.usuario";

const formatoMoneda = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  minimumFractionDigits: 2,
});
const formatoNumero = new Intl.NumberFormat("es-MX");

const ETIQUETAS = {
  nombre: "Nombre",
  descripcion: "Descripción",
  precio: "Precio",
  stock: "Stock",
  categoria: "Categoría",
  email: "Correo",
  password: "Contraseña",
};

const estado = {
  token: sessionStorage.getItem(CLAVE_TOKEN) || "",
  usuario: leerUsuarioGuardado(),
  productos: [],
  filtro: "",
  edicionId: null,
  eliminandoId: null,
};

const el = {};
const campos = {};

/* ------------------------------------------------------------------ arranque */

function iniciar() {
  cachearElementos();
  conectarEventos();

  if (estado.token && !tokenExpirado(estado.token)) {
    mostrarApp();
    cargarProductos();
  } else {
    if (estado.token) limpiarSesion();
    mostrarLogin();
  }
}

function cachearElementos() {
  const ids = [
    "vistaLogin",
    "vistaApp",
    "barraUsuario",
    "nombreUsuario",
    "btnSalir",
    "formLogin",
    "loginEmail",
    "loginPassword",
    "loginError",
    "btnLogin",
    "btnNuevo",
    "formTitulo",
    "formSubtitulo",
    "formModo",
    "tarjetaFormulario",
    "formProducto",
    "productoId",
    "campoNombre",
    "campoDescripcion",
    "campoPrecio",
    "campoStock",
    "campoCategoria",
    "formError",
    "btnGuardar",
    "btnLimpiar",
    "statProductos",
    "statStock",
    "statValor",
    "resumenLista",
    "buscador",
    "tablaEnvoltura",
    "tablaProductos",
    "tablaVacia",
    "dialogoEliminar",
    "textoEliminar",
    "btnCancelarEliminar",
    "btnConfirmarEliminar",
    "avisos",
  ];

  for (const id of ids) {
    el[id] = document.getElementById(id);
  }

  Object.assign(campos, {
    nombre: el.campoNombre,
    descripcion: el.campoDescripcion,
    precio: el.campoPrecio,
    stock: el.campoStock,
    categoria: el.campoCategoria,
  });
}

function conectarEventos() {
  el.formLogin.addEventListener("submit", manejarLogin);
  el.btnSalir.addEventListener("click", salir);
  el.btnNuevo.addEventListener("click", () => limpiarFormulario(true));
  el.formProducto.addEventListener("submit", manejarGuardar);
  el.btnLimpiar.addEventListener("click", () => limpiarFormulario(true));

  el.buscador.addEventListener("input", (evento) => {
    estado.filtro = evento.target.value;
    renderizarProductos();
  });

  el.tablaProductos.addEventListener("click", manejarAccionTabla);
  el.btnCancelarEliminar.addEventListener("click", cerrarDialogoEliminar);
  el.btnConfirmarEliminar.addEventListener("click", confirmarEliminar);

  el.dialogoEliminar.addEventListener("close", () => {
    estado.eliminandoId = null;
  });

  el.dialogoEliminar.addEventListener("click", (evento) => {
    if (evento.target === el.dialogoEliminar) cerrarDialogoEliminar();
  });

  for (const campo of Object.values(campos)) {
    campo.addEventListener("input", () => {
      campo.classList.remove("invalido");
      campo.removeAttribute("aria-invalid");
    });
  }
}

/* ------------------------------------------------------------------- sesión */

function leerUsuarioGuardado() {
  try {
    const crudo = sessionStorage.getItem(CLAVE_USUARIO);
    return crudo ? JSON.parse(crudo) : null;
  } catch {
    return null;
  }
}

function tokenExpirado(token) {
  try {
    const partes = token.split(".");
    if (partes.length !== 3) return true;

    const base64 = partes[1].replace(/-/g, "+").replace(/_/g, "/");
    const relleno = "=".repeat((4 - (base64.length % 4)) % 4);
    const binario = atob(base64 + relleno);
    const bytes = Uint8Array.from(binario, (caracter) => caracter.charCodeAt(0));
    const payload = JSON.parse(new TextDecoder().decode(bytes));

    return !payload.exp || payload.exp * 1000 <= Date.now();
  } catch {
    return true;
  }
}

function mostrarLogin() {
  el.vistaApp.classList.add("hidden");
  el.vistaLogin.classList.remove("hidden");
  el.barraUsuario.classList.add("hidden");
  ocultarErrorLogin();
  document.title = "Catálogo de productos";
}

function mostrarApp() {
  el.vistaLogin.classList.add("hidden");
  el.vistaApp.classList.remove("hidden");
  el.barraUsuario.classList.remove("hidden");
  el.nombreUsuario.textContent = estado.usuario?.nombre || "Administrador";
  el.nombreUsuario.title = estado.usuario?.email || "";
  document.title = "Productos · Catálogo";
}

async function manejarLogin(evento) {
  evento.preventDefault();
  ocultarErrorLogin();

  const email = el.loginEmail.value.trim();
  const password = el.loginPassword.value;

  if (!email || !password) {
    mostrarErrorLogin("Ingresa tu correo y contraseña.");
    return;
  }

  const textoOriginal = el.btnLogin.textContent;
  el.btnLogin.disabled = true;
  el.btnLogin.textContent = "Entrando…";

  try {
    const datos = await api("/auth/login", {
      method: "POST",
      body: { email, password },
    });

    if (!datos?.token) throw new Error("El servidor no devolvió un token.");

    estado.token = datos.token;
    estado.usuario = datos.usuario || { nombre: "Administrador", email };
    sessionStorage.setItem(CLAVE_TOKEN, estado.token);
    sessionStorage.setItem(CLAVE_USUARIO, JSON.stringify(estado.usuario));

    mostrarApp();
    await cargarProductos();
    aviso("Sesión iniciada. Bienvenido.");
  } catch (error) {
    mostrarErrorLogin(mensajeError(error));
  } finally {
    el.btnLogin.disabled = false;
    el.btnLogin.textContent = textoOriginal;
  }
}

function salir() {
  limpiarSesion();
  mostrarLogin();
  aviso("Sesión cerrada.");
  el.loginEmail.focus();
}

function limpiarSesion() {
  estado.token = "";
  estado.usuario = null;
  estado.productos = [];
  estado.filtro = "";
  estado.edicionId = null;
  estado.eliminandoId = null;

  sessionStorage.removeItem(CLAVE_TOKEN);
  sessionStorage.removeItem(CLAVE_USUARIO);

  if (el.buscador) el.buscador.value = "";
  if (el.dialogoEliminar?.open) el.dialogoEliminar.close();

  limpiarFormulario();
  renderizarProductos();
}

function cerrarSesionExpirada() {
  if (!el.vistaApp || el.vistaApp.classList.contains("hidden")) return;
  limpiarSesion();
  mostrarLogin();
  aviso("Tu sesión expiró. Inicia sesión de nuevo.", "error");
}

function mostrarErrorLogin(mensaje) {
  el.loginError.textContent = mensaje;
  el.loginError.classList.remove("hidden");
}

function ocultarErrorLogin() {
  el.loginError.textContent = "";
  el.loginError.classList.add("hidden");
}

/* -------------------------------------------------------------------- datos */

async function api(ruta, { method = "GET", body, auth = false } = {}) {
  const headers = { Accept: "application/json" };

  if (body !== undefined) headers["Content-Type"] = "application/json";

  if (auth) {
    if (!estado.token) {
      cerrarSesionExpirada();
      const error = new Error("Tu sesión expiró. Inicia sesión de nuevo.");
      error.sesionExpirada = true;
      throw error;
    }
    headers.Authorization = `Bearer ${estado.token}`;
  }

  let respuesta;
  try {
    respuesta = await fetch(`${RUTA_API}${ruta}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor. Verifica que esté en ejecución.");
  }

  if (respuesta.status === 204) return null;

  const texto = await respuesta.text();
  let datos = null;
  if (texto) {
    try {
      datos = JSON.parse(texto);
    } catch {
      datos = { error: texto };
    }
  }

  if (!respuesta.ok) {
    if (respuesta.status === 401 && auth) {
      cerrarSesionExpirada();
      const error = new Error("Tu sesión expiró. Inicia sesión de nuevo.");
      error.sesionExpirada = true;
      throw error;
    }

    const error = new Error(
      datos?.error || `No se pudo completar la solicitud (${respuesta.status}).`
    );
    error.estado = respuesta.status;
    error.detalles = datos?.detalles;
    throw error;
  }

  return datos;
}

async function cargarProductos() {
  try {
    const datos = await api("/productos");
    estado.productos = Array.isArray(datos?.productos) ? datos.productos : [];
  } catch (error) {
    estado.productos = [];
    aviso(mensajeError(error), "error");
  }

  renderizarProductos();
}

function renderizarProductos() {
  const termino = normalizar(estado.filtro.trim());
  const visibles = termino
    ? estado.productos.filter((producto) =>
        normalizar(
          `${producto.nombre} ${producto.descripcion ?? ""} ${producto.categoria}`
        ).includes(termino)
      )
    : estado.productos;

  dibujarEstadisticas();
  actualizarResumen(visibles.length);
  el.tablaProductos.replaceChildren(...visibles.map(crearFila));

  const hayVisibles = visibles.length > 0;
  el.tablaEnvoltura.classList.toggle("hidden", !hayVisibles);
  el.tablaVacia.classList.toggle("hidden", hayVisibles);

  if (!hayVisibles) {
    const hayProductos = estado.productos.length > 0;
    el.tablaVacia.querySelector("strong").textContent = hayProductos
      ? "Sin resultados"
      : "Sin productos";
    el.tablaVacia.querySelector("span").textContent = hayProductos
      ? `No encontramos coincidencias para “${estado.filtro.trim()}”.`
      : "Agrega el primero con el formulario.";
  }
}

function dibujarEstadisticas() {
  const total = estado.productos.length;
  const unidades = estado.productos.reduce(
    (suma, producto) => suma + (Number(producto.stock) || 0),
    0
  );
  const valor = estado.productos.reduce(
    (suma, producto) =>
      suma + (Number(producto.precio) || 0) * (Number(producto.stock) || 0),
    0
  );

  el.statProductos.textContent = formatoNumero.format(total);
  el.statStock.textContent = formatoNumero.format(unidades);
  el.statValor.textContent = formatoMoneda.format(valor);
}

function actualizarResumen(totalVisibles) {
  const total = estado.productos.length;
  if (estado.filtro.trim()) {
    el.resumenLista.textContent = `${totalVisibles} de ${total} ${
      total === 1 ? "producto" : "productos"
    }`;
  } else {
    el.resumenLista.textContent = `${total} ${
      total === 1 ? "producto" : "productos"
    } en el catálogo`;
  }
}

function crearFila(producto) {
  const fila = document.createElement("tr");

  const celdaProducto = document.createElement("td");
  const nombre = document.createElement("span");
  nombre.className = "producto-nombre";
  nombre.textContent = producto.nombre;

  const descripcion = document.createElement("span");
  descripcion.className = "producto-desc";
  descripcion.textContent = producto.descripcion || "Sin descripción";
  descripcion.title = producto.descripcion || "";

  celdaProducto.append(nombre, descripcion);

  const celdaCategoria = document.createElement("td");
  const categoria = document.createElement("span");
  categoria.className = "etiqueta-categoria";
  categoria.textContent = producto.categoria;
  celdaCategoria.appendChild(categoria);

  const celdaPrecio = document.createElement("td");
  celdaPrecio.className = "col-numero";
  celdaPrecio.textContent = formatoMoneda.format(Number(producto.precio) || 0);

  const celdaStock = document.createElement("td");
  celdaStock.className = "col-numero";
  const stock = document.createElement("span");
  const unidades = Number(producto.stock) || 0;
  stock.className = "stock";
  if (unidades === 0) stock.classList.add("stock-agotado");
  else if (unidades <= 5) stock.classList.add("stock-bajo");
  stock.textContent = formatoNumero.format(unidades);
  stock.title = unidades === 0 ? "Agotado" : `${unidades} unidades`;
  celdaStock.appendChild(stock);

  const celdaAcciones = document.createElement("td");
  celdaAcciones.className = "col-acciones";
  const acciones = document.createElement("div");
  acciones.className = "acciones";
  const editar = botonAccion("Editar", "editar", producto);
  const eliminar = botonAccion("Eliminar", "eliminar", producto);
  eliminar.classList.add("peligro");
  acciones.append(editar, eliminar);
  celdaAcciones.appendChild(acciones);

  fila.append(celdaProducto, celdaCategoria, celdaPrecio, celdaStock, celdaAcciones);
  return fila;
}

function botonAccion(texto, accion, producto) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.className = "btn-enlace";
  boton.textContent = texto;
  boton.dataset.accion = accion;
  boton.dataset.id = String(producto.id);
  boton.setAttribute("aria-label", `${texto}: ${producto.nombre}`);
  return boton;
}

function manejarAccionTabla(evento) {
  const boton = evento.target.closest("button[data-accion]");
  if (!boton) return;

  const id = Number(boton.dataset.id);
  if (!Number.isInteger(id)) return;

  if (boton.dataset.accion === "editar") {
    cargarEnFormulario(id);
  } else if (boton.dataset.accion === "eliminar") {
    abrirConfirmacion(id);
  }
}

function normalizar(texto) {
  return String(texto ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

/* ---------------------------------------------------------------- formulario */

function actualizarFormularioUI() {
  const editando = estado.edicionId !== null;

  el.formTitulo.textContent = editando ? "Editar producto" : "Nuevo producto";
  el.formSubtitulo.textContent = editando
    ? `Modifica los datos del producto #${estado.edicionId}.`
    : "Registra un artículo en el catálogo.";
  el.formModo.classList.toggle("hidden", !editando);
  el.btnGuardar.textContent = editando ? "Guardar cambios" : "Guardar producto";
  el.btnLimpiar.textContent = editando ? "Cancelar" : "Limpiar";
}

function limpiarFormulario(enfocar = false) {
  estado.edicionId = null;
  el.productoId.value = "";
  el.formProducto.reset();
  ocultarErroresFormulario();
  actualizarFormularioUI();

  if (enfocar) {
    el.tarjetaFormulario.scrollIntoView({ behavior: "smooth", block: "start" });
    el.campoNombre.focus({ preventScroll: true });
  }
}

function cargarEnFormulario(id) {
  const producto = estado.productos.find((item) => item.id === id);
  if (!producto) return;

  estado.edicionId = id;
  el.productoId.value = String(id);
  el.campoNombre.value = producto.nombre ?? "";
  el.campoDescripcion.value = producto.descripcion ?? "";
  el.campoPrecio.value = String(producto.precio ?? "");
  el.campoStock.value = String(producto.stock ?? "");
  el.campoCategoria.value = producto.categoria ?? "";

  ocultarErroresFormulario();
  actualizarFormularioUI();
  el.tarjetaFormulario.scrollIntoView({ behavior: "smooth", block: "start" });
  el.campoNombre.focus({ preventScroll: true });
}

async function manejarGuardar(evento) {
  evento.preventDefault();
  ocultarErroresFormulario();

  const datos = {
    nombre: el.campoNombre.value.trim(),
    descripcion: el.campoDescripcion.value.trim(),
    precio: el.campoPrecio.value.trim(),
    stock: el.campoStock.value.trim(),
    categoria: el.campoCategoria.value.trim(),
  };

  const errores = validarFormulario(datos);
  if (Object.keys(errores).length > 0) {
    mostrarErroresFormulario(errores);
    return;
  }

  const cuerpo = {
    nombre: datos.nombre,
    descripcion: datos.descripcion,
    precio: Number(datos.precio),
    stock: Number(datos.stock),
    categoria: datos.categoria,
  };

  const editando = estado.edicionId !== null;
  const boton = el.btnGuardar;
  boton.disabled = true;
  boton.textContent = editando ? "Guardando…" : "Creando…";

  try {
    if (editando) {
      await api(`/productos/${estado.edicionId}`, {
        method: "PUT",
        body: cuerpo,
        auth: true,
      });
    } else {
      await api("/productos", { method: "POST", body: cuerpo, auth: true });
    }

    aviso(editando ? "Producto actualizado." : "Producto agregado al catálogo.");
    limpiarFormulario();
    await cargarProductos();
  } catch (error) {
    if (error.sesionExpirada) return;

    if (error.detalles) {
      mostrarErroresFormulario(error.detalles);
    } else {
      mostrarErrorFormulario(mensajeError(error));
      aviso(mensajeError(error), "error");
    }
  } finally {
    boton.disabled = false;
    boton.textContent =
      estado.edicionId === null ? "Guardar producto" : "Guardar cambios";
  }
}

function validarFormulario(datos) {
  const errores = {};

  if (datos.nombre.length < 2) {
    errores.nombre = "Escribe al menos 2 caracteres.";
  } else if (datos.nombre.length > 80) {
    errores.nombre = "Máximo 80 caracteres.";
  }

  if (datos.descripcion.length > 300) {
    errores.descripcion = "Máximo 300 caracteres.";
  }

  const precio = Number(datos.precio);
  if (datos.precio === "" || !Number.isFinite(precio) || precio <= 0) {
    errores.precio = "Ingresa un precio mayor que 0.";
  }

  const stock = Number(datos.stock);
  if (datos.stock === "" || !Number.isInteger(stock) || stock < 0) {
    errores.stock = "Ingresa un stock entero mayor o igual a 0.";
  }

  if (datos.categoria.length < 2) {
    errores.categoria = "Indica una categoría.";
  } else if (datos.categoria.length > 40) {
    errores.categoria = "Máximo 40 caracteres.";
  }

  return errores;
}

function mostrarErroresFormulario(detalles) {
  if (!detalles || typeof detalles !== "object") return;

  ocultarErroresFormulario();
  const mensajes = [];

  for (const [campo, texto] of Object.entries(detalles)) {
    mensajes.push(`${ETIQUETAS[campo] || campo}: ${texto}`);
    const input = campos[campo];
    if (input) {
      input.classList.add("invalido");
      input.setAttribute("aria-invalid", "true");
    }
  }

  mostrarErrorFormulario(mensajes.join(" ") || "Revisa los datos del formulario.");

  const primero = Object.keys(detalles)
    .map((campo) => campos[campo])
    .find(Boolean);
  if (primero) primero.focus();
}

function mostrarErrorFormulario(texto) {
  el.formError.textContent = texto;
  el.formError.classList.remove("hidden");
}

function ocultarErroresFormulario() {
  el.formError.textContent = "";
  el.formError.classList.add("hidden");

  for (const campo of Object.values(campos)) {
    campo.classList.remove("invalido");
    campo.removeAttribute("aria-invalid");
  }
}

/* ------------------------------------------------------------------ eliminar */

function abrirConfirmacion(id) {
  const producto = estado.productos.find((item) => item.id === id);
  if (!producto) return;

  estado.eliminandoId = id;
  el.textoEliminar.textContent = `Se eliminará “${producto.nombre}” del catálogo. Esta acción no se puede deshacer.`;
  el.dialogoEliminar.showModal();
}

function cerrarDialogoEliminar() {
  if (el.dialogoEliminar.open) el.dialogoEliminar.close();
  estado.eliminandoId = null;
}

async function confirmarEliminar() {
  const id = estado.eliminandoId;
  if (id === null) return;

  const boton = el.btnConfirmarEliminar;
  const textoOriginal = boton.textContent;
  boton.disabled = true;
  boton.textContent = "Eliminando…";

  try {
    await api(`/productos/${id}`, { method: "DELETE", auth: true });

    if (estado.edicionId === id) limpiarFormulario();
    cerrarDialogoEliminar();
    aviso("Producto eliminado.");
    await cargarProductos();
  } catch (error) {
    if (error.sesionExpirada) return;
    aviso(mensajeError(error), "error");
  } finally {
    boton.disabled = false;
    boton.textContent = textoOriginal;
  }
}

/* -------------------------------------------------------------------- avisos */

function mensajeError(error) {
  if (!error) return "Ocurrió un error inesperado.";

  if (error.detalles && typeof error.detalles === "object") {
    const detalles = Object.entries(error.detalles)
      .map(([campo, texto]) => `${ETIQUETAS[campo] || campo}: ${texto}`)
      .join(" ");
    return [error.message, detalles].filter(Boolean).join(" ");
  }

  return error.message || "Ocurrió un error inesperado.";
}

function aviso(mensaje, tipo = "ok") {
  const nodo = document.createElement("div");
  nodo.className = `aviso${tipo === "error" ? " aviso-error" : ""}`;
  nodo.textContent = mensaje;
  el.avisos.appendChild(nodo);

  window.setTimeout(() => {
    nodo.classList.add("aviso-saliendo");
    window.setTimeout(() => nodo.remove(), 220);
  }, 3400);
}

iniciar();
