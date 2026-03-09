/* ═══════════════════════════════════════════════════════════
   MedTrack – Appointment Management Logic
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
    if (!requireAuth()) return;
    setupSidebar();

    const user = getUser();
    if (user.role === "patient") {
        loadPatientAppointments();
    } else if (user.role === "doctor") {
        loadDoctorAppointments();
    }
});

// ─── Patient Appointments ────────────────────────────────────
async function loadPatientAppointments() {
    const status = document.getElementById("status-filter")?.value || "";
    const params = status ? `?status=${status}` : "";

    showLoading();
    const res = await apiRequest(`/appointments/patient${params}`);
    hideLoading();

    if (res?.ok) {
        renderAppointments(res.data.appointments || [], "patient");
    }
}

// ─── Doctor Appointments ─────────────────────────────────────
async function loadDoctorAppointments() {
    const status = document.getElementById("status-filter")?.value || "";
    const date = document.getElementById("date-filter")?.value || "";

    let params = new URLSearchParams();
    if (status) params.append("status", status);
    if (date) params.append("date", date);

    showLoading();
    const res = await apiRequest(`/appointments/doctor?${params.toString()}`);
    hideLoading();

    if (res?.ok) {
        renderAppointments(res.data.appointments || [], "doctor");
    }
}

function renderAppointments(appointments, role) {
    const container = document.getElementById("appointments-list");

    if (appointments.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📋</div>
                <h3>No appointments found</h3>
                <p>${role === "patient" ? "Book your first appointment" : "No appointments for this filter"}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = appointments.map(appt => `
        <div class="appointment-card ${appt.isEmergency ? 'emergency' : ''}">
            <div class="appt-header">
                <h4>${role === "patient" ? (appt.doctorName || 'Doctor') : (appt.patientName || 'Patient')}</h4>
                <span class="badge badge-${appt.status}">${appt.status.replace('_', ' ')}</span>
            </div>
            <div class="appt-details">
                <span>📅 ${appt.date}</span>
                <span>🕐 ${appt.timeSlot}</span>
                ${role === "patient" ? `<span>🏥 ${appt.specialization || ''}</span>` : ''}
                ${appt.isEmergency ? '<span class="badge badge-emergency">EMERGENCY</span>' : ''}
            </div>
            ${appt.reason ? `<p style="margin-top:8px; font-size:0.85rem; color:var(--text-secondary);">📝 ${appt.reason}</p>` : ''}
            ${appt.patientAlerts && appt.patientAlerts.length > 0 ? `
                <div style="margin-top:8px;">
                    ${appt.patientAlerts.map(a => `<div class="health-alert danger">⚠️ ${a}</div>`).join("")}
                </div>
            ` : ''}
            <div style="margin-top:12px; display:flex; gap:8px; flex-wrap:wrap;">
                <button class="btn btn-outline btn-sm" onclick="viewAppointment('${appt._id}')">View Details</button>
                ${role === "doctor" && appt.status === "pending" ? `
                    <button class="btn btn-success btn-sm" onclick="updateStatus('${appt._id}', 'approved')">✅ Approve</button>
                    <button class="btn btn-danger btn-sm" onclick="updateStatus('${appt._id}', 'cancelled')">❌ Cancel</button>
                ` : ''}
                ${role === "doctor" && appt.status === "approved" ? `
                    <button class="btn btn-success btn-sm" onclick="updateStatus('${appt._id}', 'completed')">✅ Mark Complete</button>
                ` : ''}
                ${role === "patient" && (appt.status === "completed" || appt.status === "prescription_uploaded") ? `
                    <button class="btn btn-warning btn-sm" onclick="openReviewModal('${appt.doctorId || appt._id}')">⭐ Rate Doctor</button>
                ` : ''}
            </div>
        </div>
    `).join("");
}

async function updateStatus(appointmentId, status) {
    const res = await apiRequest("/appointments/status", "PUT", {
        appointmentId: appointmentId,
        status: status
    });

    if (res?.ok) {
        showToast(`Appointment ${status} successfully`, "success");
        const user = getUser();
        if (user.role === "doctor") loadDoctorAppointments();
        else loadPatientAppointments();
    } else {
        showToast(res?.data?.error || "Failed to update", "error");
    }
}

function viewAppointment(id) {
    window.location.href = `/pages/appointmentDetails.html?id=${id}`;
}

// ─── Review Modal ────────────────────────────────────────────
let reviewDoctorId = null;
let selectedRating = 0;

function openReviewModal(doctorId) {
    reviewDoctorId = doctorId;
    selectedRating = 0;
    const modal = document.getElementById("review-modal");
    if (modal) {
        modal.classList.add("active");
        updateStars(0);
    }
}

function closeReviewModal() {
    const modal = document.getElementById("review-modal");
    if (modal) modal.classList.remove("active");
    reviewDoctorId = null;
}

function setRating(rating) {
    selectedRating = rating;
    updateStars(rating);
}

function updateStars(rating) {
    const stars = document.querySelectorAll(".review-star");
    stars.forEach((star, i) => {
        star.classList.toggle("filled", i < rating);
    });
}

async function submitReview() {
    if (!selectedRating) {
        showToast("Please select a rating", "warning");
        return;
    }

    const comment = document.getElementById("review-comment")?.value || "";

    const res = await apiRequest("/appointments/review", "POST", {
        doctorId: reviewDoctorId,
        rating: selectedRating,
        comment: comment
    });

    if (res?.ok) {
        showToast("Review submitted! Thank you 🙏", "success");
        closeReviewModal();
    } else {
        showToast(res?.data?.error || "Failed to submit review", "error");
    }
}

function filterAppointments() {
    const user = getUser();
    if (user.role === "patient") loadPatientAppointments();
    else loadDoctorAppointments();
}
