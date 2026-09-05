const API_URL = "http://127.0.0.1:8000";
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

    document.getElementById(id).classList.add("active");
}


// ==========================================
// REDIRECCIÓN
// ==========================================

function irAInterfaz() {
    window.location.href = "../ia/interfaz.html";
}


// ==========================================
// SI YA HAY SESIÓN
// ==========================================
//
function irAInterfaz() {
    window.location.replace("http://127.0.0.1:5501/ia/interfaz.html");
}


// ==========================================
// LOGIN
// ==========================================

document.getElementById("formLogin").addEventListener("submit", async (e) => {
    e.preventDefault();

    const mensaje = document.getElementById("loginMensaje");

    const correo = document.getElementById("loginCorreo").value.trim();
    const contraseña = document.getElementById("loginPassword").value;

    mensaje.textContent = "Iniciando sesión...";
    mensaje.className = "form-mensaje";

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
            throw new Error(data.detail || "No se pudo iniciar sesión.");
        }

        // Guardar usuario
        guardarSesion(data);

        mensaje.textContent = "Inicio de sesión exitoso.";

        // Ir a la interfaz
        setTimeout(() => {
            irAInterfaz();
        }, 500);

    } catch (error) {

        console.error(error);

        mensaje.textContent = error.message;
        mensaje.className = "form-mensaje error";
    }
});


// ==========================================
// REGISTRO
// ==========================================

document.getElementById("formRegister").addEventListener("submit", async (e) => {
    e.preventDefault();

    const mensaje = document.getElementById("registerMensaje");

    const nombre = document.getElementById("registerNombre").value.trim();
    const correo = document.getElementById("registerCorreo").value.trim();
    const contraseña = document.getElementById("registerPassword").value;

    mensaje.hidden = false;
    mensaje.textContent = "Creando cuenta...";
    mensaje.className = "form-mensaje";

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

        // Guardar sesión automáticamente
        guardarSesion(data);

        mensaje.textContent = "Cuenta creada correctamente.";

        // Ir a la interfaz
        setTimeout(() => {
            irAInterfaz();
        }, 500);

    } catch (error) {

        console.error(error);

        mensaje.textContent = error.message;
        mensaje.className = "form-mensaje error";
    }
});