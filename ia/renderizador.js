// --- CERRAR SESION ---
function cerrarSesion() {
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/login/login.html";
}
// --- FIN CERRAR SESION ---

const chatBox = document.getElementById('chat-box');
const promptInput = document.getElementById('prompt-input');
const btnEnviar = document.getElementById('btn-enviar');
let historialConversacion = [];

function manejarEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        enviarMensaje();
    }
}
async function enviarMensaje() {
    const texto = promptInput.value.trim();
    if (!texto) return;
    agregarMensajeUsuario(texto);
    historialConversacion.push({ rol: "usuario", texto: texto });
    promptInput.value = '';
    btnEnviar.disabled = true;
    btnEnviar.style.opacity = '0.5';
    const idCarga = agregarMensajeCarga();
    scrollAlFondo();
    try {
        const respuesta = await fetch('/api/ia/generar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: texto, historial: historialConversacion })
        });
        let datos;
        const textoRespuesta = await respuesta.text();
        try { datos = JSON.parse(textoRespuesta); } catch { throw new Error(textoRespuesta || 'Error en la respuesta del servidor'); }
        if (!respuesta.ok) throw new Error(datos.detail || 'Ocurrió un error al procesar');
        const textoIA = datos.mensaje || "He procesado tu respuesta.";
        historialConversacion.push({ rol: "ia", texto: textoIA });
        removerElemento(idCarga);
        agregarMensajeIA(datos);
    } catch (error) {
        removerElemento(idCarga);
        agregarMensajeError(error.message);
    } finally {
        btnEnviar.disabled = false;
        btnEnviar.style.opacity = '1';
        promptInput.focus();
        scrollAlFondo();
    }
}
function agregarMensajeUsuario(texto) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.style.flexDirection = 'row-reverse';
    div.innerHTML = `<div class="avatar" style="background:#1e293b">👩🏻‍💻</div><div class="contenido" style="background:#1e293b"><p>${escaparHTML(texto)}</p></div>`;
    chatBox.appendChild(div);
}
function agregarMensajeCarga() {
    const id = 'carga-' + Date.now();
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.id = id;
    div.innerHTML = `<div class="avatar">🤖</div><div class="contenido"><p>⏳ <em>StudNova IA está respondiendo...</em></p></div>`;
    chatBox.appendChild(div);
    return id;
}
function agregarMensajeIA(datos) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    const tienePlan = (datos.tipo === "plan_generado") || (datos.plan && datos.plan.modulos && datos.plan.modulos.length > 0) || (datos.modulos && datos.modulos.length > 0);
    if (!tienePlan) {
        const mensajeTexto = datos.mensaje || (typeof datos === 'string' ? datos : "Cuéntame más sobre lo que quieres aprender.");
        div.innerHTML = `<div class="avatar">🤖</div><div class="contenido"><p>${escaparHTML(mensajeTexto)}</p></div>`;
    } else {
        const planObjeto = datos.plan || datos;
        localStorage.setItem("plan_estudio_actual", JSON.stringify(planObjeto));
        const mensajeTexto = datos.mensaje || "✨ ¡Plan de estudio generado con éxito!";
        div.innerHTML = `<div class="avatar">🤖</div><div class="contenido" style="width: 85%;"><p><strong>${escaparHTML(mensajeTexto)}</strong></p><p style="margin-top: 5px; font-size: 14px; opacity: 0.9;">He estructurado tu ruta de aprendizaje a tu medida con quizzes y control de fatiga.</p><div style="margin: 12px 0;"><a href="/principal/interfaz plan de estudio/visor_plan.html" target="_blank" style="display:inline-block; padding: 8px 16px; background:#2563eb; color:white; text-decoration:none; border-radius:8px; font-weight:bold; font-size:14px;">↗️ Abrir Plan en Pantalla Completa</a></div><div style="border-radius: 10px; overflow: hidden; border: 1px solid #334155; margin-top: 10px;"><iframe src="/principal/interfaz plan de estudio/visor_plan.html" style="width: 100%; height: 500px; border: none; background: #0f172a;"></iframe></div></div>`;
    }
    chatBox.appendChild(div);
}
function agregarMensajeError(mensaje) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.innerHTML = `<div class="avatar" style="background:#dc2626;">⚠️</div><div class="contenido" style="background:#7f1d1d;"><p><strong>Error:</strong> ${escaparHTML(mensaje)}</p></div>`;
    chatBox.appendChild(div);
}
function removerElemento(id) { const el = document.getElementById(id); if (el) el.remove(); }
function scrollAlFondo() { chatBox.scrollTop = chatBox.scrollHeight; }
function escaparHTML(str) { return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }