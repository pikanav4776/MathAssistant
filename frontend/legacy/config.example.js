// Copy to config.js for local dev, or rely on the committed config.js default.
// On Render, the static-site build overwrites config.js from API_BASE_URL.
window.API_BASE = window.API_BASE || "http://127.0.0.1:8000";
