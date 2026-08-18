import os
import firebase_admin
from firebase_admin import auth, credentials, firestore
from config import Config


def _initialize_firebase():
    if firebase_admin._apps:
        return True
    service_account = Config.FIREBASE_SERVICE_ACCOUNT
    if not os.path.exists(service_account):
        return False
    firebase_admin.initialize_app(credentials.Certificate(service_account))
    return True


FIREBASE_CONFIGURED = _initialize_firebase()
db = firestore.client() if FIREBASE_CONFIGURED else None


def require_db():
    if db is None:
        raise RuntimeError(
            "Firebase Admin is not configured. Add firebase/serviceAccountKey.json "
            "or set FIREBASE_SERVICE_ACCOUNT to a valid service-account JSON path."
        )
    return db


def verify_id_token(id_token: str) -> dict:
    if not FIREBASE_CONFIGURED:
        raise ValueError("Firebase Admin is not configured on the server.")
    if not id_token:
        raise ValueError("Authentication token is required.")
    try:
        return auth.verify_id_token(id_token)
    except auth.ExpiredIdTokenError as exc:
        raise ValueError("Session expired. Please log in again.") from exc
    except auth.InvalidIdTokenError as exc:
        raise ValueError("Invalid authentication token.") from exc
    except Exception as exc:
        raise ValueError("Authentication verification failed.") from exc
