import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    UPLOAD_FOLDER = str(BASE_DIR / os.getenv("UPLOAD_FOLDER", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "25")) * 1024 * 1024

    FIREBASE_SERVICE_ACCOUNT = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT", "firebase/serviceAccountKey.json"
    )
    if not os.path.isabs(FIREBASE_SERVICE_ACCOUNT):
        FIREBASE_SERVICE_ACCOUNT = str(BASE_DIR / FIREBASE_SERVICE_ACCOUNT)

    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or os.getenv("AI_API_KEY")
    MISTRAL_BASE_URL = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai/v1").rstrip("/")
    MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
