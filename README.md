# 🏥 MedTrack – Smart Hospital Management System

A full-stack hospital management system built with **Flask**, **MongoDB**, and **HTML/CSS/JavaScript**.

## 🚀 Features

### Patient Side
- ✅ Register & Login with JWT authentication
- ✅ Search doctors by specialization and rating
- ✅ Smart appointment slot booking (prevents double booking)
- ✅ Emergency quick booking
- ✅ Medical records timeline
- ✅ Upload medical reports (PDF, images)
- ✅ View prescriptions
- ✅ AI Symptom Checker (suggests departments)
- ✅ Rate and review doctors
- ✅ Notification system

### Doctor Side
- ✅ Doctor registration with specialization
- ✅ Manage appointments (approve/complete/cancel)
- ✅ View patient details with health alerts (allergies, conditions)
- ✅ Weekly availability calendar
- ✅ Upload prescriptions & reports

### System Features
- ✅ JWT-based authentication
- ✅ Role-based access control (Patient, Doctor, Admin)
- ✅ Health alert system (allergy warnings)
- ✅ Appointment status lifecycle
- ✅ Real-time notifications
- ✅ Admin analytics dashboard

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | MongoDB (Compass) |
| Auth | JWT (PyJWT) + bcrypt |
| API | RESTful API |

## 📁 Project Structure

```
medtrack/
├── frontend/
│   ├── css/style.css
│   ├── js/ (api.js, login.js, register.js, dashboard.js, ...)
│   └── pages/ (15 HTML pages)
├── backend/
│   ├── app.py (main server)
│   ├── config/db.py
│   ├── models/ (user, doctor, patient, appointment, ...)
│   ├── controllers/ (auth, doctor, patient, appointment, medical)
│   ├── routes/ (auth, doctor, patient, appointment, medical, notification)
│   ├── middleware/auth_middleware.py
│   └── utils/helpers.py
├── database/medtrack_db_schema.md
├── uploads/ (reports, prescriptions)
├── requirements.txt
└── README.md
```

## ⚡ Setup & Run

### 1. Install MongoDB
Download and install [MongoDB Community Server](https://www.mongodb.com/try/download/community) and [MongoDB Compass](https://www.mongodb.com/try/download/compass).

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start MongoDB
Make sure MongoDB is running on `localhost:27017`.

### 4. Run the Server
```bash
python backend/app.py
```

### 5. Open the App
Visit `http://127.0.0.1:5000` in your browser.

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login & get token |
| GET | `/api/auth/profile` | Get profile |

### Doctors
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/doctors/` | List all doctors |
| GET | `/api/doctors/<id>` | Get doctor details |
| GET | `/api/doctors/<id>/slots?date=YYYY-MM-DD` | Get available slots |
| PUT | `/api/doctors/profile/update` | Update doctor profile |

### Appointments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/appointments/book` | Book appointment |
| GET | `/api/appointments/patient` | Patient's appointments |
| GET | `/api/appointments/doctor` | Doctor's appointments |
| PUT | `/api/appointments/status` | Update status |
| POST | `/api/appointments/emergency` | Emergency booking |
| POST | `/api/appointments/review` | Add review |

### Medical Records
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/medical/upload` | Upload record |
| GET | `/api/medical/records` | Get health timeline |

### Others
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | Get notifications |
| POST | `/api/symptoms/suggest` | AI symptom suggestion |
| GET | `/api/admin/analytics` | Admin dashboard data |

## 📄 Pages (15 Total)

1. Login
2. Register
3. Patient Dashboard
4. Doctor Dashboard
5. Search Doctor
6. Book Appointment
7. Patient Appointments
8. Doctor Appointments
9. Appointment Details
10. Patient Profile
11. Medical Records
12. Upload Report
13. Prescription View
14. Notifications
15. Appointment History

## 👨‍💻 Built By

**Deva** – Final Year Project
