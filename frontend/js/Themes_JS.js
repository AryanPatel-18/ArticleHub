/* ======================================================
   GLOBAL THEME ENGINE (NO FLASH VERSION)
   Applies theme before render + universal persistence
====================================================== */
import { protectRoute } from "./auth_guard.js";

(function () {
    const root = document.documentElement;

    /* -------- APPLY THEME IMMEDIATELY -------- */
    const saved = localStorage.getItem("theme");

    if (saved) {
        root.setAttribute("data-theme", saved);
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        root.setAttribute("data-theme", "dark");
    }
})();


/* -------- AFTER PAGE LOAD: BUTTON LOGIC -------- */
document.addEventListener("DOMContentLoaded", () => {
    const root = document.documentElement;
    const toggles = document.querySelectorAll("#theme-toggle");

    if (!toggles.length) return;

    updateIcons();

    toggles.forEach(btn => {
        btn.addEventListener("click", () => {
            const current = root.getAttribute("data-theme");
            const next = current === "dark" ? "light" : "dark";

            root.setAttribute("data-theme", next);
            localStorage.setItem("theme", next);
            updateIcons();
        });
    });

    function updateIcons() {
        const dark = root.getAttribute("data-theme") === "dark";
        toggles.forEach(btn => btn.textContent = dark ? "☀️" : "🌙");
    }
});


/* -------- SYNC BETWEEN TABS -------- */
window.addEventListener("storage", (e) => {
    if (e.key === "theme") {
        if (e.newValue)
            document.documentElement.setAttribute("data-theme", e.newValue);
    }
});
