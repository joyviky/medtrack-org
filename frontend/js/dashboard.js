/* ═══════════════════════════════════════════════════════════
   MedTrack – Patient Dashboard Logic
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
    if (!requireAuth() || !requireRole("patient")) return;
    setupSidebar();
    loadDashboard();
});

async function loadDashboard() {
    showLoading();

    // Load stats
    const [apptRes, notifRes] = await Promise.all([
        apiRequest("/appointments/patient"),
        apiRequest("/notifications/")
    ]);

    hideLoading();

    if (apptRes?.ok) {
        const appointments = apptRes.data.appointments || [];
        renderStats(appointments);
        renderUpcomingAppointments(appointments);
    }

    if (notifRes?.ok) {
        updateNotificationBadge(notifRes.data.unreadCount || 0);
    }
}

function renderStats(appointments) {
    const total = appointments.length;
    const pending = appointments.filter(a => a.status === "pending").length;
    const completed = appointments.filter(a => a.status === "completed" || a.status === "prescription_uploaded").length;
    const upcoming = appointments.filter(a => a.status === "approved").length;

    document.getElementById("stat-total").textContent = total;
    document.getElementById("stat-pending").textContent = pending;
    document.getElementById("stat-completed").textContent = completed;
    document.getElementById("stat-upcoming").textContent = upcoming;
}

function renderUpcomingAppointments(appointments) {
    const container = document.getElementById("upcoming-appointments");
    const upcoming = appointments
        .filter(a => a.status === "pending" || a.status === "approved")
        .slice(0, 5);

    if (upcoming.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📅</div>
                <h3>No upcoming appointments</h3>
                <p>Book an appointment with a doctor to get started</p>
                <a href="/pages/searchDoctor.html" class="btn btn-primary mt-2">Find a Doctor</a>
            </div>
        `;
        return;
    }

    container.innerHTML = upcoming.map(appt => `
        <div class="appointment-card ${appt.isEmergency ? 'emergency' : ''}" onclick="viewAppointment('${appt._id}')">
            <div class="appt-header">
                <h4>${appt.doctorName || 'Doctor'}</h4>
                <span class="badge badge-${appt.status}">${appt.status.replace('_', ' ')}</span>
            </div>
            <div class="appt-details">
                <span>📅 ${appt.date}</span>
                <span>🕐 ${appt.timeSlot}</span>
                <span>🏥 ${appt.specialization || ''}</span>
                ${appt.isEmergency ? '<span class="badge badge-emergency">EMERGENCY</span>' : ''}
            </div>
        </div>
    `).join("");
}

function updateNotificationBadge(count) {
    const badge = document.getElementById("notif-count");
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? "flex" : "none";
    }
}

function viewAppointment(id) {
    window.location.href = `/pages/appointmentDetails.html?id=${id}`;
}
