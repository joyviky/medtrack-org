/* ═══════════════════════════════════════════════════════════
   MedTrack – Registration Page Logic
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
    if (isLoggedIn()) {
        window.location.href = "/pages/patientDashboard.html";
        return;
    }

    const roleSelect = document.getElementById("role");
    const doctorFields = document.getElementById("doctor-fields");
    const form = document.getElementById("register-form");

    // Toggle doctor-specific fields
    roleSelect.addEventListener("change", () => {
        if (roleSelect.value === "doctor") {
            doctorFields.classList.remove("hidden");
        } else {
            doctorFields.classList.add("hidden");
        }
    });

    form.addEventListener("submit", handleRegister);
});

async function handleRegister(e) {
    e.preventDefault();

    const data = {
        fullName: document.getElementById("fullName").value.trim(),
        email: document.getElementById("email").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        password: document.getElementById("password").value,
        role: document.getElementById("role").value,
    };

    const confirmPassword = document.getElementById("confirmPassword").value;

    // Validations
    if (!data.fullName || !data.email || !data.password) {
        showToast("Please fill in all required fields", "warning");
        return;
    }

    if (data.password !== confirmPassword) {
        showToast("Passwords do not match", "error");
        return;
    }

    if (data.password.length < 6) {
        showToast("Password must be at least 6 characters", "warning");
        return;
    }

    // Add doctor fields if role is doctor
    if (data.role === "doctor") {
        data.specialization = document.getElementById("specialization").value;
        data.qualification = document.getElementById("qualification").value.trim();
        data.experienceYears = parseInt(document.getElementById("experience").value) || 0;
        data.consultationFee = parseInt(document.getElementById("fee").value) || 500;
    }

    const btn = document.getElementById("register-btn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating account...';

    const res = await apiRequest("/auth/register", "POST", data);

    if (res && res.ok) {
        saveAuth(res.data.token, res.data.user);
        showToast("Registration successful! Welcome to MedTrack 🏥", "success");
        setTimeout(() => {
            if (data.role === "doctor") {
                window.location.href = "/pages/doctorDashboard.html";
            } else {
                window.location.href = "/pages/patientDashboard.html";
            }
        }, 1000);
    } else {
        showToast(res?.data?.error || "Registration failed", "error");
        btn.disabled = false;
        btn.innerHTML = 'Create Account';
    }
}
