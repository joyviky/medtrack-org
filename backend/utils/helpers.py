from datetime import datetime, timedelta


def generate_time_slots(start_time, end_time, duration_minutes=15):
    """Generate appointment time slots between start and end times."""
    slots = []
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")

    current = start
    while current + timedelta(minutes=duration_minutes) <= end:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration_minutes)

    return slots


def format_user(user):
    """Convert MongoDB user document to JSON-safe dict."""
    if user:
        user["_id"] = str(user["_id"])
        user.pop("password", None)
    return user


def format_doc(doc):
    """Convert any MongoDB document ObjectId to string."""
    if doc:
        doc["_id"] = str(doc["_id"])
    return doc


def format_docs(docs):
    """Convert list of MongoDB documents."""
    return [format_doc(doc) for doc in docs]


SYMPTOM_DEPARTMENT_MAP = {
    "headache": ["Neurology", "General Physician"],
    "fever": ["General Physician", "Internal Medicine"],
    "cough": ["ENT", "Pulmonology", "General Physician"],
    "chest pain": ["Cardiology", "Emergency"],
    "stomach pain": ["Gastroenterology", "General Physician"],
    "skin rash": ["Dermatology"],
    "back pain": ["Orthopedics", "General Physician"],
    "eye pain": ["Ophthalmology"],
    "tooth pain": ["Dentistry"],
    "anxiety": ["Psychiatry", "Psychology"],
    "depression": ["Psychiatry", "Psychology"],
    "joint pain": ["Orthopedics", "Rheumatology"],
    "breathing difficulty": ["Pulmonology", "Emergency"],
    "dizziness": ["Neurology", "ENT"],
    "ear pain": ["ENT"],
    "sore throat": ["ENT", "General Physician"],
    "nausea": ["Gastroenterology", "General Physician"],
    "vomiting": ["Gastroenterology", "Emergency"],
    "fatigue": ["Internal Medicine", "General Physician"],
    "weight loss": ["Endocrinology", "Internal Medicine"],
    "diabetes": ["Endocrinology"],
    "blood pressure": ["Cardiology", "Internal Medicine"],
    "pregnancy": ["Obstetrics", "Gynecology"],
    "child": ["Pediatrics"],
    "fracture": ["Orthopedics", "Emergency"],
    "allergy": ["Dermatology", "General Physician"],
    "urinary": ["Urology", "Nephrology"],
}


def suggest_departments(symptoms_text):
    """Suggest departments based on symptom keywords."""
    symptoms_text = symptoms_text.lower()
    suggested = set()
    matched_symptoms = []

    for symptom, departments in SYMPTOM_DEPARTMENT_MAP.items():
        if symptom in symptoms_text:
            suggested.update(departments)
            matched_symptoms.append(symptom)

    if not suggested:
        suggested.add("General Physician")

    return {
        "matchedSymptoms": matched_symptoms,
        "suggestedDepartments": list(suggested)
    }
