/* ═══════════════════════════════════════════════════════════
   MedTrack – Login Page Logic
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
    // If already logged in, redirect to dashboard
    if (isLoggedIn()) {
        redirectToDashboard();
        return;
    }

    const form = document.getElementById("login-form");
    form.addEventListener("submit", handleLogin);
});

async function handleLogin(e) {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const btn = document.getElementById("login-btn");

    if (!email || !password) {
        showToast("Please fill in all fields", "warning");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Logging in...';

    const res = await apiRequest("/auth/login", "POST", { email, password });

    if (res && res.ok) {
        saveAuth(res.data.token, res.data.user);
        showToast("Login successful! Redirecting...", "success");
        setTimeout(() => redirectToDashboard(), 800);
    } else {
        showToast(res?.data?.error || "Login failed", "error");
        btn.disabled = false;
        btn.innerHTML = 'Sign In';
    }
}

function redirectToDashboard() {
    const user = getUser();
    if (!user) return;

    const routes = {
        doctor: "/pages/doctorDashboard.html",
        admin: "/pages/adminDashboard.html",
        patient: "/pages/patientDashboard.html"
    };
    window.location.href = routes[user.role] || "/pages/patientDashboard.html";
}
