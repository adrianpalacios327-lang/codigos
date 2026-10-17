// ==========================================
// CONFIGURACIÓN Y ESTADO GLOBAL
// ==========================================
const API_BASE = (window.location.port === "8000" || window.location.port === "") ? "" : "http://127.0.0.1:8000";
const LOGIN_URL = "/login/login.html";
const VISOR_URL = "/principal/interfaz plan de estudio/visor_plan.html";

const chatBox = document.getElementById('chat-box');
const promptInput = document.getElementById('prompt-input');
const btnEnviar = document.getElementById('btn-enviar');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const historyList = document.getElementById('history-list');
const btnMenu = document.getElementById('menuToggle');

let historialConversacion = [];
let listaMensajesUI = [];
let enviando = false;                 // evita envíos dobles (Enter + clic, doble Enter)
let archivoAdjuntoActual = null;
const visoresPlan = [];               // { iframe, plan } para responder a cada visor con SU plan
window.ultimoPlanGenerado = null;
window.planesSugeridos = window.planesSugeridos || {};

// Banco de mensajes motivacionales aleatorios para el modal
const mensajesMotivacionales = [
  "🎉 ¡Excelente trabajo! Un paso más cerca de dominar este tema.",
  "🚀 ¡Poderoso avance! Tu constancia está dando frutos.",
  "⚡ ¡Nivel de conocimiento aumentado! Sigue con ese gran ritmo.",
  "🧠 ¡Concepto dominado! Tu cerebro te lo agradecerá.",
  "🔥 ¡Estás en racha! Sigue así y alcanzarás tus metas pronto.",
  "🌟 ¡Increíble esfuerzo! Cada lección completada cuenta.",
  "🏆 ¡Lo lograste! Tómate un respiro o continúa al siguiente nivel."
];

// ==========================================
// AUXILIARES
// ==========================================

// Escapa texto para insertarlo en HTML o en atributos (incluye comillas)
function escaparHTML(str) {
    if (str === null || str === undefined || str === '') return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function removerElemento(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollAlFondo() {
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
}

// localStorage que no rompe la app si se llena la cuota
function guardarLS(clave, valor) {
    try {
        localStorage.setItem(clave, typeof valor === 'string' ? valor : JSON.stringify(valor));
    } catch (e) {
        console.warn(`No se pudo guardar "${clave}" en localStorage:`, e);
    }
}

// FastAPI puede devolver "detail" como texto, lista de errores u objeto
function extraerDetalle(detail) {
    if (!detail) return null;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map(d => (d && d.msg) ? d.msg : JSON.stringify(d)).join('; ');
    }
    try { return JSON.stringify(detail); } catch (e) { return String(detail); }
}

function urlVisor(idPlan) {
    return encodeURI(VISOR_URL) + (idPlan ? `?id=${encodeURIComponent(idPlan)}` : '');
}

function origenSeguro() {
    return window.location.origin === 'null' ? '*' : window.location.origin;
}

function htmlAvatarIA() {
    return `<div class="avatar"><img src="avatar.png" alt="Avatar IA"></div>`;
}

function htmlSaludo() {
    return `
        <div class="mensaje">
            <div class="avatar">
                <img src="avatar.png" alt="Logo" width="50" height="50" class="logo" style="border-radius:50%; object-fit:cover;">
            </div>
            <div class="contenido">
                <p>¡Hola! 👋 Soy tu asistente de <strong>StudNova IA</strong>.</p>
                <p style="margin-top: 8px;">Cuéntame, ¿qué materia o tema te gustaría aprender hoy?</p>
            </div>
        </div>
    `;
}

// ==========================================
// UTILIDAD: OBTENER ID USUARIO
// (si no hay sesión devuelve null; ya no se usa el usuario 1 por defecto)
// ==========================================
function obtenerIdUsuario() {
    try {
        const idDirecto = localStorage.getItem("id_usuario") || sessionStorage.getItem("id_usuario");
        const n = parseInt(idDirecto, 10);
        if (!isNaN(n)) return n;

        const usuarioStr = localStorage.getItem("user")
            || localStorage.getItem("usuario")
            || localStorage.getItem("studnova:session")
            || sessionStorage.getItem("usuario");
        if (usuarioStr) {
            const u = JSON.parse(usuarioStr);
            const id = parseInt(u.id_usuario || u.id, 10);
            if (!isNaN(id)) return id;
        }
    } catch (e) {
        console.warn("No se pudo parsear la información de usuario:", e);
    }
    return null;
}

// ==========================================
// INICIALIZACIÓN
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
    await asegurarUsuarioRegistrado();

    if (obtenerIdUsuario() === null) {
        window.location.href = LOGIN_URL;
        return;
    }

    cargarHistorialPlanes();
    restaurarEstadoChat();
    registrarEventosChat();
});

// Sincronizar automáticamente usuarios autenticados por Google
async function asegurarUsuarioRegistrado() {
    try {
        const idActual = localStorage.getItem("id_usuario");
        let email = localStorage.getItem("userEmail");
        let nombre = localStorage.getItem("userName");

        if (!email) {
            const userRaw = localStorage.getItem("user");
            if (userRaw) {
                const uObj = JSON.parse(userRaw);
                email = uObj.email || uObj.correo;
                nombre = uObj.name || uObj.nombre;
            }
        }

        if (email && (!idActual || isNaN(parseInt(idActual, 10)))) {
            const res = await fetch(`${API_BASE}/usuario/google`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    nombre: nombre || "Estudiante",
                    correo: email
                })
            });
            if (res.ok) {
                const u = await res.json();
                localStorage.setItem("id_usuario", u.id_usuario);
                localStorage.setItem("user", JSON.stringify(u));
                console.log("Usuario de Google sincronizado con PostgreSQL:", u.id_usuario);
            }
        }
    } catch (e) {
        console.warn("Aviso al verificar usuario:", e);
    }
}

// ==========================================
// CERRAR SESIÓN
// ==========================================
function cerrarSesion() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "../principal interfaz/index.html";
}

// ==========================================
// CONTROL DEL MENÚ HAMBURGUESA / SIDEBAR
// ==========================================
function toggleMenu() {
    if (sidebar) sidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
    if (btnMenu && sidebar) {
        btnMenu.setAttribute('aria-expanded', String(sidebar.classList.contains('active')));
    }
}

// ==========================================
// CARGAR HISTORIAL DE PLANES (BASE DE DATOS)
// ==========================================
async function cargarHistorialPlanes() {
    if (!historyList) return;

    const idUsuario = obtenerIdUsuario();
    if (idUsuario === null) return;

    try {
        const respuesta = await fetch(`${API_BASE}/plan-estudio/usuario/${idUsuario}`);
        if (!respuesta.ok) {
            throw new Error("No se pudo obtener el historial de planes.");
        }

        const planes = await respuesta.json();
        historyList.innerHTML = '';

        if (!planes || planes.length === 0) {
            historyList.innerHTML = '<li class="sin-planes">No hay planes creados aún.</li>';
            return;
        }

        planes.forEach(plan => {
            try {
                const li = document.createElement('li');
                li.className = 'history-item';
                li.tabIndex = 0;
                li.setAttribute('role', 'button');

                const fechaFormateada = plan.fecha_creacion
                    ? new Date(plan.fecha_creacion).toLocaleDateString('es')
                    : (plan.fecha || 'Reciente');

                const contenidoPlan = plan.contenido_json
                    ? (typeof plan.contenido_json === 'string' ? JSON.parse(plan.contenido_json) : plan.contenido_json)
                    : plan;

                const idPlan = plan.id_plan || plan.id || contenidoPlan.id_plan;
                const abrir = () => cargarPlanSeleccionado(contenidoPlan, idPlan);

                li.addEventListener('click', abrir);
                li.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrir(); }
                });

                li.innerHTML = `
                    <span class="plan-title">${escaparHTML(plan.titulo || plan.nombre || "Plan de Estudio")}</span>
                    <span class="plan-date">${escaparHTML(plan.nivel_objetivo || "Intermedio")} • ${escaparHTML(fechaFormateada)}</span>
                `;
                historyList.appendChild(li);
            } catch (e) {
                // un plan dañado ya no tumba toda la lista
                console.warn("Se omitió un plan con datos inválidos:", e);
            }
        });

        if (!historyList.children.length) {
            historyList.innerHTML = '<li class="sin-planes">No hay planes creados aún.</li>';
        }

    } catch (error) {
        console.warn("Aviso al cargar historial de planes:", error);
        historyList.innerHTML = '<li class="sin-planes">No hay planes creados aún.</li>';
    }
}

function cargarPlanSeleccionado(plan, idPlan) {
    if (!plan) return;
    const id = idPlan || plan.id_plan;
    // el visor necesita id_plan para guardar el progreso en el backend
    if (id && !plan.id_plan) plan.id_plan = id;
    guardarLS("plan_estudio_actual", plan);
    window.location.href = urlVisor(id);
}

// ==========================================
// GESTIÓN DE ARCHIVOS ADJUNTOS Y CONFIGURACIÓN
// ==========================================
function activarInputArchivo() {
    const input = document.getElementById('input-archivo');
    if (input) input.click();
}

function manejarArchivoSeleccionado(evento) {
    const file = evento.target.files && evento.target.files[0];
    if (!file) return;

    archivoAdjuntoActual = file;
    const contenedor = document.getElementById('contenedor-adjunto');
    const txtNombre = document.getElementById('nombre-archivo-adjunto');
    const btnClip = document.getElementById('btn-adjuntar');

    if (txtNombre) txtNombre.innerText = file.name;
    if (contenedor) contenedor.style.display = 'flex';
    if (btnClip) btnClip.classList.add('activo');
}

function quitarArchivoAdjunto() {
    archivoAdjuntoActual = null;
    const input = document.getElementById('input-archivo');
    if (input) input.value = '';

    const selModulos = document.getElementById('select-modulos');
    if (selModulos) selModulos.value = '';

    const selDuracion = document.getElementById('select-duracion');
    if (selDuracion) selDuracion.value = '';

    const contenedor = document.getElementById('contenedor-adjunto');
    const btnClip = document.getElementById('btn-adjuntar');

    if (contenedor) contenedor.style.display = 'none';
    if (btnClip) btnClip.classList.remove('activo');
}

// ==========================================
// ENVÍO DE MENSAJES Y CHAT
// ==========================================
function manejarEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        enviarMensaje();
    }
}

async function enviarMensaje(forzarNuevo = false, promptPersonalizado = null, cantModulosParam = null, duracionParam = null) {
    if (enviando) return;

    const input = document.getElementById('prompt-input') || promptInput;
    const boton = document.getElementById('btn-enviar') || btnEnviar;
    const texto = promptPersonalizado !== null ? promptPersonalizado.trim() : (input ? input.value.trim() : '');

    if (!texto && !archivoAdjuntoActual) return;

    const idUsuario = obtenerIdUsuario();
    if (idUsuario === null) {
        window.location.href = LOGIN_URL;
        return;
    }

    // Parámetros de módulos y duración
    const hayAdjunto = Boolean(archivoAdjuntoActual);
    const selModulos = document.getElementById('select-modulos');
    const selDuracion = document.getElementById('select-duracion');

    const cantModulos = cantModulosParam || ((hayAdjunto && selModulos && selModulos.value) ? Number(selModulos.value) : null);
    const duracionDeseada = duracionParam || ((hayAdjunto && selDuracion && selDuracion.value) ? selDuracion.value : null);

    // Texto visible del mensaje del usuario
    let textoAMostrar = texto;
    if (forzarNuevo && promptPersonalizado) {
        const detalle = [];
        if (cantModulos) detalle.push(`${cantModulos} módulos`);
        if (duracionDeseada) detalle.push(`en ${duracionDeseada}`);
        const strDetalle = detalle.length > 0 ? ` (${detalle.join(', ')})` : '';
        textoAMostrar = `✨ Prefiero generar un plan nuevo desde cero${strDetalle}: "${texto}"`;
    } else if (hayAdjunto) {
        const detalleExtra = [];
        if (cantModulos) detalleExtra.push(`${cantModulos} módulos`);
        if (duracionDeseada) detalleExtra.push(duracionDeseada);
        const strDetalle = detalleExtra.length > 0 ? ` (${detalleExtra.join(', ')})` : '';
        const mensajeBase = texto || "Crea un plan de estudio a partir de este documento adjunto.";
        textoAMostrar = `📄 [Adjunto: ${archivoAdjuntoActual.name}${strDetalle}]\n${mensajeBase}`;
    }

    historialConversacion.push({ rol: "usuario", texto: textoAMostrar });
    agregarMensajeUsuario(textoAMostrar);

    if (input && promptPersonalizado === null) input.value = '';

    enviando = true;
    if (boton) boton.disabled = true;

    const idCarga = agregarMensajeCarga();
    scrollAlFondo();

    try {
        let respuesta;

        if (hayAdjunto) {
            // Archivo adjunto real: endpoint multipart
            const formData = new FormData();
            formData.append('prompt', texto || "Genera un plan de estudio pedagógico a partir de este documento.");
            formData.append('id_usuario', Number(idUsuario));
            if (cantModulos) formData.append('cantidad_modulos', cantModulos);
            if (duracionDeseada) formData.append('duracion_personalizada', duracionDeseada);
            formData.append('historial_json', JSON.stringify(historialConversacion.slice(0, -1)));
            formData.append('archivo', archivoAdjuntoActual);

            respuesta = await fetch(`${API_BASE}/api/ia/generar-con-archivo`, {
                method: 'POST',
                body: formData
            });
        } else {
            // Flujo conversacional JSON
            let promptFinal = texto;
            if (forzarNuevo) {
                promptFinal = `Genera directamente el plan de estudio estructurado completo en JSON sobre: ${texto}.`;
                if (cantModulos) promptFinal += ` Requisito obligatorio: DEBE contener exactamente ${cantModulos} módulos completos.`;
                if (duracionDeseada) promptFinal += ` Diseñado para completarse en un tiempo de: ${duracionDeseada}.`;
            }

            respuesta = await fetch(`${API_BASE}/api/ia/generar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    prompt: promptFinal,
                    historial: historialConversacion,
                    id_usuario: Number(idUsuario),
                    forzar_nuevo: Boolean(forzarNuevo),
                    cantidad_modulos: cantModulos ? Number(cantModulos) : null,
                    duracion_personalizada: duracionDeseada || null
                })
            });
        }

        let datos;
        const textoRespuesta = await respuesta.text();

        try {
            datos = JSON.parse(textoRespuesta);
        } catch {
            // si el servidor devolvió una página de error, no la volcamos entera al chat
            throw new Error((textoRespuesta || 'Error en la respuesta del servidor').slice(0, 200));
        }

        if (!respuesta.ok) {
            throw new Error(extraerDetalle(datos.detail) || 'Ocurrió un error al procesar la solicitud');
        }

        removerElemento(idCarga);

        // CASO 1: Sugerencia de plan existente
        if (datos.tipo === "sugerencia_plan_existente") {
            const textoIA = datos.mensaje || "He encontrado un plan existente similar a tu solicitud.";
            historialConversacion.push({ rol: "ia", texto: textoIA });
            agregarMensajeSugerenciaPlan(datos);
            return;
        }

        const textoIA = datos.mensaje || datos.respuesta || "He procesado tu solicitud.";
        historialConversacion.push({ rol: "ia", texto: textoIA });

        const tienePlan = (datos.tipo === "plan_generado") ||
                          (datos.plan && datos.plan.modulos && datos.plan.modulos.length > 0) ||
                          (datos.modulos && datos.modulos.length > 0);

        if (tienePlan) {
            const planObjeto = datos.plan || datos;
            // el visor necesita id_plan para guardar el progreso
            if (datos.id_plan && !planObjeto.id_plan) planObjeto.id_plan = datos.id_plan;
            window.ultimoPlanGenerado = planObjeto;

            guardarLS("plan_estudio_actual", planObjeto);
            cargarHistorialPlanes();

            agregarMensajeIARespuestaPlan(datos, planObjeto);
        } else {
            agregarMensajeIATexto(textoIA);
        }

        // Limpiar archivo adjunto tras envío exitoso
        quitarArchivoAdjunto();

    } catch (error) {
        removerElemento(idCarga);
        // el mensaje del usuario no tuvo respuesta: no lo dejamos en el contexto de la IA
        if (historialConversacion.length && historialConversacion[historialConversacion.length - 1].rol === "usuario") {
            historialConversacion.pop();
        }
        agregarMensajeError(error.message || "Ocurrió un error inesperado.");
    } finally {
        enviando = false;
        if (boton) boton.disabled = false;
        if (input) input.focus();
        guardarEstadoChat();
        scrollAlFondo();
    }
}

// ==========================================
// PERSISTENCIA DEL ESTADO DEL CHAT
// ==========================================
function guardarEstadoChat() {
    const idUsuario = obtenerIdUsuario();
    if (idUsuario === null) return;

    guardarLS(`studnova_chat_historial_${idUsuario}`, historialConversacion);
    guardarLS(`studnova_chat_mensajes_ui_${idUsuario}`, listaMensajesUI);
    if (window.ultimoPlanGenerado) {
        guardarLS(`studnova_ultimo_plan_${idUsuario}`, window.ultimoPlanGenerado);
    }
}

function restaurarEstadoChat() {
    try {
        const idUsuario = obtenerIdUsuario();
        if (idUsuario === null) return;

        const rawHistorial = localStorage.getItem(`studnova_chat_historial_${idUsuario}`);
        const rawMensajesUI = localStorage.getItem(`studnova_chat_mensajes_ui_${idUsuario}`);
        const rawUltimoPlan = localStorage.getItem(`studnova_ultimo_plan_${idUsuario}`);

        if (rawHistorial) historialConversacion = JSON.parse(rawHistorial);
        if (rawUltimoPlan) window.ultimoPlanGenerado = JSON.parse(rawUltimoPlan);

        if (rawMensajesUI) {
            listaMensajesUI = JSON.parse(rawMensajesUI);
            if (Array.isArray(listaMensajesUI) && listaMensajesUI.length > 0) {
                listaMensajesUI.forEach(item => {
                    if (item.tipo === 'usuario') {
                        renderizarDOMMensajeUsuario(item.texto);
                    } else if (item.tipo === 'ia_texto') {
                        renderizarDOMMensajeIATexto(item.texto);
                    } else if (item.tipo === 'ia_plan') {
                        renderizarDOMMensajeIAPlan(item.datos, item.planObjeto);
                    } else if (item.tipo === 'ia_sugerencia') {
                        renderizarDOMMensajeSugerencia(item.datos);
                    } else if (item.tipo === 'error') {
                        renderizarDOMMensajeError(item.texto);
                    }
                });
                scrollAlFondo();
            }
        }
    } catch (e) {
        console.warn("Aviso al restaurar estado del chat:", e);
    }
}

// ==========================================
// INICIAR NUEVO CHAT
// ==========================================
function iniciarNuevoChat() {
    const idUsuario = obtenerIdUsuario();
    if (idUsuario !== null) {
        localStorage.removeItem(`studnova_chat_historial_${idUsuario}`);
        localStorage.removeItem(`studnova_chat_mensajes_ui_${idUsuario}`);
        localStorage.removeItem(`studnova_ultimo_plan_${idUsuario}`);
    }
    historialConversacion = [];
    listaMensajesUI = [];
    visoresPlan.length = 0;
    window.ultimoPlanGenerado = null;
    window.planesSugeridos = {};

    if (chatBox) chatBox.innerHTML = htmlSaludo();

    quitarArchivoAdjunto();
    if (sidebar && sidebar.classList.contains('active')) {
        toggleMenu();
    }
}

// ==========================================
// RENDERIZADO DE MENSAJES EN EL CHAT (DOM)
// ==========================================
function renderizarDOMMensajeUsuario(texto) {
    const div = document.createElement('div');
    div.className = 'mensaje mensaje-usuario';
    div.innerHTML = `
        <div class="avatar avatar-usuario">👩🏻‍💻</div>
        <div class="contenido"><p>${escaparHTML(texto)}</p></div>
    `;
    chatBox.appendChild(div);
}

function agregarMensajeUsuario(texto) {
    renderizarDOMMensajeUsuario(texto);
    listaMensajesUI.push({ tipo: 'usuario', texto });
    guardarEstadoChat();
}

function agregarMensajeCarga() {
    const id = 'carga-' + Date.now();
    const div = document.createElement('div');
    div.className = 'mensaje mensaje-carga';
    div.id = id;
    div.innerHTML = `
        ${htmlAvatarIA()}
        <div class="contenido contenido-pensando" role="status" aria-live="polite">
            <span class="puntos-pensando" aria-hidden="true"><span></span><span></span><span></span></span>
            <span class="texto-pensando">StudNova IA está pensando…</span>
        </div>
    `;
    chatBox.appendChild(div);
    return id;
}

function renderizarDOMMensajeIATexto(texto) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.innerHTML = `
        ${htmlAvatarIA()}
        <div class="contenido"><p>${escaparHTML(texto)}</p></div>
    `;
    chatBox.appendChild(div);
}

function agregarMensajeIATexto(texto) {
    renderizarDOMMensajeIATexto(texto);
    listaMensajesUI.push({ tipo: 'ia_texto', texto });
    guardarEstadoChat();
}

// ==========================================
// SUGERENCIA INTERACTIVA DE PLAN EXISTENTE
// (los botones usan data-* y delegación de eventos: ya no hay
//  texto del usuario dentro de atributos onclick)
// ==========================================
function renderizarDOMMensajeSugerencia(datos) {
    const div = document.createElement('div');
    div.className = 'mensaje';

    const plan = datos.plan_sugerido || {};
    const idPlan = datos.id_plan;
    window.planesSugeridos[idPlan] = plan;

    const titulo = plan.titulo || "Plan de Estudio";
    const descripcion = plan.descripcion || "Ruta estructurada de aprendizaje interactivo.";
    const modulosCount = (plan.modulos && Array.isArray(plan.modulos)) ? plan.modulos.length : 3;
    const materia = plan.materia || "Materia Principal";
    const idCard = `sugerencia-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
    const temaOriginal = datos.prompt_original || materia;

    div.innerHTML = `
        ${htmlAvatarIA()}
        <div class="contenido contenido-ancho">
            <div class="tarjeta-sugerencia" id="${idCard}">
                <div class="sugerencia-badge">💡 Plan similar encontrado en biblioteca</div>
                <div class="sugerencia-titulo">${escaparHTML(titulo)}</div>
                <div class="sugerencia-desc">${escaparHTML(descripcion)}</div>

                <div class="sugerencia-meta">
                    <span class="meta-item">📖 ${modulosCount} módulos</span>
                    <span class="meta-item">🏷️ ${escaparHTML(materia)}</span>
                    <span class="meta-item ahorro">⚡ 0 tokens requeridos (Carga instantánea)</span>
                </div>

                <p class="sugerencia-pregunta">
                    Ya existe este plan estructurado que cubre tu consulta. ¿Qué deseas hacer?
                </p>

                <div class="sugerencia-acciones" id="acciones-${idCard}">
                    <button type="button" class="btn-sugerencia btn-sugerencia-aceptar"
                            data-accion="aceptar-plan" data-id-plan="${escaparHTML(idPlan)}" data-id-card="${idCard}">
                        📖 1. Ver este plan existente
                    </button>
                    <button type="button" class="btn-sugerencia btn-sugerencia-nuevo"
                            data-accion="preguntas-nuevo" data-tema="${escaparHTML(temaOriginal)}" data-id-card="${idCard}">
                        ✨ 2. Generar un plan nuevo con IA
                    </button>
                </div>
            </div>
        </div>
    `;

    chatBox.appendChild(div);
}

function agregarMensajeSugerenciaPlan(datos) {
    renderizarDOMMensajeSugerencia(datos);
    listaMensajesUI.push({ tipo: 'ia_sugerencia', datos });
    guardarEstadoChat();
    scrollAlFondo();
}

async function aceptarPlanSugerido(idPlan, idCard) {
    const contenedorCard = document.getElementById(idCard);
    if (contenedorCard) {
        contenedorCard.querySelectorAll('button').forEach(b => { b.disabled = true; });
    }

    const idCarga = agregarMensajeCarga();
    scrollAlFondo();

    try {
        const idUsuario = obtenerIdUsuario();
        const res = await fetch(`${API_BASE}/api/ia/aceptar-sugerencia`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                id_plan: Number(idPlan),
                id_usuario: Number(idUsuario)
            })
        });

        removerElemento(idCarga);

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(extraerDetalle(errData.detail) || "Error al cargar el plan existente");
        }

        const datos = await res.json();
        const planObjeto = datos.plan || window.planesSugeridos[idPlan];
        if (!planObjeto) throw new Error("No se recibió el contenido del plan.");

        // el visor necesita id_plan para guardar el progreso
        if (!planObjeto.id_plan) planObjeto.id_plan = datos.id_plan || Number(idPlan);
        if (!datos.id_plan) datos.id_plan = planObjeto.id_plan;

        window.ultimoPlanGenerado = planObjeto;
        guardarLS("plan_estudio_actual", planObjeto);
        cargarHistorialPlanes();

        if (contenedorCard) {
            contenedorCard.classList.add('tarjeta-aceptada');
            const acciones = contenedorCard.querySelector('.sugerencia-acciones');
            if (acciones) {
                acciones.innerHTML = '<span class="sugerencia-estado estado-ok">✔️ Has seleccionado ver este plan existente</span>';
            }
        }

        agregarMensajeIARespuestaPlan(datos, planObjeto);

    } catch (e) {
        removerElemento(idCarga);
        if (contenedorCard) {
            // permite reintentar si algo falló
            contenedorCard.querySelectorAll('button').forEach(b => { b.disabled = false; });
        }
        agregarMensajeError(e.message);
    }
}

// ==========================================
// PREGUNTAS INTERACTIVAS PARA NUEVO PLAN
// ==========================================
function mostrarPreguntasNuevoPlan(temaOriginal, idCard) {
    const contenedorAcciones = document.getElementById(`acciones-${idCard}`);
    if (!contenedorAcciones) return;

    contenedorAcciones.innerHTML = `
        <div class="formulario-preguntas-nuevo">
            <p class="pregunta-titulo">
                🎯 Personaliza tu nuevo plan sobre "${escaparHTML(temaOriginal)}":
            </p>

            <div class="pregunta-campos">
                <div class="pregunta-campo">
                    <label for="tiempo-${idCard}">⏱️ ¿En cuánto tiempo?</label>
                    <select id="tiempo-${idCard}">
                        <option value="1 semana">1 semana (Intensivo)</option>
                        <option value="2 semanas" selected>2 semanas (Recomendado)</option>
                        <option value="1 mes">1 mes (Paso a paso)</option>
                        <option value="2 meses">2 meses (A profundidad)</option>
                    </select>
                </div>

                <div class="pregunta-campo">
                    <label for="modulos-${idCard}">📚 ¿Cuántos módulos?</label>
                    <select id="modulos-${idCard}">
                        <option value="3">3 módulos (Esencial)</option>
                        <option value="4" selected>4 módulos (Equilibrado)</option>
                        <option value="5">5 módulos (Completo)</option>
                    </select>
                </div>
            </div>

            <button type="button" class="btn-sugerencia btn-sugerencia-nuevo btn-sugerencia-ancho"
                    data-accion="confirmar-nuevo" data-tema="${escaparHTML(temaOriginal)}" data-id-card="${idCard}">
                🚀 ¡Generar mi plan personalizado!
            </button>
        </div>
    `;

    scrollAlFondo();
}

function confirmarNuevoPlanPersonalizado(temaOriginal, idCard) {
    const selTiempo = document.getElementById(`tiempo-${idCard}`);
    const selModulos = document.getElementById(`modulos-${idCard}`);

    const tiempoSeleccionado = selTiempo ? selTiempo.value : "2 semanas";
    const modulosSeleccionados = selModulos ? Number(selModulos.value) : 4;

    const acciones = document.getElementById(`acciones-${idCard}`);
    if (acciones) {
        acciones.innerHTML = `<span class="sugerencia-estado estado-info">⚙️ Generando ruta con ${modulosSeleccionados} módulos para ${escaparHTML(tiempoSeleccionado)}...</span>`;
    }

    enviarMensaje(true, temaOriginal, modulosSeleccionados, tiempoSeleccionado);
}

function forzarGeneracionNueva(promptOriginal, idCard) {
    mostrarPreguntasNuevoPlan(promptOriginal, idCard);
}

// Delegación de eventos para los botones creados dinámicamente en el chat
function registrarEventosChat() {
    if (!chatBox || chatBox.dataset.eventos === 'ok') return;
    chatBox.dataset.eventos = 'ok';

    chatBox.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-accion]');
        if (!btn || btn.disabled) return;

        const { accion, idPlan, idCard, tema } = btn.dataset;

        if (accion === 'aceptar-plan') aceptarPlanSugerido(idPlan, idCard);
        else if (accion === 'preguntas-nuevo') mostrarPreguntasNuevoPlan(tema, idCard);
        else if (accion === 'confirmar-nuevo') confirmarNuevoPlanPersonalizado(tema, idCard);
    });
}

// ==========================================
// MENSAJE CON EL PLAN GENERADO (visor embebido)
// ==========================================
function enviarPlanAIframe(iframe, plan) {
    try {
        iframe.contentWindow.postMessage({ tipo: 'CARGAR_PLAN', plan }, origenSeguro());
    } catch (err) {
        console.warn("Aviso al enviar postMessage al iframe:", err);
    }
}

function renderizarDOMMensajeIAPlan(datos, planObjeto) {
    const div = document.createElement('div');
    div.className = 'mensaje';

    const mensajeTexto = datos.mensaje || datos.respuesta || "✨ ¡Plan de estudio generado con éxito!";
    const idPlan = datos.id_plan || (planObjeto && planObjeto.id_plan) || "";
    const url = urlVisor(idPlan);

    div.innerHTML = `
        ${htmlAvatarIA()}
        <div class="contenido contenido-ancho">
            <p><strong>${escaparHTML(mensajeTexto)}</strong></p>
            <p class="nota-plan">
                He estructurado tu ruta de aprendizaje a tu medida con quizzes y control de fatiga.
            </p>
            <div class="acciones-plan">
                <a class="btn-abrir-plan" href="${escaparHTML(url)}">↗️ Abrir Plan en Pantalla Completa</a>
            </div>
            <div class="visor-plan">
                <iframe src="${escaparHTML(url)}" title="Plan de estudio" loading="lazy"></iframe>
            </div>
        </div>
    `;

    const iframe = div.querySelector('iframe');
    if (iframe) {
        // limpiar visores de mensajes que ya no existen y registrar el nuevo
        for (let i = visoresPlan.length - 1; i >= 0; i--) {
            if (!visoresPlan[i].iframe.isConnected) visoresPlan.splice(i, 1);
        }
        visoresPlan.push({ iframe, plan: planObjeto });
        iframe.addEventListener('load', () => enviarPlanAIframe(iframe, planObjeto));
    }

    chatBox.appendChild(div);
}

function agregarMensajeIARespuestaPlan(datos, planObjeto) {
    if (planObjeto) guardarLS("plan_estudio_actual", planObjeto);
    renderizarDOMMensajeIAPlan(datos, planObjeto);
    listaMensajesUI.push({ tipo: 'ia_plan', datos, planObjeto });
    guardarEstadoChat();
    scrollAlFondo();
}

// ==========================================
// ERRORES
// ==========================================
function renderizarDOMMensajeError(mensaje) {
    const div = document.createElement('div');
    div.className = 'mensaje mensaje-error';
    div.innerHTML = `
        <div class="avatar avatar-error">⚠️</div>
        <div class="contenido contenido-error"><p><strong>Error:</strong> ${escaparHTML(mensaje)}</p></div>
    `;
    chatBox.appendChild(div);
}

function agregarMensajeError(mensaje) {
    renderizarDOMMensajeError(mensaje);
    listaMensajesUI.push({ tipo: 'error', texto: mensaje });
    guardarEstadoChat();
    scrollAlFondo();
}

// ==========================================
// MENSAJES ENTRE VENTANAS (visor del plan dentro del iframe)
// ==========================================
window.addEventListener('message', (event) => {
    if (window.location.origin !== 'null' && event.origin !== window.location.origin) return;

    const data = event.data;
    if (!data || typeof data !== 'object') return;

    if (data.tipo === 'SOLICITAR_PLAN' && event.source) {
        // cada visor recibe SU plan (antes todos recibían el último generado)
        const visor = visoresPlan.find(v => v.iframe.contentWindow === event.source);
        const plan = visor ? visor.plan : window.ultimoPlanGenerado;
        if (plan) {
            event.source.postMessage({ tipo: 'CARGAR_PLAN', plan }, origenSeguro());
        }
    } else if (data.tipo === 'LECCION_COMPLETADA') {
        mostrarModalLeccionCompletada();
    }
});

// ==========================================
// CONTROL DEL MODAL EMERGENTE (LECCIÓN COMPLETADA)
// ==========================================
function mostrarModalLeccionCompletada() {
    const modal = document.getElementById('modal-completado');
    const txtMensaje = document.getElementById('texto-motivacional');

    if (modal && txtMensaje) {
        const indiceAleatorio = Math.floor(Math.random() * mensajesMotivacionales.length);
        txtMensaje.innerText = mensajesMotivacionales[indiceAleatorio];
        modal.classList.add('activo');
    }
}

function cerrarModalCompletado() {
    const modal = document.getElementById('modal-completado');
    if (modal) modal.classList.remove('activo');
}

// Cerrar con ESC (modal y menú lateral) y con clic fuera del modal
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    cerrarModalCompletado();
    if (sidebar && sidebar.classList.contains('active')) toggleMenu();
});

document.addEventListener('click', (e) => {
    const modal = document.getElementById('modal-completado');
    if (e.target === modal) cerrarModalCompletado();
});