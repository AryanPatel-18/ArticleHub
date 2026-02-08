/* ======================================================
   GLOBAL THEME ENGINE
   Works on every page automatically
====================================================== */

(function () {
    const root = document.documentElement;

    /* Apply saved/system theme immediately (prevents flash) */
    const saved = localStorage.getItem("theme");
    if (saved) {
        root.setAttribute("data-theme", saved);
    } else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        root.setAttribute("data-theme", "dark");
    }

    /* After DOM loads, connect buttons */
    document.addEventListener("DOMContentLoaded", () => {
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
})();
