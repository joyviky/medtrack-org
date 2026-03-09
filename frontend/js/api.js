/* ═══════════════════════════════════════════════════════════
   MedTrack – API Service Layer
   Handles all communication with Flask backend
   ═══════════════════════════════════════════════════════════ */

const API_BASE = "http://127.0.0.1:5000/api";

// ─── Auth Helpers ────────────────────────────────────────────
function getToken() {
    return localStorage.getItem("medtrack_token");
}

function getUser() {
    const data = localStorage.getItem("medtrack_user");
    return data ? JSON.parse(data) : null;
}

function saveAuth(token, user) {
    localStorage.setItem("medtrack_token", token);
    localStorage.setItem("medtrack_user", JSON.stringify(user));
}

function clearAuth() {
    localStorage.removeItem("medtrack_token");
    localStorage.removeItem("medtrack_user");
}

function isLoggedIn() {
    return !!getToken();
}

function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = "/pages/login.html";
        return false;
    }
    return true;
}

function requireRole(role) {
    const user = getUser();
    if (!user || user.role !== role) {
        window.location.href = "/pages/login.html";
        return false;
    }
    return true;
}

function logout() {
    clearAuth();
    window.location.href = "/pages/login.html";
}

// ─── API Request Helper ──────────────────────────────────────
async function apiRequest(endpoint, method = "GET", body = null, isFormData = false) {
    const headers = {};
    const token = getToken();

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    if (!isFormData && body) {
        headers["Content-Type"] = "application/json";
    }

    const config = { method, headers };

    if (body) {
        config.body = isFormData ? body : JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const data = await response.json();

        if (response.status === 401) {
            clearAuth();
            window.location.href = "/pages/login.html";
            return null;
        }

        return { ok: response.ok, status: response.status, data };
    } catch (error) {
        console.error("API Error:", error);
        return { ok: false, status: 500, data: { error: "Network error. Please try again." } };
    }
}

// ─── Toast Notifications ─────────────────────────────────────
function showToast(message, type = "info") {
    let container = document.getElementById("toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "toast-container";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    const icons = {
        success: "✅",
        error: "❌",
        warning: "⚠️",
        info: "ℹ️"
    };

    toast.innerHTML = `<span>${icons[type] || ""}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 4000);
}

// ─── Loading State ───────────────────────────────────────────
function showLoading() {
    let overlay = document.getElementById("loading-overlay");
    if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "loading-overlay";
        overlay.className = "loading-overlay";
        overlay.innerHTML = '<div class="spinner spinner-lg spinner-primary"></div>';
        document.body.appendChild(overlay);
    }
    overlay.style.display = "flex";
}

function hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) overlay.style.display = "none";
}

// ─── Sidebar Setup ─────────────────────────────────────────
function setupSidebar() {
    const user = getUser();
    if (!user) return;

    // Set user info
    const avatarEl = document.getElementById("sidebar-avatar");
    const nameEl = document.getElementById("sidebar-name");
    const roleEl = document.getElementById("sidebar-role");

    if (avatarEl) avatarEl.textContent = user.fullName?.charAt(0) || "U";
    if (nameEl) nameEl.textContent = user.fullName || "User";
    if (roleEl) roleEl.textContent = user.role || "user";
}

// ─── Mobile Menu Toggle ──────────────────────────────────────
function toggleSidebar() {
    const sidebar = document.querySelector(".sidebar");
    if (sidebar) sidebar.classList.toggle("open");
}

// ─── Format Date ─────────────────────────────────────────────
function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric"
    });
}

function formatDateTime(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

function timeAgo(dateStr) {
    const now = new Date();
    const past = new Date(dateStr);
    const diffMs = now - past;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return formatDate(dateStr);
}
