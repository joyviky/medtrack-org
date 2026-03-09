/* ═══════════════════════════════════════════════════════════
   MedTrack – Search Doctor & Book Appointment Logic
   ═══════════════════════════════════════════════════════════ */

document.addEventListener("DOMContentLoaded", () => {
    if (!requireAuth()) return;
    setupSidebar();

    const searchInput = document.getElementById("search-input");
    const specFilter = document.getElementById("spec-filter");

    if (searchInput) searchInput.addEventListener("input", debounce(loadDoctors, 300));
    if (specFilter) specFilter.addEventListener("change", loadDoctors);

    loadDoctors();
});

let selectedSlot = null;
let selectedDoctorId = null;

async function loadDoctors() {
    const search = document.getElementById("search-input")?.value || "";
    const spec = document.getElementById("spec-filter")?.value || "";

    const params = new URLSearchParams();
    if (spec) params.append("specialization", spec);

    showLoading();
    const res = await apiRequest(`/doctors/?${params.toString()}`);
    hideLoading();

    if (res?.ok) {
        let doctors = res.data.doctors || [];

        // Client-side name filter
        if (search) {
            doctors = doctors.filter(d =>
                d.fullName?.toLowerCase().includes(search.toLowerCase()) ||
                d.specialization?.toLowerCase().includes(search.toLowerCase())
            );
        }

        renderDoctors(doctors);
    }
}

function renderDoctors(doctors) {
    const container = document.getElementById("doctors-list");

    if (doctors.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3>No doctors found</h3>
                <p>Try adjusting your search criteria</p>
            </div>
        `;
        return;
    }

    container.innerHTML = doctors.map(doc => `
        <div class="doctor-card">
            <div class="doctor-header">
                <div class="doctor-avatar">${doc.fullName?.charAt(0) || 'D'}</div>
                <div class="doctor-info">
                    <h3>Dr. ${doc.fullName || 'Unknown'}</h3>
                    <span class="specialization">${doc.specialization || 'General'}</span>
                </div>
            </div>
            <div class="doctor-meta">
                <span class="rating">⭐ ${doc.avgRating || '0.0'} <span class="count">(${doc.totalReviews || 0} reviews)</span></span>
                <span>📋 ${doc.experienceYears || 0} yrs exp</span>
                <span>💰 ₹${doc.consultationFee || 500}</span>
            </div>
            <p style="font-size:0.88rem; color:var(--text-secondary); margin-bottom:16px;">${doc.bio || 'Experienced medical professional committed to patient care.'}</p>
            <div style="display:flex; gap:8px;">
                <button class="btn btn-primary btn-sm" onclick="openBookModal('${doc._id}', 'Dr. ${doc.fullName}')">
                    📅 Book Appointment
                </button>
                <button class="btn btn-outline btn-sm" onclick="window.location.href='/pages/appointmentDetails.html?doctorId=${doc._id}'">
                    View Profile
                </button>
            </div>
        </div>
    `).join("");
}

function openBookModal(doctorId, doctorName) {
    selectedDoctorId = doctorId;
    selectedSlot = null;
    document.getElementById("modal-doctor-name").textContent = doctorName;
    document.getElementById("booking-modal").classList.add("active");
    document.getElementById("slots-container").innerHTML = '<p class="text-center" style="color:var(--text-light);">Select a date to see available slots</p>';
}

function closeBookModal() {
    document.getElementById("booking-modal").classList.remove("active");
    selectedSlot = null;
    selectedDoctorId = null;
}

async function loadSlots() {
    const date = document.getElementById("appt-date").value;
    if (!date || !selectedDoctorId) return;

    const slotsContainer = document.getElementById("slots-container");
    slotsContainer.innerHTML = '<div class="flex-center"><div class="spinner spinner-primary"></div></div>';

    const res = await apiRequest(`/doctors/${selectedDoctorId}/slots?date=${date}`);

    if (res?.ok) {
        const { availableSlots, bookedSlots } = res.data;

        if (availableSlots.length === 0 && bookedSlots.length === 0) {
            slotsContainer.innerHTML = '<p class="text-center" style="color:var(--text-light);">Doctor not available on this day</p>';
            return;
        }

        const allSlots = [...availableSlots, ...bookedSlots].sort();

        slotsContainer.innerHTML = `
            <div class="slots-grid">
                ${allSlots.map(slot => {
                    const isBooked = bookedSlots.includes(slot);
                    return `<button class="slot-btn ${isBooked ? 'booked' : ''}" 
                                ${isBooked ? 'disabled' : ''}
                                onclick="selectSlot(this, '${slot}')">
                                ${slot}
                            </button>`;
                }).join("")}
            </div>
        `;
    } else {
        slotsContainer.innerHTML = '<p class="text-center" style="color:var(--danger);">Failed to load slots</p>';
    }
}

function selectSlot(btn, time) {
    document.querySelectorAll(".slot-btn.selected").forEach(b => b.classList.remove("selected"));
    btn.classList.add("selected");
    selectedSlot = time;
}

async function confirmBooking() {
    const date = document.getElementById("appt-date").value;
    const reason = document.getElementById("appt-reason").value;
    const isEmergency = document.getElementById("appt-emergency")?.checked || false;

    if (!date || !selectedSlot) {
        showToast("Please select a date and time slot", "warning");
        return;
    }

    const btn = document.getElementById("confirm-booking-btn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Booking...';

    const res = await apiRequest("/appointments/book", "POST", {
        doctorId: selectedDoctorId,
        date: date,
        timeSlot: selectedSlot,
        reason: reason,
        isEmergency: isEmergency
    });

    if (res?.ok) {
        showToast("Appointment booked successfully! 🎉", "success");
        closeBookModal();
        setTimeout(() => {
            window.location.href = "/pages/patientAppointments.html";
        }, 1000);
    } else {
        showToast(res?.data?.error || "Booking failed", "error");
        btn.disabled = false;
        btn.innerHTML = 'Confirm Booking';
    }
}

// ─── Debounce utility ────────────────────────────────────────
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
