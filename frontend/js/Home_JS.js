import { protectRoute } from "./auth_guard.js";

document.addEventListener("DOMContentLoaded", () => {
    protectRoute();
});