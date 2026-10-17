/* ============================================================
   StudNova — landing-motion.js
   Movimiento tipo Apple para la landing:
     1) Avatar flotando en el hero (con halo de luz), que se
        encoge y se desvanece suavemente al hacer scroll.
     2) Las secciones aparecen con fade + deslizamiento al entrar
        en pantalla, en cascada.

   No necesita cambios en el HTML salvo agregar, al final del body:
     <script src="landing-motion.js" defer></script>
   ============================================================ */
(function () {
    "use strict";

    /* ---------- CONFIGURACIÓN (lo único que debes ajustar) ---------- */

    // Ruta de la imagen del avatar vista desde la landing.
    // Ideal: la versión PNG con fondo transparente (sticker sin fondo).
    const AVATAR_SRC = "/ia/avatar.png";

    // true  → recorta el avatar en círculo (úsalo si la imagen tiene fondo)
    // false → muestra el personaje tal cual (úsalo con el PNG transparente)
    const AVATAR_REDONDO = true;

    /* ---------------------------------------------------------------- */

    const reducirMovimiento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Marca que el JS está activo: el CSS solo oculta los bloques "reveal"
    // si esta clase existe (si el JS falla, la página sigue visible).
    document.documentElement.classList.add("js-motion");

    /* ============ 1. AVATAR DEL HERO ============ */
    function crearAvatarHero() {
        const contenedor = document.querySelector(".hero-grid > div:first-child");
        if (!contenedor || contenedor.querySelector(".hero-avatar")) return null;

        const wrap = document.createElement("div");
        wrap.className = "hero-avatar" + (AVATAR_REDONDO ? " hero-avatar--circulo" : "");
        wrap.setAttribute("aria-hidden", "true"); // es decorativo

        const halo = document.createElement("span");
        halo.className = "hero-avatar-halo";

        const img = document.createElement("img");
        img.className = "hero-avatar-img";
        img.src = AVATAR_SRC;
        img.alt = "";
        img.decoding = "async";
        // si la ruta falla, no dejamos un hueco ni una imagen rota
        img.addEventListener("error", () => wrap.remove());

        wrap.appendChild(halo);
        wrap.appendChild(img);
        contenedor.insertBefore(wrap, contenedor.firstChild);
        return wrap;
    }

    // El avatar se encoge, sube y se desvanece mientras bajas por la página
    function enlazarScroll(wrap) {
        if (!wrap || reducirMovimiento) return;

        let pendiente = false;
        const actualizar = () => {
            const p = Math.min(Math.max(window.scrollY / (window.innerHeight * 0.6), 0), 1);
            wrap.style.setProperty("--p", p.toFixed(3));
            pendiente = false;
        };

        window.addEventListener("scroll", () => {
            if (!pendiente) {
                pendiente = true;
                requestAnimationFrame(actualizar);
            }
        }, { passive: true });

        actualizar();
    }

    /* ============ 2. APARICIÓN AL HACER SCROLL ============ */
    // Cada selector se numera por "familia" (mismo padre) para escalonar la entrada.
    const GRUPOS_REVEAL = [
        ".split .eyebrow, .split h2, .problem-item",
        ".flow .eyebrow, .flow h2, .flow-step",
        ".modules-head > *, .module-card",
        ".styles-grid > div:first-child > *, .style-card",
        ".team .eyebrow, .team h2, .team-card",
        ".cta .wrap > *"
    ];

    function prepararReveal() {
        const elementos = [];

        GRUPOS_REVEAL.forEach((selector) => {
            const posicionPorPadre = new Map();

            document.querySelectorAll(selector).forEach((el) => {
                if (el.classList.contains("reveal")) return;

                const padre = el.parentElement;
                const indice = posicionPorPadre.get(padre) || 0;
                posicionPorPadre.set(padre, indice + 1);

                // cascada de 80 ms entre hermanos, con tope de 0.5 s
                el.style.setProperty("--d", Math.min(indice * 0.08, 0.5).toFixed(2) + "s");
                el.classList.add("reveal");
                elementos.push(el);
            });
        });

        // Sin soporte o con "reducir movimiento": todo visible de una vez
        if (reducirMovimiento || !("IntersectionObserver" in window)) {
            elementos.forEach((el) => el.classList.add("is-visible"));
            return;
        }

        const observador = new IntersectionObserver((entradas) => {
            entradas.forEach((entrada) => {
                if (entrada.isIntersecting) {
                    entrada.target.classList.add("is-visible");
                    observador.unobserve(entrada.target);
                }
            });
        }, { threshold: 0.15, rootMargin: "0px 0px -8% 0px" });

        elementos.forEach((el) => observador.observe(el));
    }

    /* ============ INICIO ============ */
    function iniciar() {
        enlazarScroll(crearAvatarHero());
        prepararReveal();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();