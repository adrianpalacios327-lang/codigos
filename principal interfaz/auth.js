/* ============================================================
   StudNova — Autenticación
   Registro e inicio de sesión conectados a FastAPI + PostgreSQL

   Backend:
   http://127.0.0.1:8000

   Endpoints:
   POST /usuario/registro
   POST /usuario/login

   La sesión del usuario se mantiene en localStorage.
   ============================================================ */

(function () {
    "use strict";

    /* ============================================================
       CONFIGURACIÓN DE LA API
       ============================================================ */

    const API_URL = window.location.port === "8000" ? "" : "http://127.0.0.1:8000";
    const STORAGE_SESSION = "studnova:session";
    const THEME_STORAGE = "studnova:theme";


    /* ============================================================
       PETICIONES AL BACKEND
       ============================================================ */

    async function apiRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                ...options,
                headers: {
                    "Content-Type": "application/json",
                    ...(options.headers || {})
                }
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(
                    data.detail || "Ocurrió un error en el servidor."
                );
            }

            return data;

        } catch (error) {
            console.error("Error comunicando con StudNova API:", error);

            if (error instanceof TypeError) {
                throw new Error(
                    "No se pudo conectar con el servidor. " +
                    "Verifica que FastAPI esté ejecutándose en el puerto 8000."
                );
            }

            throw error;
        }
    }


    /* ============================================================
       SESIÓN
       ============================================================ */

    function getSession() {
        try {
            const raw = localStorage.getItem(STORAGE_SESSION);
            return raw ? JSON.parse(raw) : null;
        } catch (error) {
            console.error("No se pudo leer la sesión:", error);
            return null;
        }
    }


    function setSession(usuario) {
        const session = {
            id_usuario: usuario.id_usuario,
            nombre: usuario.nombre,
            correo: usuario.correo,
            rol: usuario.rol,
            since: Date.now()
        };

        localStorage.setItem(STORAGE_SESSION, JSON.stringify(session));
        localStorage.setItem("user", JSON.stringify(usuario));
        localStorage.setItem("userEmail", usuario.correo);
        localStorage.setItem("userName", usuario.nombre);
        localStorage.setItem("isLoggedIn", "true");
    }


    function clearSession() {
        localStorage.removeItem(STORAGE_SESSION);
        localStorage.removeItem("user");
        localStorage.removeItem("userEmail");
        localStorage.removeItem("userName");
        localStorage.removeItem("isLoggedIn");
        localStorage.removeItem("loginMethod");
    }


    /* ============================================================
       STUDNOVA SESSION
       ============================================================ */

    window.StudNovaSession = {
        get: function () {
            return getSession();
        },
        save: function (usuario) {
            setSession(usuario);
        },
        clear: function () {
            clearSession();
        },
        isAuthenticated: function () {
            return getSession() !== null;
        },
        openChat: function () {
            if (!this.isAuthenticated()) {
                showToast("Debes iniciar sesión para acceder al chat de IA.", "error");
                openModal("login");
                return;
            }
            // Redirige a la interfaz del chat dentro de la carpeta /ia
            window.location.href = "../ia/interfaz.html";
        }
    };


    /* ============================================================
       UTILIDADES
       ============================================================ */

    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function isValidEmail(value) {
        return EMAIL_RE.test(value.trim());
    }

    function passwordStrength(password) {
        let score = 0;
        if (password.length >= 8) score++;
        if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
        if (/\d/.test(password)) score++;
        if (/[^A-Za-z0-9]/.test(password)) score++;
        return score;
    }

    function initials(name) {
        const parts = name.trim().split(/\s+/).filter(Boolean);
        if (parts.length === 0) return "?";
        if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
        return (parts[0][0] + parts[1][0]).toUpperCase();
    }


    /* ============================================================
       TEMA OSCURO / CLARO
       ============================================================ */

    function initTheme() {
        const saved = localStorage.getItem(THEME_STORAGE);
        const prefersDark = saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches);

        if (prefersDark) {
            document.documentElement.classList.add("dark-mode");
        }
        updateThemeToggle();
    }

    function toggleTheme() {
        const isDark = document.documentElement.classList.toggle("dark-mode");
        localStorage.setItem(THEME_STORAGE, isDark ? "dark" : "light");
        updateThemeToggle();
    }

    function updateThemeToggle() {
        const isDark = document.documentElement.classList.contains("dark-mode");
        const buttons = document.querySelectorAll(".theme-toggle");
        buttons.forEach((btn) => {
            btn.textContent = isDark ? "☀️" : "🌙";
        });
    }

    initTheme();

    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("theme-toggle")) {
            toggleTheme();
        }
    });


    /* ============================================================
       MENÚ MÓVIL
       ============================================================ */

    const hamburgerBtn = document.getElementById("hamburgerBtn");
    const navCollapsible = document.getElementById("navCollapsible");

    function closeMobileMenu() {
        if (!navCollapsible || !hamburgerBtn) return;
        navCollapsible.classList.remove("is-open");
        hamburgerBtn.setAttribute("aria-expanded", "false");
    }

    function toggleMobileMenu() {
        if (!navCollapsible || !hamburgerBtn) return;
        const isOpen = navCollapsible.classList.toggle("is-open");
        hamburgerBtn.setAttribute("aria-expanded", String(isOpen));
    }

    if (hamburgerBtn && navCollapsible) {
        hamburgerBtn.addEventListener("click", toggleMobileMenu);

        navCollapsible.addEventListener("click", (e) => {
            if (e.target.closest("a") || e.target.closest("button")) {
                closeMobileMenu();
            }
        });

        document.addEventListener("click", (e) => {
            if (navCollapsible.classList.contains("is-open") && !navCollapsible.contains(e.target) && !hamburgerBtn.contains(e.target)) {
                closeMobileMenu();
            }
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                closeMobileMenu();
            }
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 880) {
                closeMobileMenu();
            }
        });
    }


    /* ============================================================
       MODALES
       ============================================================ */

    const overlay = document.getElementById("modalOverlay");
    const modals = {
        login: document.getElementById("loginModal"),
        signup: document.getElementById("signupModal")
    };

    let lastFocusedEl = null;

    function openModal(name) {
        const target = modals[name];
        if (!target || !overlay) return;

        lastFocusedEl = document.activeElement;

        Object.values(modals).forEach((modal) => {
            if (!modal) return;
            modal.classList.remove("is-active");
            modal.hidden = true;
        });

        target.hidden = false;
        void target.offsetWidth;
        target.classList.add("is-active");
        overlay.classList.add("is-open");
        document.body.style.overflow = "hidden";

        clearFormBanners();

        const firstField = target.querySelector("input");
        if (firstField) {
            setTimeout(() => firstField.focus(), 80);
        }
    }

    function closeModal() {
        if (!overlay) return;
        overlay.classList.remove("is-open");
        document.body.style.overflow = "";

        Object.values(modals).forEach((modal) => {
            if (modal) modal.classList.remove("is-active");
        });

        setTimeout(() => {
            Object.values(modals).forEach((modal) => {
                if (modal) modal.hidden = true;
            });
        }, 220);

        if (lastFocusedEl && typeof lastFocusedEl.focus === "function") {
            lastFocusedEl.focus();
        }
    }

    function clearFormBanners() {
        document.querySelectorAll(".form-banner").forEach((banner) => {
            banner.hidden = true;
            banner.textContent = "";
            banner.classList.remove("error", "success");
        });
    }

    document.querySelectorAll("[data-open-modal]").forEach((btn) => {
        btn.addEventListener("click", () => {
            openModal(btn.getAttribute("data-open-modal"));
        });
    });

    document.querySelectorAll("[data-close-modal]").forEach((btn) => {
        btn.addEventListener("click", closeModal);
    });

    if (overlay) {
        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal();
        });
    }

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && overlay && overlay.classList.contains("is-open")) {
            closeModal();
        }
    });


    /* ============================================================
       MOSTRAR / OCULTAR CONTRASEÑA
       ============================================================ */

    document.querySelectorAll("[data-toggle-pass]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const input = document.getElementById(btn.getAttribute("data-toggle-pass"));
            if (!input) return;
            const isHidden = input.type === "password";
            input.type = isHidden ? "text" : "password";
            btn.textContent = isHidden ? "Ocultar" : "Ver";
        });
    });


    /* ============================================================
       TOASTS
       ============================================================ */

    const toastStack = document.getElementById("toastStack");

    function showToast(message, type) {
        if (!toastStack) return;
        const toast = document.createElement("div");
        toast.className = "toast " + (type === "error" ? "error" : "success");
        toast.textContent = message;
        toastStack.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add("is-visible");
        });

        setTimeout(() => {
            toast.classList.remove("is-visible");
            setTimeout(() => toast.remove(), 250);
        }, 3600);
    }


    /* ============================================================
       ERRORES DE CAMPOS
       ============================================================ */

    function setFieldError(inputId, message) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(inputId + "Error");
        if (!input || !errorEl) return;
        const field = input.closest(".field");
        if (field) field.classList.add("has-error");
        errorEl.textContent = message;
    }

    function clearFieldError(inputId) {
        const input = document.getElementById(inputId);
        const errorEl = document.getElementById(inputId + "Error");
        if (!input || !errorEl) return;
        const field = input.closest(".field");
        if (field) field.classList.remove("has-error");
        errorEl.textContent = "";
    }

    function clearAllFieldErrors(formEl) {
        if (!formEl) return;
        formEl.querySelectorAll(".field").forEach((field) => field.classList.remove("has-error"));
        formEl.querySelectorAll(".field-error").forEach((error) => error.textContent = "");
    }

    function setFormBanner(bannerId, message, type) {
        const banner = document.getElementById(bannerId);
        if (!banner) return;
        banner.hidden = false;
        banner.textContent = message;
        banner.classList.remove("error", "success");
        banner.classList.add(type);
    }


    /* ============================================================
       LIMPIAR ERRORES AL ESCRIBIR
       ============================================================ */

    ["signupName", "signupEmail", "signupPassword", "signupPasswordConfirm", "loginEmail", "loginPassword"].forEach((id) => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener("input", () => clearFieldError(id));
        }
    });


    /* ============================================================
       FORMULARIO — CREAR CUENTA
       ============================================================ */

    const signupForm = document.getElementById("signupForm");
    const signupPasswordInput = document.getElementById("signupPassword");
    const strengthMeter = document.getElementById("strengthMeter");

    if (signupPasswordInput && strengthMeter) {
        signupPasswordInput.addEventListener("input", () => {
            const score = passwordStrength(signupPasswordInput.value);
            strengthMeter.className = "strength-meter";
            if (signupPasswordInput.value.length === 0) return;
            if (score <= 1) strengthMeter.classList.add("s1");
            else if (score === 2) strengthMeter.classList.add("s2");
            else if (score === 3) strengthMeter.classList.add("s3");
            else strengthMeter.classList.add("s4");
        });
    }

    if (signupForm) {
        signupForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAllFieldErrors(signupForm);
            clearFormBanners();

            const name = document.getElementById("signupName").value.trim();
            const email = document.getElementById("signupEmail").value.trim().toLowerCase();
            const password = document.getElementById("signupPassword").value;
            const passwordConfirm = document.getElementById("signupPasswordConfirm").value;

            let hasError = false;

            if (name.length < 2) {
                setFieldError("signupName", "Escribe tu nombre completo.");
                hasError = true;
            }

            if (!isValidEmail(email)) {
                setFieldError("signupEmail", "Ingresa un correo electrónico válido.");
                hasError = true;
            }

            if (password.length < 8) {
                setFieldError("signupPassword", "La contraseña debe tener al menos 8 caracteres.");
                hasError = true;
            }

            if (passwordConfirm !== password || passwordConfirm === "") {
                setFieldError("signupPasswordConfirm", "Las contraseñas no coinciden.");
                hasError = true;
            }

            if (hasError) return;

            try {
                const usuario = await apiRequest("/usuario/registro", {
                    method: "POST",
                    body: JSON.stringify({ nombre: name, correo: email, contraseña: password })
                });

                setSession(usuario);
                signupForm.reset();
                if (strengthMeter) strengthMeter.className = "strength-meter";
                closeModal();
                showToast("Cuenta creada. ¡Bienvenido a StudNova, " + usuario.nombre.split(" ")[0] + "!", "success");
                refreshAuthUI();

            } catch (error) {
                if (error.message.toLowerCase().includes("correo") || error.message.toLowerCase().includes("registrado")) {
                    setFieldError("signupEmail", "Ya existe una cuenta con este correo.");
                    setFormBanner("signupFormBanner", "Ese correo ya está registrado. Intenta iniciar sesión.", "error");
                } else {
                    setFormBanner("signupFormBanner", error.message, "error");
                }
            }
        });
    }


    /* ============================================================
       FORMULARIO — INICIAR SESIÓN
       ============================================================ */

    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            clearAllFieldErrors(loginForm);
            clearFormBanners();

            const email = document.getElementById("loginEmail").value.trim().toLowerCase();
            const password = document.getElementById("loginPassword").value;

            let hasError = false;

            if (!isValidEmail(email)) {
                setFieldError("loginEmail", "Ingresa un correo electrónico válido.");
                hasError = true;
            }

            if (password.length === 0) {
                setFieldError("loginPassword", "Ingresa tu contraseña.");
                hasError = true;
            }

            if (hasError) return;

            try {
                const usuario = await apiRequest("/usuario/login", {
                    method: "POST",
                    body: JSON.stringify({ correo: email, contraseña: password })
                });

                setSession(usuario);
                loginForm.reset();
                closeModal();
                showToast("Sesión iniciada. Bienvenido, " + usuario.nombre.split(" ")[0] + ".", "success");
                refreshAuthUI();

            } catch (error) {
                setFormBanner("loginFormBanner", "Correo o contraseña incorrectos.", "error");
            }
        });
    }


    /* ============================================================
       ESTADO DE SESIÓN EN LA INTERFAZ
       ============================================================ */

    const navLoggedOut = document.getElementById("navCtaLoggedOut");
    const navLoggedIn = document.getElementById("navCtaLoggedIn");
    const userChipAvatar = document.getElementById("userChipAvatar");
    const userChipName = document.getElementById("userChipName");
    const openChatBtn = document.getElementById("openChatBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const dashboardBanner = document.getElementById("dashboardBanner");
    const dashboardGreeting = document.getElementById("dashboardGreeting");
    const dashboardSub = document.getElementById("dashboardSub");

    function refreshAuthUI() {
        const session = getSession();

        if (session && session.nombre) {
            if (navLoggedOut) navLoggedOut.hidden = true;
            if (navLoggedIn) navLoggedIn.hidden = false;
            if (dashboardBanner) dashboardBanner.hidden = false;

            const nombre = session.nombre;
            const firstName = nombre.split(" ")[0];

            if (userChipAvatar) userChipAvatar.textContent = initials(nombre);
            if (userChipName) userChipName.textContent = firstName;
            if (dashboardGreeting) dashboardGreeting.textContent = "Hola, " + firstName + " 👋";
            if (dashboardSub) dashboardSub.textContent = "Tu cuenta está lista. En la versión completa, aquí verías tu plan de estudios generado por IA.";

        } else {
            if (navLoggedOut) navLoggedOut.hidden = false;
            if (navLoggedIn) navLoggedIn.hidden = true;
            if (dashboardBanner) dashboardBanner.hidden = true;
        }
    }


    /* ============================================================
       ACCIONES DE BOTONES
       ============================================================ */

    if (openChatBtn) {
        openChatBtn.addEventListener("click", () => {
            window.StudNovaSession.openChat();
        });
    }

    if (logoutBtn) {
        logoutBtn.addEventListener("click", () => {
            clearSession();
            refreshAuthUI();
            showToast("Cerraste sesión correctamente.", "success");
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    refreshAuthUI();
})();