// principal/interfaz plan de estudio/java.js

let planActualGlobal = null;

function getSesionUsuarioId() {
    try {
        const raw = localStorage.getItem("studnova:session") || localStorage.getItem("user");
        if (raw) {
            const parsed = JSON.parse(raw);
            return parsed.id_usuario || parsed.id || null;
        }
    } catch (e) {}
    return null;
}

function renderizarPlan(plan) {
    if (!plan) return;
    if (plan.plan_json) plan = plan.plan_json;
    if (plan.contenido_json) plan = plan.contenido_json;
    if (plan.plan) plan = plan.plan;
    if (plan.contenido_json) plan = plan.contenido_json;
    planActualGlobal = plan;

    // Header
    const titulo = plan.titulo || "Plan de Estudio Personalizado";
    const materia = plan.materia || "Ruta de Aprendizaje";
    const descripcion = plan.descripcion || "Lecciones teóricas, ejemplos prácticos y ejercicios resueltos paso a paso.";
    const fatiga = plan.recomendacion_fatiga || "Estudia 25 min y realiza pausas activas de 5 min.";

    if (document.getElementById('titulo-plan')) document.getElementById('titulo-plan').innerText = titulo;
    if (document.getElementById('badge-materia')) document.getElementById('badge-materia').innerText = materia;
    if (document.getElementById('descripcion-plan')) document.getElementById('descripcion-plan').innerText = descripcion;
    if (document.getElementById('estado-fatiga')) document.getElementById('estado-fatiga').innerText = fatiga;

    const listaModulos = plan.modulos || [];
    const contenedor = document.getElementById('contenedor-modulos');
    if (!contenedor) return;

    contenedor.innerHTML = '';

    listaModulos.forEach((modulo, index) => {
        const idMod = modulo.id || `mod-${index + 1}`;
        const tituloMod = modulo.titulo || `Módulo ${index + 1}`;
        const tagNivel = modulo.nivel_tag || (index === 0 ? 'Nivel 1: Fundamentos' : index === 1 ? 'Nivel 2: Básico' : `Nivel ${index + 1}`);
        const claseNivel = modulo.nivel_clase || (index === 0 ? 'basico' : index === 1 ? 'intermedio' : 'avanzado');

        // A. Resumen Teórico del Módulo
        let htmlTeoriaModulo = '';
        if (modulo.teoria_modulo || modulo.teoria || modulo.objetivo) {
            const txt = modulo.teoria_modulo || modulo.teoria || modulo.objetivo;
            htmlTeoriaModulo = `
                <div style="background: #172033; border-left: 4px solid #2563eb; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                    <strong style="color: #60a5fa; font-size: 14px; display: block; margin-bottom: 6px;">📖 Marco Teórico del Módulo:</strong>
                    <p style="color: #cbd5e1; font-size: 13.5px; line-height: 1.6;">${escapar(txt)}</p>
                </div>
            `;
        }

        // B. Lecciones con Contenido Teórico Profundo y Ejemplos
        let htmlLecciones = '';
        const lecciones = modulo.lecciones || modulo.tareas || [];

        lecciones.forEach((lec, lIdx) => {
            const idLec = `lec-${idMod}-${lIdx}`;
            const tituloLec = lec.titulo || `Lección ${lIdx + 1}`;
            const duracion = lec.duracion_minutos || 45;
            const idModDB = modulo.id_modulo || (index + 1);
            const idTemaDB = lec.id_tema || (lIdx + 1);

            // Extraer teoría y detalles
            const teoria = lec.concepto_teorico || (lec.guia_aprendizaje && lec.guia_aprendizaje.explicacion_teorica) || lec.detalle || '';
            const puntos = lec.puntos_clave || (lec.guia_aprendizaje && lec.guia_aprendizaje.puntos_clave) || [];
            const codigo = lec.ejemplo_codigo_o_formula || (lec.guia_aprendizaje && lec.guia_aprendizaje.ejemplo_explicado) || '';
            const ejercicio = lec.ejercicio_practico || (lec.guia_aprendizaje && lec.guia_aprendizaje.ejercicio_resuelto) || null;

            // Puntos clave
            let puntosHTML = '';
            if (puntos.length > 0) {
                puntosHTML = `
                    <div style="margin-top: 10px;">
                        <strong style="color: #60a5fa; font-size: 13px;">💡 Puntos Clave y Reglas:</strong>
                        <ul style="margin: 6px 0 0 18px; color: #cbd5e1; font-size: 13px; line-height: 1.5;">
                            ${puntos.map(p => `<li>${escapar(p)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            // Código
            let codigoHTML = '';
            if (codigo) {
                codigoHTML = `
                    <div style="margin-top: 12px;">
                        <strong style="color: #38bdf8; font-size: 13px;">💻 Código / Ejemplo Explicado:</strong>
                        <pre style="background: #0b1120; border: 1px solid #334155; color: #38bdf8; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 13px; overflow-x: auto; margin-top: 6px; white-space: pre-wrap;"><code>${escapar(codigo)}</code></pre>
                    </div>
                `;
            }

            // Ejercicio y solución
            let ejercicioHTML = '';
            if (ejercicio) {
                const enunciado = ejercicio.enunciado || (typeof ejercicio === 'string' ? ejercicio : '');
                const solucion = ejercicio.solucion_paso_a_paso || ejercicio.solucion || '';
                ejercicioHTML = `
                    <div style="margin-top: 12px; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 14px;">
                        <strong style="color: #34d399; font-size: 13px;">✍️ Ejercicio de Práctica:</strong>
                        <p style="color: #f8fafc; font-size: 13px; margin: 6px 0;">${escapar(enunciado)}</p>
                        ${solucion ? `
                            <details style="margin-top: 8px; background: #0f172a; border: 1px dashed #10b981; border-radius: 6px; padding: 8px 12px; cursor: pointer;">
                                <summary style="color: #34d399; font-size: 12.5px; font-weight: bold;">🔍 Ver Solución Paso a Paso</summary>
                                <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #334155; color: #f1f5f9; font-size: 13px; white-space: pre-line;">${escapar(solucion)}</div>
                            </details>
                        ` : ''}
                    </div>
                `;
            }

            htmlLecciones += `
                <div class="tarea-contenedor" style="margin-bottom: 12px;">
                    <div class="tarea-item" style="display: flex; justify-content: space-between; align-items: center;">
                        <label style="display: flex; align-items: center; gap: 12px; cursor: pointer; flex: 1;">
                            <input type="checkbox" data-modulo="${idModDB}" data-tema="${idTemaDB}" onchange="actualizarProgreso(this); autoIniciarTimer();">
                            <span class="check-custom"></span>
                            <div class="tarea-texto">
                                <strong>${escapar(tituloLec)}</strong>
                                <small>⏱️ ${duracion} min • Contenido y práctica</small>
                            </div>
                        </label>
                        <button type="button" class="btn-ver-guia" onclick="alternarGuia('${idLec}', this); autoIniciarTimer();">📖 Abrir Lección</button>
                    </div>

                    <!-- Panel de la Lección Completa -->
                    <div class="guia-aprendizaje-drawer" id="${idLec}" style="display: none; background: #0f172a; border: 1.5px solid #3b82f6; border-radius: 12px; padding: 18px; margin-top: 6px;">
                        <div style="font-size: 13.5px; line-height: 1.6; color: #f1f5f9;">
                            <strong style="color: #60a5fa; font-size: 14px; display: block; margin-bottom: 6px;">📚 Concepto y Explicación:</strong>
                            <p style="white-space: pre-line; color: #cbd5e1;">${escapar(teoria)}</p>
                            ${puntosHTML}
                            ${codigoHTML}
                            ${ejercicioHTML}
                        </div>
                    </div>
                </div>
            `;
        });

        // C. Mini Quizzes
        let htmlQuizzes = '';
        const quizzes = modulo.mini_quizzes || (modulo.quiz ? [modulo.quiz] : []);

        quizzes.forEach((quizObj, qIdx) => {
            const tituloQ = quizObj.titulo || `Comprobación ${qIdx + 1}`;
            const pregunta = quizObj.pregunta || "¿Pregunta de evaluación?";
            const opciones = quizObj.opciones || [];
            const correcta = quizObj.indice_correcto ?? 0;

            let botones = '';
            opciones.forEach((opc, opcIdx) => {
                botones += `<button onclick="verificarRespuesta(this, ${opcIdx}); autoIniciarTimer();">${escapar(opc)}</button>`;
            });

            htmlQuizzes += `
                <div class="quiz-box" style="margin-top: 16px;">
                    <h4>🧪 ${escapar(tituloQ)}</h4>
                    <p>${escapar(pregunta)}</p>
                    <div class="opciones-quiz" data-correcta="${correcta}">
                        ${botones}
                    </div>
                    <div class="feedback-quiz"></div>
                </div>
            `;
        });

        // D. Tarjeta del Módulo
        const htmlModulo = `
            <section class="modulo-card" id="card-${idMod}">
                <div class="modulo-header" onclick="alternarModulo('${idMod}'); autoIniciarTimer();">
                    <div class="modulo-titulo-area">
                        <span class="nivel-tag ${claseNivel}">${escapar(tagNivel)}</span>
                        <h2>${escapar(tituloMod)}</h2>
                    </div>
                    <span class="flecha" id="flecha-${idMod}">▼</span>
                </div>
                
                <div class="modulo-contenido" id="${idMod}">
                    ${htmlTeoriaModulo}
                    <div class="lista-tareas">
                        ${htmlLecciones}
                    </div>
                    ${htmlQuizzes}
                </div>
            </section>
        `;

        contenedor.innerHTML += htmlModulo;
    });

    actualizarProgreso();
    restaurarEstadoProgresoLocal();
}

function alternarGuia(idLec, boton) {
    const guia = document.getElementById(idLec);
    if (!guia) return;

    if (guia.style.display === 'none') {
        guia.style.display = 'block';
        boton.innerText = "✖ Cerrar Lección";
        boton.style.background = "#475569";

        // Marcar AUTOMÁTICAMENTE la lección como completada al abrirla para estudiar
        const tareaContenedor = boton.closest('.tarea-contenedor');
        if (tareaContenedor) {
            const chk = tareaContenedor.querySelector('input[type="checkbox"]');
            if (chk && !chk.checked) {
                chk.checked = true;
                actualizarProgreso(chk);
                guardarEstadoProgresoLocal();
            }
        }
    } else {
        guia.style.display = 'none';
        boton.innerText = "📖 Abrir Lección";
        boton.style.background = "#2563eb";
    }
}

function escapar(str) {
    if (!str) return '';
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function actualizarProgreso(checkboxEl) {
    const checkboxes = document.querySelectorAll('.tarea-item input[type="checkbox"]');
    const total = checkboxes.length;
    let marcadas = 0;
    checkboxes.forEach(chk => { if (chk.checked) marcadas++; });

    const porcentaje = total > 0 ? Math.round((marcadas / total) * 100) : 0;
    const elBarra = document.getElementById('barra-progreso');
    const elTexto = document.getElementById('porcentaje-texto');
    const elContador = document.getElementById('contador-tareas');

    if (elBarra) elBarra.style.width = porcentaje + '%';
    if (elTexto) elTexto.innerText = porcentaje + '%';
    if (elContador) elContador.innerText = `${marcadas} de ${total} lecciones completadas`;

    // Comprobar módulos completados al 100%
    document.querySelectorAll('.modulo-card').forEach(card => {
        const totalMod = card.querySelectorAll('input[type="checkbox"]').length;
        const marcadasMod = card.querySelectorAll('input[type="checkbox"]:checked').length;
        if (totalMod > 0 && totalMod === marcadasMod) {
            marcarCardComoCompletada(card);
        }
    });

    guardarEstadoProgresoLocal();

    // Persistencia en el backend (PostgreSQL)
    if (checkboxEl) {
        const idUsuario = getSesionUsuarioId();
        const params = new URLSearchParams(window.location.search);
        const idPlan = (planActualGlobal && planActualGlobal.id_plan) || params.get('id');
        const idModulo = parseInt(checkboxEl.getAttribute('data-modulo')) || 1;
        const idTema = parseInt(checkboxEl.getAttribute('data-tema')) || 1;

        if (idUsuario && idPlan) {
            fetch(`${API_BASE}/progreso/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id_usuario: parseInt(idUsuario),
                    id_plan: parseInt(idPlan),
                    id_modulo: idModulo,
                    id_tema: idTema,
                    porcentaje: parseFloat(porcentaje),
                    completado: checkboxEl.checked
                })
            }).catch(err => console.warn("Aviso: no se pudo guardar progreso en backend:", err));
        }
    }
}

function completarModulo(idMod, evento) {
    if (evento && evento.stopPropagation) evento.stopPropagation();
    const contenido = document.getElementById(idMod);
    if (!contenido) return;

    // 1. Marcar automáticamente todas las tareas de este módulo
    const checks = contenido.querySelectorAll('input[type="checkbox"]');
    checks.forEach(chk => { chk.checked = true; });

    // 2. Resolver quizzes del módulo si existen
    const quizzes = contenido.querySelectorAll('.quiz-box');
    quizzes.forEach(qb => {
        const opcionesDiv = qb.querySelector('.opciones-quiz');
        if (opcionesDiv) {
            const correcta = parseInt(opcionesDiv.getAttribute('data-correcta')) || 0;
            const botones = opcionesDiv.querySelectorAll('button');
            botones.forEach(b => b.disabled = true);
            if (botones[correcta]) botones[correcta].classList.add('correcto');
        }
        const fb = qb.querySelector('.feedback-quiz');
        if (fb) fb.innerHTML = '<span style="color: #34d399;">✅ Módulo y comprobación completados.</span>';
    });

    // 3. Subir automáticamente la barra de progreso
    actualizarProgreso();

    // 4. Marcar tarjeta visualmente
    const moduloCard = contenido.closest('.modulo-card');
    if (moduloCard) {
        marcarCardComoCompletada(moduloCard);
    }
}

function marcarCardComoCompletada(moduloCard) {
    if (!moduloCard) return;
    moduloCard.classList.add('modulo-completado');
    const tituloArea = moduloCard.querySelector('.modulo-titulo-area');
    if (tituloArea && !tituloArea.querySelector('.badge-completado')) {
        const badge = document.createElement('span');
        badge.className = 'badge-completado';
        badge.innerText = '✔️ Completado';
        badge.style.cssText = 'background: #065f46; color: #34d399; font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: bold; margin-left: 8px; vertical-align: middle;';
        tituloArea.appendChild(badge);
    }
}

function guardarEstadoProgresoLocal() {
    try {
        const idPlan = (planActualGlobal && planActualGlobal.id_plan) || (new URLSearchParams(window.location.search)).get('id') || 'actual';
        const checkboxes = document.querySelectorAll('.tarea-item input[type="checkbox"]');
        const estados = [];
        checkboxes.forEach((chk, idx) => {
            if (chk.checked) estados.push(idx);
        });
        localStorage.setItem(`studnova_progreso_plan_${idPlan}`, JSON.stringify(estados));
    } catch (e) {
        console.warn("Aviso al guardar progreso local:", e);
    }
}

function restaurarEstadoProgresoLocal() {
    try {
        const idPlan = (planActualGlobal && planActualGlobal.id_plan) || (new URLSearchParams(window.location.search)).get('id') || 'actual';
        const guardado = localStorage.getItem(`studnova_progreso_plan_${idPlan}`);
        if (guardado) {
            const indices = JSON.parse(guardado);
            const checkboxes = document.querySelectorAll('.tarea-item input[type="checkbox"]');
            indices.forEach(idx => {
                if (checkboxes[idx]) checkboxes[idx].checked = true;
            });
            actualizarProgreso();
        }
    } catch (e) {
        console.warn("Aviso al restaurar progreso local:", e);
    }
}

function alternarModulo(id) {
    const contenido = document.getElementById(id);
    const flecha = document.getElementById('flecha-' + id);
    if (!contenido) return;

    if (contenido.style.display === 'none') {
        contenido.style.display = 'flex';
        if (flecha) flecha.style.transform = 'rotate(0deg)';
    } else {
        contenido.style.display = 'none';
        if (flecha) flecha.style.transform = 'rotate(-90deg)';
    }
}

function verificarRespuesta(boton, indiceSeleccionado) {
    const contenedorOpciones = boton.parentElement;
    const indiceCorrecto = parseInt(contenedorOpciones.getAttribute('data-correcta'));
    const botones = contenedorOpciones.querySelectorAll('button');
    const feedback = contenedorOpciones.nextElementSibling;

    botones.forEach(btn => btn.disabled = true);

    if (indiceSeleccionado === indiceCorrecto) {
        boton.classList.add('correcto');
        feedback.innerHTML = '<span style="color: #34d399;">✅ ¡Correcto! Módulo completado automáticamente.</span>';

        // AUTOMÁTICAMENTE completar lecciones de este módulo al superar la comprobación
        const moduloContenedor = boton.closest('.modulo-contenido');
        if (moduloContenedor) {
            const checks = moduloContenedor.querySelectorAll('input[type="checkbox"]');
            checks.forEach(chk => { chk.checked = true; });
            actualizarProgreso();

            const moduloCard = moduloContenedor.closest('.modulo-card');
            if (moduloCard) {
                marcarCardComoCompletada(moduloCard);
            }
        }
    } else {
        boton.classList.add('incorrecto');
        if (botones[indiceCorrecto]) botones[indiceCorrecto].classList.add('correcto');
        feedback.innerHTML = '<span style="color: #f87171;">❌ Respuesta incorrecta. Revisa la opción resaltada en verde.</span>';
    }
}

// Pomodoro
let tiempoSegundos = 25 * 60;
let intervalo = null;
let enPausa = true;
let timerIniciadoPreviamente = false;

function autoIniciarTimer() {
    if (!timerIniciadoPreviamente && enPausa) {
        timerIniciadoPreviamente = true;
        alternarTimer();
        const estado = document.getElementById('estado-fatiga');
        if (estado) estado.innerText = "⚡ Sesión iniciada automáticamente por interacción. ¡Enfócate!";
    }
}

function alternarTimer() {
    const btn = document.getElementById('btn-timer');
    const estado = document.getElementById('estado-fatiga');

    if (enPausa) {
        enPausa = false;
        if (btn) btn.innerText = "Pausar";
        if (estado) estado.innerText = "Sesión activa de enfoque. ¡Concéntrate!";
        intervalo = setInterval(() => {
            if (tiempoSegundos > 0) {
                tiempoSegundos--;
                actualizarDisplayTimer();
            } else {
                clearInterval(intervalo);
                alert("🔔 ¡Sesión completada! Toma una pausa activa de 5 minutos.");
                tiempoSegundos = 5 * 60;
                enPausa = true;
                if (btn) btn.innerText = "Iniciar Descanso";
                actualizarDisplayTimer();

                // Registrar sesión y control de fatiga en el backend
                const idUsuario = getSesionUsuarioId();
                const params = new URLSearchParams(window.location.search);
                const idPlan = (planActualGlobal && planActualGlobal.id_plan) || params.get('id');
                if (idUsuario && idPlan) {
                    fetch(`${API_BASE}/sesion-estudio/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id_usuario: parseInt(idUsuario),
                            id_plan: parseInt(idPlan),
                            id_modulo: 1,
                            id_tema: 1,
                            duracion_minutos: 25,
                            completada: true
                        })
                    }).catch(e => console.warn(e));

                    fetch(`${API_BASE}/control-fatiga/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            id_usuario: parseInt(idUsuario),
                            id_plan: parseInt(idPlan),
                            nivel_fatiga: 2,
                            observacion: "Pausa activa recomendada tras 25 min de estudio completados"
                        })
                    }).catch(e => console.warn(e));
                }
            }
        }, 1000);
    } else {
        enPausa = true;
        clearInterval(intervalo);
        if (btn) btn.innerText = "Continuar";
        if (estado) estado.innerText = "Sesión en pausa.";
    }
}

function actualizarDisplayTimer() {
    const minutos = Math.floor(tiempoSegundos / 60);
    const segundos = tiempoSegundos % 60;
    const el = document.getElementById('temporizador');
    if (el) el.innerText = `${minutos.toString().padStart(2, '0')}:${segundos.toString().padStart(2, '0')}`;
}

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

// Escuchar mensajes desde ventana padre (iframe o postMessage)
window.addEventListener("message", (evento) => {
    if (evento.data && (evento.data.tipo === "CARGAR_PLAN" || evento.data.plan)) {
        const planRecibido = evento.data.plan || evento.data;
        try {
            localStorage.setItem("plan_estudio_actual", JSON.stringify(planRecibido));
        } catch (e) {}
        renderizarPlan(planRecibido);
    }
});

function volverAlChat(e) {
    if (e && e.preventDefault) e.preventDefault();

    // 1. Si se abrió en una pestaña secundaria desde el chat, enfocar padre y cerrar
    if (window.opener && !window.opener.closed) {
        try {
            window.opener.focus();
            window.close();
            return;
        } catch (err) {
            console.warn("No se pudo cerrar la ventana secundaria:", err);
        }
    }

    // 2. Si el navegador tiene historial de navegación hacia el chat
    if (window.history.length > 1) {
        window.history.back();
        return;
    }

    // 3. Fallback: redirigir a la interfaz del chat
    window.location.href = '/ia/interfaz.html';
}

document.addEventListener("DOMContentLoaded", async () => {
    // Si estamos dentro de un iframe (chat embebido), ocultar el botón volver
    if (window.self !== window.top) {
        const btnVolver = document.querySelector('.btn-volver');
        if (btnVolver) btnVolver.style.display = 'none';
    }

    // 1. Si estamos en un iframe, solicitar el plan al padre inmediatamente
    if (window.parent && window.parent !== window) {
        try {
            window.parent.postMessage({ tipo: 'SOLICITAR_PLAN' }, '*');
            if (window.parent.ultimoPlanGenerado) {
                renderizarPlan(window.parent.ultimoPlanGenerado);
                return;
            }
        } catch (e) {}
    }

    // 2. Intentar cargar desde localStorage
    const guardado = localStorage.getItem("plan_estudio_actual");
    if (guardado) {
        try {
            const planParsed = JSON.parse(guardado);
            if (planParsed && (planParsed.modulos || (planParsed.plan && planParsed.plan.modulos) || planParsed.contenido_json)) {
                renderizarPlan(planParsed);
                return;
            }
        } catch (e) {
            console.error("Error leyendo localStorage:", e);
        }
    }

    // 3. Fallback: Buscar id en la URL (?id=X o #id=X) y consultar backend
    const params = new URLSearchParams(window.location.search);
    const idPlan = params.get('id') || (window.location.hash ? window.location.hash.replace('#id=', '').replace('#', '') : null);
    if (idPlan && !isNaN(idPlan)) {
        try {
            const respuesta = await fetch(`${API_BASE}/plan-estudio/${idPlan}`);
            if (respuesta.ok) {
                const data = await respuesta.json();
                const targetPlan = data.contenido_json || data.plan;
                if (targetPlan) {
                    renderizarPlan(targetPlan);
                    try { localStorage.setItem("plan_estudio_actual", JSON.stringify(targetPlan)); } catch (e) {}
                }
            }
        } catch (err) {
            console.error("Error al consultar plan por ID:", err);
        }
    }
});