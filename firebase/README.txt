FIREBASE SETUP

1. Firebase Console -> Authentication -> Sign-in method -> enable Email/Password.
2. Firebase Console -> Firestore Database -> Create database.
3. Project Settings -> Service Accounts -> Firebase Admin SDK -> Generate new private key.
4. Save the downloaded JSON as firebase/serviceAccountKey.json. Never commit or share it.
5. Copy `.env.example` to `.env` and set `MISTRAL_API_KEY`.
6. The frontend Firebase config is in static/js/firebase.js.

Firestore user document model
users/{uid}
  Student: role, name, email, reg_no, department, year, semester, goal, bio, created_at, updated_at
  Faculty: role, name, email, employee_id, department, designation, subjects, created_at, updated_at

Subcollections
users/{studentUid}/documents/{documentId}
users/{studentUid}/documents/{documentId}/chunks/{chunkId}
users/{studentUid}/faculty_notes/{noteId}
announcements/{announcementId}
