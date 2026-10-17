const API_URL = (window.location.protocol === "http:" || window.location.protocol === "https:") && window.location.port === "8000"
    ? ""
    : "http://127.0.0.1:8000";
const SESSION_KEY = "studnova:session";

// ==========================================
// GUARDAR SESIÓN
// ==========================================

function guardarSesion(usuario) {
    const session = {
        id_usuario: usuario.id_usuario,
        nombre: usuario.nombre,
        correo: usuario.correo,
        rol: usuario.rol,
        since: Date.now()
    };

    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    localStorage.setItem("user", JSON.stringify(usuario));
    localStorage.setItem("id_usuario", usuario.id_usuario);
    localStorage.setItem("userEmail", usuario.correo);
    localStorage.setItem("userName", usuario.nombre);
    localStorage.setItem("isLoggedIn", "true");
}


// ==========================================
// OBTENER SESIÓN
// ==========================================

function obtenerSesion() {
    try {
        const raw = localStorage.getItem(SESSION_KEY);
        return raw ? JSON.parse(raw) : null;
    } catch (error) {
        console.error("Error leyendo la sesión:", error);
        return null;
    }
}


// ==========================================
// MOSTRAR LOGIN / REGISTRO
// ==========================================

function mostrarFormulario(id) {
    document.querySelectorAll(".form-container").forEach(form => {
        form.classList.remove("active");
    });

    const el = document.getElementById(id);
    if (el) el.classList.add("active");
}


// ==========================================
// REDIRECCIÓN INTELIGENTE
// ==========================================

function irAInterfaz() {
    window.location.href = "/ia/interfaz.html";
}


// ==========================================
// LOGIN (INICIAR SESIÓN)
// ==========================================

document.getElementById("formLogin").addEventListener("submit", async (e) => {
    e.preventDefault();

    const mensaje = document.getElementById("loginMensaje");
    const correo = document.getElementById("loginCorreo").value.trim().toLowerCase();
    const contraseña = document.getElementById("loginPassword").value;

    mensaje.hidden = false;
    mensaje.textContent = "Iniciando sesión...";
    mensaje.className = "form-mensaje";
    mensaje.style.color = "#93c5fd";

    try {
        const respuesta = await fetch(`${API_URL}/usuario/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                correo: correo,
                contraseña: contraseña
            })
        });

        const data = await respuesta.json();

        if (!respuesta.ok) {
            if (respuesta.status === 401) {
                throw new Error("Correo o contraseña incorrectos.");
            }
            throw new Error(data.detail || "No se pudo iniciar sesión.");
        }

        // Guardar sesión en localStorage
        guardarSesion(data);

        mensaje.textContent = `¡Bienvenido, ${data.nombre}! Entrando a la plataforma...`;
        mensaje.style.color = "lightgreen";

        // Ir a la interfaz
        setTimeout(() => {
            irAInterfaz();
        }, 600);

    } catch (error) {
        console.error("Error al iniciar sesión:", error);
        mensaje.hidden = false;
        mensaje.className = "form-mensaje error";
        mensaje.style.color = "#E9938A";

        if (error instanceof TypeError) {
            mensaje.textContent = "No se pudo conectar con el servidor backend. Verifica que FastAPI esté corriendo en http://127.0.0.1:8000.";
        } else {
            mensaje.textContent = error.message;
        }
    }
});


// ==========================================
// REGISTRO (CREAR CUENTA)
// ==========================================

document.getElementById("formRegister").addEventListener("submit", async (e) => {
    e.preventDefault();

    const mensajeRegister = document.getElementById("registerMensaje");
    const mensajeLogin = document.getElementById("loginMensaje");
    const nombre = document.getElementById("registerNombre").value.trim();
    const correo = document.getElementById("registerCorreo").value.trim().toLowerCase();
    const contraseña = document.getElementById("registerPassword").value;

    mensajeRegister.hidden = false;
    mensajeRegister.textContent = "Creando cuenta en el servidor...";
    mensajeRegister.className = "form-mensaje";
    mensajeRegister.style.color = "#93c5fd";

    try {
        const respuesta = await fetch(`${API_URL}/usuario/registro`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                nombre: nombre,
                correo: correo,
                contraseña: contraseña
            })
        });

        const data = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(data.detail || "No se pudo crear la cuenta.");
        }

        // Cuenta creada exitosamente en la base de datos PostgreSQL
        mensajeRegister.textContent = "¡Cuenta creada exitosamente! Cambiando a inicio de sesión...";
        mensajeRegister.style.color = "lightgreen";

        // Prellenar el formulario de login con el correo recién registrado
        const loginCorreoInput = document.getElementById("loginCorreo");
        const loginPasswordInput = document.getElementById("loginPassword");
        if (loginCorreoInput) loginCorreoInput.value = correo;
        if (loginPasswordInput) {
            loginPasswordInput.value = "";
        }

        // Limpiar el formulario de registro
        document.getElementById("formRegister").reset();

        // Cambiar automáticamente a la vista de login tras 1 segundo para que el usuario inicie sesión
        setTimeout(() => {
            mostrarFormulario("login");
            if (mensajeLogin) {
                mensajeLogin.hidden = false;
                mensajeLogin.textContent = `¡Cuenta creada para ${data.nombre}! Ingresa tu contraseña para entrar.`;
                mensajeLogin.style.color = "lightgreen";
            }
            if (loginPasswordInput) loginPasswordInput.focus();
        }, 1000);

    } catch (error) {
        console.error("Error al registrar cuenta:", error);
        mensajeRegister.hidden = false;
        mensajeRegister.className = "form-mensaje error";
        mensajeRegister.style.color = "#E9938A";

        if (error instanceof TypeError) {
            mensajeRegister.textContent = "No se pudo conectar con el servidor backend. Verifica que FastAPI esté corriendo en http://127.0.0.1:8000.";
        } else {
            mensajeRegister.textContent = error.message;
        }
    }
});
