# MedTrack Database Schema

## Collections Overview

### 1. `users`
Stores authentication data for all users (patients, doctors, admins).

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| email | String | Unique, indexed |
| password | String | bcrypt hashed |
| role | String | 'patient', 'doctor', 'admin' |
| fullName | String | Display name |
| phone | String | Contact number |
| createdAt | DateTime | Registration timestamp |
| updatedAt | DateTime | Last update |

---

### 2. `doctors`
Doctor profile information linked to a user.

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| userId | String | Reference to users._id |
| specialization | String | Medical specialty |
| qualification | String | MBBS, MD, etc. |
| experienceYears | Number | Years of experience |
| consultationFee | Number | Fee in INR |
| availability | Object | Weekly schedule |
| bio | String | Short bio |
| avgRating | Number | Average rating (1-5) |
| totalReviews | Number | Review count |
| isApproved | Boolean | Admin approval status |
| slotDurationMinutes | Number | Slot duration (default: 15) |

---

### 3. `patients`
Patient profile with health data.

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| userId | String | Reference to users._id |
| dateOfBirth | String | DOB |
| gender | String | male/female/other |
| bloodGroup | String | A+, B-, O+, etc. |
| address | String | Home address |
| emergencyContact | String | Emergency phone |
| allergies | Array | List of allergies |
| conditions | Array | Medical conditions |

---

### 4. `appointments`
All appointment bookings.

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| patientId | String | Reference to patients._id |
| doctorId | String | Reference to doctors._id |
| date | String | YYYY-MM-DD |
| timeSlot | String | HH:MM format |
| reason | String | Visit reason |
| status | String | pending/approved/completed/cancelled/prescription_uploaded |
| isEmergency | Boolean | Emergency flag |
| prescription | String | Prescribed medicines/instructions |
| notes | String | Doctor's notes |

---

### 5. `medical_records`
Patient health timeline records.

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| patientId | String | Reference to patients._id |
| doctorId | String | Uploading doctor's userId |
| recordType | String | blood_test/prescription/scan/consultation/report |
| title | String | Record title |
| description | String | Details |
| filePath | String | Upload path |
| createdAt | DateTime | Upload timestamp |

---

### 6. `notifications`
System notifications for users.

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| userId | String | Target user's ID |
| message | String | Notification text |
| type | String | info/appointment/prescription/alert/emergency |
| readStatus | Boolean | Read flag |
| createdAt | DateTime | Timestamp |

---

### 7. `reviews`
Doctor review ratings from patients.

| Field | Type | Description |
|-------|------|-------------|
| _id | ObjectId | Auto-generated |
| patientId | String | Reference to patients._id |
| doctorId | String | Reference to doctors._id |
| rating | Number | 1-5 stars |
| comment | String | Review text |
| createdAt | DateTime | Timestamp |
