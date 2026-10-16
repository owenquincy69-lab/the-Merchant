
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("dashboardSidebar");
    const toggle = document.getElementById("dashboardMenuToggle");
    const scrim = document.getElementById("dashboardScrim");

    function closeMenu() {
        sidebar?.classList.remove("is-open");
        document.body.classList.remove("sidebar-open");
        toggle?.setAttribute("aria-expanded", "false");

        if (scrim) {
            scrim.hidden = true;
        }
    }

    function openMenu() {
        sidebar?.classList.add("is-open");
        document.body.classList.add("sidebar-open");
        toggle?.setAttribute("aria-expanded", "true");

        if (scrim) {
            scrim.hidden = false;
        }
    }

    toggle?.addEventListener("click", () => {
        if (sidebar?.classList.contains("is-open")) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    scrim?.addEventListener("click", closeMenu);

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeMenu();
        }
    });

    window.addEventListener("resize", () => {
        if (window.matchMedia("(min-width: 900px)").matches) {
            closeMenu();
        }
    });

    const currentPath =
        window.location.pathname.replace(/\/+$/, "") || "/";

    document.querySelectorAll(".sidebar-nav .sidebar-link").forEach((link) => {
        const linkPath =
            new URL(link.href, window.location.origin).pathname.replace(/\/+$/, "") || "/";

        if (linkPath === currentPath) {
            link.classList.add("is-active");
            link.setAttribute("aria-current", "page");
        }
    });
});
