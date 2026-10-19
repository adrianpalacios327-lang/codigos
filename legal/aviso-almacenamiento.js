/* ============================================================
   StudNova — aviso-almacenamiento.js
   Aviso breve sobre cookies y almacenamiento local.

   USO: agregar antes de </body> en las páginas públicas (landing y login):
     <script src="/legal/aviso-almacenamiento.js" defer></script>

   - Se muestra una sola vez (hasta que cambies VERSION).
   - Guarda la fecha y la versión en que el usuario lo aceptó.
   - No tiene dependencias: inyecta su propio CSS.

   IMPORTANTE: este aviso es suficiente mientras la plataforma use SOLO
   almacenamiento esencial/funcional. Si más adelante agregas analítica,
   publicidad o píxeles, ese contenido NO debe cargarse hasta que el
   usuario lo acepte de forma expresa (botón "Aceptar" y "Rechazar" por
   separado). Pídele a un abogado que valide el texto final.
   ============================================================ */
(function () {
    "use strict";

    const CLAVE = "studnova:aviso-almacenamiento";
    const VERSION = "2026-10-17";                       // cámbiala si modificas la política
    const URL_POLITICA = "/legal/privacidad.html#cookies";

    // Si ya lo aceptó en esta versión, no se vuelve a mostrar
    try {
        const guardado = JSON.parse(localStorage.getItem(CLAVE) || "null");
        if (guardado && guardado.version === VERSION) return;
    } catch (e) { /* si localStorage falla, mostramos el aviso */ }

    const estilo = document.createElement("style");
    estilo.textContent = `
        .aviso-alm{
            position:fixed; left:50%; bottom:20px; z-index:9998;
            width:min(640px, calc(100% - 28px));
            transform:translate(-50%, 24px); opacity:0;
            display:flex; align-items:center; gap:16px; flex-wrap:wrap;
            padding:16px 18px 16px 22px;
            border-radius:22px;
            background:rgba(18,40,72,.92);
            border:1px solid rgba(114,175,193,.35);
            -webkit-backdrop-filter:blur(20px) saturate(160%);
            backdrop-filter:blur(20px) saturate(160%);
            box-shadow:0 24px 60px -20px rgba(0,0,0,.65);
            color:#F4F8FC;
            font:14.5px/1.45 -apple-system,BlinkMacSystemFont,"SF Pro Text","Inter","Segoe UI",Helvetica,Arial,sans-serif;
            letter-spacing:-0.01em;
            transition:opacity .5s cubic-bezier(.22,1,.36,1), transform .7s cubic-bezier(.22,1,.36,1);
        }
        .aviso-alm.visible{ transform:translate(-50%, 0); opacity:1; }
        .aviso-alm p{ flex:1 1 280px; margin:0; color:#dbe7f2; }
        .aviso-alm a{ color:#A9D6E0; text-underline-offset:3px; }
        .aviso-alm a:hover{ color:#fff; }
        .aviso-alm button{
            border:none; cursor:pointer; flex-shrink:0;
            padding:9px 22px; border-radius:980px;
            background:#72AFC1; color:#0A082D;
            font:inherit; font-weight:600;
            transition:background .2s ease, transform .2s ease;
        }
        .aviso-alm button:hover{ background:#A9D6E0; }
        .aviso-alm button:active{ transform:scale(.97); }
        .aviso-alm button:focus-visible, .aviso-alm a:focus-visible{ outline:2px solid #A9D6E0; outline-offset:3px; }
        @media (prefers-reduced-motion: reduce){ .aviso-alm{ transition:none; } }
    `;
    document.head.appendChild(estilo);

    const aviso = document.createElement("div");
    aviso.className = "aviso-alm";
    aviso.setAttribute("role", "dialog");
    aviso.setAttribute("aria-label", "Aviso sobre cookies y almacenamiento");
    aviso.innerHTML = `
        <p>StudNova guarda en tu navegador unos pocos datos necesarios para mantener tu sesión y recordar tus
        preferencias, y usa servicios de Google para iniciar sesión. No usamos cookies de publicidad.
        <a href="${URL_POLITICA}">Más información</a></p>
        <button type="button">Entendido</button>
    `;
    document.body.appendChild(aviso);

    // entra con una pequeña transición
    requestAnimationFrame(() => requestAnimationFrame(() => aviso.classList.add("visible")));

    aviso.querySelector("button").addEventListener("click", () => {
        try {
            localStorage.setItem(CLAVE, JSON.stringify({ version: VERSION, fecha: new Date().toISOString() }));
        } catch (e) { /* sin almacenamiento: se cierra igual */ }
        aviso.classList.remove("visible");
        setTimeout(() => aviso.remove(), 600);
    });
})();