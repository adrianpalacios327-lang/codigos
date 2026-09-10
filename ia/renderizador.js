// --- CONFIGURACIÓN BASE ---
const API_BASE_URL = "[http://127.0.0.1:8000](http://127.0.0.1:8000)";
const ID_USUARIO = localStorage.getItem("id_usuario") || 1; 

// --- ELEMENTOS DEL DOM ---
const chatBox = document.getElementById('chat-box');
const promptInput = document.getElementById('prompt-input');
const btnEnviar = document.getElementById('btn-enviar');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
const historyList = document.getElementById('history-list');

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', () => {
    cargarHistorialPlanes();
});

// --- CERRAR SESIÓN ---
function cerrarSesion() {
    if (!confirm("¿Seguro que quieres cerrar sesión?")) return;
    localStorage.clear();
    sessionStorage.clear();
    window.location.href = "/login/login.html";
}

// --- CONTROL DEL MENÚ HAMBURGUESA ---
function toggleMenu() {
    if (sidebar) sidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
}

// --- CARGAR HISTORIAL DE PLANES (BASE DE DATOS) ---
async function cargarHistorialPlanes() {
    if (!historyList) return;
    
    try {
        const respuesta = await fetch(`${API_BASE_URL}/plan-estudio/usuario/${ID_USUARIO}`);
        
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
            const li = document.createElement('li');
            li.className = 'history-item';
            
            const fechaFormateada = plan.fecha_creacion 
                ? new Date(plan.fecha_creacion).toLocaleDateString() 
                : 'Reciente';

            li.onclick = () => cargarPlanSeleccionado(plan);
            li.innerHTML = `
                <div class="plan-info">
                    <span class="plan-title">${escaparHTML(plan.titulo || 'Plan de Estudio')}</span>
                    <span class="plan-date">${plan.nivel_objetivo || 'Intermedio'} • ${fechaFormateada}</span>
                </div>
            `;
            historyList.appendChild(li);
        });

    } catch (error) {
        console.error("Error al cargar historial:", error);
        historyList.innerHTML = '<li class="sin-planes texto-error">Error al cargar planes.</li>';
    }
}

function cargarPlanSeleccionado(plan) {
    localStorage.setItem("plan_estudio_actual", JSON.stringify(plan));
    window.open('/principal/interfaz plan de estudio/visor_plan.html', '_blank');
}

// --- ENVIAR MENSAJES Y CHAT ---
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
    promptInput.value = '';
    btnEnviar.disabled = true;
    btnEnviar.style.opacity = '0.5';

    const idCarga = agregarMensajeCarga();
    scrollAlFondo();

    try {
        const respuesta = await fetch(`${API_BASE_URL}/prompt-ia/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mensaje: texto,
                id_usuario: parseInt(ID_USUARIO)
            })
        });

        if (!respuesta.ok) throw new Error("Error en la solicitud al servidor.");

        const datos = await respuesta.json();
        removerElemento(idCarga);

        if (datos.tipo === "plan_generado") {
            // Guardar plan actual en localStorage y refrescar el panel lateral con la DB
            localStorage.setItem("plan_estudio_actual", JSON.stringify(datos.plan));
            cargarHistorialPlanes();

            agregarMensajeIARespuestaPlan(datos);
        } else {
            // Mostrar respuesta normal de texto
            agregarMensajeIATexto(datos.respuesta || "Respuesta procesada.");
        }

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

// --- FUNCIONES DE MOSTRAR MENSAJES ---
function agregarMensajeUsuario(texto) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.style.flexDirection = 'row-reverse';
    div.innerHTML = `
        <div class="avatar" style="background:#1e293b">👩🏻‍💻</div>
        <div class="contenido" style="background:#1e293b"><p>${escaparHTML(texto)}</p></div>
    `;
    chatBox.appendChild(div);
}

function agregarMensajeCarga() {
    const id = 'carga-' + Date.now();
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.id = id;
    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="contenido"><p>⏳ <em>StudNova IA está respondiendo...</em></p></div>
    `;
    chatBox.appendChild(div);
    return id;
}

function agregarMensajeIATexto(texto) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="contenido"><p>${escaparHTML(texto)}</p></div>
    `;
    chatBox.appendChild(div);
}

function agregarMensajeIARespuestaPlan(datos) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="contenido" style="width: 85%;">
            <p><strong>${escaparHTML(datos.respuesta)}</strong></p>
            <p style="margin-top: 5px; font-size: 14px; opacity: 0.9;">
                He guardado tu nueva ruta de aprendizaje en la base de datos. Puedes verla integrada a continuación:
            </p>
            <div style="margin: 12px 0;">
                <a href="/principal/interfaz plan de estudio/visor_plan.html" target="_blank" style="display:inline-block; padding: 8px 16px; background:#2563eb; color:white; text-decoration:none; border-radius:8px; font-weight:bold; font-size:14px;">↗️ Abrir Plan en Pantalla Completa</a>
            </div>
            <div style="border-radius: 10px; overflow: hidden; border: 1px solid #334155; margin-top: 10px;">
                <iframe src="/principal/interfaz plan de estudio/visor_plan.html" style="width: 100%; height: 500px; border: none; background: #0f172a;"></iframe>
            </div>
        </div>
    `;
    chatBox.appendChild(div);
}

function agregarMensajeError(mensaje) {
    const div = document.createElement('div');
    div.className = 'mensaje';
    div.innerHTML = `
        <div class="avatar" style="background:#dc2626;">⚠️</div>
        <div class="contenido" style="background:#7f1d1d;"><p><strong>Error:</strong> ${escaparHTML(mensaje)}</p></div>
    `;
    chatBox.appendChild(div);
}

// --- AUXILIARES ---
function removerElemento(id) { 
    const el = document.getElementById(id); 
    if (el) el.remove(); 
}

function scrollAlFondo() { 
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight; 
}

function escaparHTML(str) { 
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;"); 
}