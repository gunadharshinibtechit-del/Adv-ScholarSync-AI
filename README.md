# ScholarSync AI — Student + Faculty Academic Portal

This version turns ScholarSync into a role-based academic platform. Students and faculty have separate login/register portals and separate dashboards.

## Student portal
- Firebase Email/Password authentication
- Firestore academic identity: name, register number, department, year, semester, goal, learning style
- AI Chat
- PDF/TXT study vault and document-grounded answers
- Exam Answer Studio (2/5/10/13/16 marks)
- AI Quiz
- Smart Planner
- Viva practice
- Faculty announcements
- Dedicated student profile

## Faculty portal
- Separate Firebase login/register
- Firestore faculty identity: name, employee ID, department, designation, subjects
- Student Directory with filters for name/register number, department, year and semester
- Student academic profile viewer
- Student study-file metadata viewer
- Private mentoring notes stored under the student record
- Faculty announcements
- Faculty AI Copilot

## Firebase
Passwords are handled by Firebase Authentication and are not stored in Firestore. Academic profile data is stored in Firestore. The Flask backend uses Firebase Admin SDK to verify tokens and enforce student/faculty permissions. See `firebase/firestore.rules` and `firebase/README.txt`.

## Setup
1. `python -m venv venv`
2. Windows PowerShell: `venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`.
5. Add the Firebase Admin service account JSON at `firebase/serviceAccountKey.json`.
6. Set `MISTRAL_API_KEY` in your `.env` file.
7. Run `python app.py`.
8. Open `http://127.0.0.1:5000`.

## Important
The server never trusts a client-supplied faculty role. Faculty-only APIs check the Firestore role, and Student/Faculty portals remain separate.
