"""
MedTrack - Database Seeder
Run: python seed.py
Seeds the database with demo users, doctors, patients, and appointments.
"""

import os, sys, bcrypt, jwt
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from backend.config.db import (
    db, users_collection, doctors_collection, patients_collection,
    appointments_collection, reviews_collection, notifications_collection
)

SECRET_KEY = os.getenv("SECRET_KEY", "medtrack-super-secret-key-2026")

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

# ──────────────────────────────────────────────
print("\n[*] Clearing old seed data...")
users_collection.delete_many({"_seeded": True})
doctors_collection.delete_many({"_seeded": True})
patients_collection.delete_many({"_seeded": True})
appointments_collection.delete_many({"_seeded": True})
reviews_collection.delete_many({"_seeded": True})
notifications_collection.delete_many({"_seeded": True})

# ──────────────────────────────────────────────
print("[*] Seeding doctors...")

DOCTORS = [
    {"fullName": "Dr. Arun Kumar",     "email": "arun@demo.com",    "specialization": "Cardiology",        "qualification": "MBBS, MD (Cardiology)",   "experience": 12, "fee": 800,  "bio": "Senior cardiologist with 12+ years of experience in heart disease management."},
    {"fullName": "Dr. Priya Sharma",   "email": "priya@demo.com",   "specialization": "Dermatology",       "qualification": "MBBS, MD (Dermatology)",  "experience": 8,  "fee": 600,  "bio": "Expert in skin disorders, cosmetic dermatology and allergy treatments."},
    {"fullName": "Dr. Ravi Menon",     "email": "ravi@demo.com",    "specialization": "Neurology",         "qualification": "MBBS, DM (Neurology)",    "experience": 15, "fee": 1000, "bio": "Specialist in neurological disorders, headaches, and epilepsy management."},
    {"fullName": "Dr. Sneha Patel",    "email": "sneha@demo.com",   "specialization": "Pediatrics",        "qualification": "MBBS, MD (Pediatrics)",   "experience": 6,  "fee": 500,  "bio": "Compassionate pediatrician providing complete child healthcare from birth to 18."},
    {"fullName": "Dr. Karthik Raj",    "email": "karthik@demo.com", "specialization": "Orthopedics",       "qualification": "MBBS, MS (Ortho)",        "experience": 10, "fee": 700,  "bio": "Orthopedic surgeon specializing in joint replacements and sports injuries."},
    {"fullName": "Dr. Divya Nair",     "email": "divya@demo.com",   "specialization": "Gynecology",        "qualification": "MBBS, MD (OBG)",          "experience": 9,  "fee": 650,  "bio": "Gynecologist dedicated to women's health from adolescence through menopause."},
    {"fullName": "Dr. Suresh Babu",    "email": "suresh@demo.com",  "specialization": "General Physician", "qualification": "MBBS, MD",                "experience": 14, "fee": 400,  "bio": "Experienced general physician handling diagnostics, fever, and chronic conditions."},
    {"fullName": "Dr. Meena Krishnan", "email": "meena@demo.com",   "specialization": "ENT",               "qualification": "MBBS, MS (ENT)",          "experience": 7,  "fee": 550,  "bio": "ENT specialist treating ear, nose, throat disorders and hearing loss."},
]

DAYS = ["monday","tuesday","wednesday","thursday","friday","saturday"]
AVAILABILITY = {d: {"active": True, "start": "09:00", "end": "17:00"} for d in DAYS}
AVAILABILITY["sunday"] = {"active": False, "start": "09:00", "end": "17:00"}

doc_ids = []
for d in DOCTORS:
    u = users_collection.insert_one({
        "email": d["email"], "password": hash_pw("demo123"),
        "fullName": d["fullName"], "role": "doctor", "phone": "9876543210",
        "createdAt": datetime.utcnow(), "_seeded": True
    })
    uid = str(u.inserted_id)
    doc = doctors_collection.insert_one({
        "userId": uid,
        "specialization": d["specialization"],
        "qualification": d["qualification"],
        "experienceYears": d["experience"],
        "consultationFee": d["fee"],
        "bio": d["bio"],
        "availability": AVAILABILITY,
        "slotDurationMinutes": 30,
        "isApproved": True,
        "avgRating": round(3.5 + (d["experience"] % 3) * 0.5, 1),
        "reviewCount": d["experience"],
        "_seeded": True,
        "createdAt": datetime.utcnow()
    })
    doc_ids.append({"userId": uid, "docId": str(doc.inserted_id), **d})
    print(f"    + {d['fullName']} ({d['specialization']})")

# ──────────────────────────────────────────────
print("[*] Seeding patients...")

PATIENTS = [
    {"fullName": "Vignesh Kumar", "email": "vignesh@demo.com", "blood": "O+", "age": 25, "gender": "Male"},
    {"fullName": "Anjali Singh",  "email": "anjali@demo.com",  "blood": "B+", "age": 30, "gender": "Female"},
    {"fullName": "Rahul Patel",   "email": "rahul@demo.com",   "blood": "A+", "age": 22, "gender": "Male"},
]

pat_ids = []
for p in PATIENTS:
    u = users_collection.insert_one({
        "email": p["email"], "password": hash_pw("demo123"),
        "fullName": p["fullName"], "role": "patient", "phone": "9876500000",
        "bloodGroup": p["blood"], "age": p["age"], "gender": p["gender"],
        "createdAt": datetime.utcnow(), "_seeded": True
    })
    uid = str(u.inserted_id)
    patients_collection.insert_one({
        "userId": uid, "bloodGroup": p["blood"],
        "gender": p["gender"], "allergies": [],
        "createdAt": datetime.utcnow(), "_seeded": True
    })
    pat_ids.append({"userId": uid, **p})
    print(f"    + {p['fullName']} ({p['email']})")

# ──────────────────────────────────────────────
print("[*] Seeding admin...")
users_collection.delete_many({"email": "admin@medtrack.com", "_seeded": True})
users_collection.insert_one({
    "email": "admin@medtrack.com", "password": hash_pw("admin123"),
    "fullName": "Admin User", "role": "admin", "phone": "9999999999",
    "createdAt": datetime.utcnow(), "_seeded": True
})

# ──────────────────────────────────────────────
print("[*] Seeding appointments...")

today = datetime.utcnow()
appt_data = [
    # Upcoming
    {"pat": 0, "doc": 0, "days": +2,  "time": "10:00", "status": "approved",  "reason": "Chest pain and breathlessness"},
    {"pat": 0, "doc": 1, "days": +5,  "time": "11:30", "status": "pending",   "reason": "Skin rash and itching"},
    {"pat": 0, "doc": 6, "days": +1,  "time": "09:30", "status": "approved",  "reason": "Routine health checkup"},
    {"pat": 0, "doc": 3, "days": +7,  "time": "14:30", "status": "pending",   "reason": "Child vaccination schedule"},
    # Past
    {"pat": 0, "doc": 2, "days": -7,  "time": "14:00", "status": "completed", "reason": "Frequent headaches"},
    {"pat": 0, "doc": 4, "days": -14, "time": "15:00", "status": "completed", "reason": "Knee pain after jogging"},
    {"pat": 0, "doc": 0, "days": -21, "time": "10:00", "status": "completed", "reason": "Annual heart checkup"},
    # Other patients
    {"pat": 1, "doc": 5, "days": +3,  "time": "10:30", "status": "approved",  "reason": "Monthly checkup"},
    {"pat": 1, "doc": 3, "days": -3,  "time": "11:00", "status": "completed", "reason": "Child fever and cough"},
    {"pat": 2, "doc": 7, "days": +4,  "time": "16:00", "status": "pending",   "reason": "Ear pain and hearing difficulty"},
]

for a in appt_data:
    pat = pat_ids[a["pat"]]
    doc = doc_ids[a["doc"]]
    date = (today + timedelta(days=a["days"])).strftime("%Y-%m-%d")
    appointments_collection.insert_one({
        "patientId":    pat["userId"],
        "doctorId":     doc["userId"],
        "patientName":  pat["fullName"],
        "doctorName":   doc["fullName"],
        "specialization": doc["specialization"],
        "date":         date,
        "timeSlot":     a["time"],
        "reason":       a["reason"],
        "status":       a["status"],
        "isEmergency":  False,
        "createdAt":    datetime.utcnow(),
        "_seeded":      True
    })

print(f"    + {len(appt_data)} appointments created")

# ──────────────────────────────────────────────
print("[*] Seeding reviews...")

REVIEWS = [
    {"doc": 0, "pat": 0, "rating": 5, "comment": "Excellent cardiologist! Very thorough and explained everything clearly."},
    {"doc": 1, "pat": 1, "rating": 4, "comment": "Very knowledgeable. Helped completely with my skin allergy issue."},
    {"doc": 2, "pat": 0, "rating": 5, "comment": "Best neurologist I have visited. My headaches are completely gone."},
    {"doc": 4, "pat": 0, "rating": 4, "comment": "Great doctor for knee issues. Treatment worked perfectly."},
    {"doc": 6, "pat": 2, "rating": 5, "comment": "Very thorough in diagnosis. Extremely patient and kind doctor."},
]

for r in REVIEWS:
    reviews_collection.insert_one({
        "doctorId":    doc_ids[r["doc"]]["docId"],
        "patientId":   pat_ids[r["pat"]]["userId"],
        "patientName": pat_ids[r["pat"]]["fullName"],
        "rating":      r["rating"],
        "comment":     r["comment"],
        "createdAt":   datetime.utcnow(),
        "_seeded":     True
    })

# ──────────────────────────────────────────────
print("[*] Seeding notifications...")
notifications_collection.insert_one({
    "userId":    pat_ids[0]["userId"],
    "title":     "Appointment Confirmed",
    "message":   "Your appointment with Dr. Arun Kumar is confirmed.",
    "type":      "appointment",
    "readStatus": False,
    "createdAt": datetime.utcnow(),
    "_seeded":   True
})
notifications_collection.insert_one({
    "userId":    pat_ids[0]["userId"],
    "title":     "Welcome to MedTrack!",
    "message":   "Your account is active. Book your first appointment today.",
    "type":      "info",
    "readStatus": True,
    "createdAt": datetime.utcnow(),
    "_seeded":   True
})

# ──────────────────────────────────────────────
print("\n" + "="*55)
print("  SEEDING COMPLETE - DEMO CREDENTIALS")
print("="*55)
print()
print("  PATIENT LOGIN (has appointments, history)")
print("  Email   : vignesh@demo.com")
print("  Password: demo123")
print()
print("  DOCTOR LOGIN (Cardiologist with schedule)")
print("  Email   : arun@demo.com")
print("  Password: demo123")
print()
print("  ADMIN LOGIN (full system access)")
print("  Email   : admin@medtrack.com")
print("  Password: admin123")
print()
print("="*55)
print("  App URL : http://127.0.0.1:5000")
print("="*55)
print()
print("  HOW TO BOOK AN APPOINTMENT:")
print("  1. Login with vignesh@demo.com / demo123")
print("  2. Sidebar > 'Find Doctor'")
print("  3. Search by specialty (e.g. Cardiology)")
print("  4. Click 'Book Appointment' on any doctor")
print("  5. Pick a date and time slot > Confirm")
print()
