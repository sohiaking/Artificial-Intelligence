import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-use-env-var")
    SESSION_COOKIE_NAME = "grading-session"
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Google OAuth
    GOOGLE_CLIENT_SECRETS_FILE = os.environ.get("GOOGLE_CLIENT_SECRETS_FILE", "client_secret.json")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/callback")
    GOOGLE_SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/classroom.courses.readonly",
        "https://www.googleapis.com/auth/classroom.coursework.students",
        "https://www.googleapis.com/auth/classroom.coursework.me",
        "https://www.googleapis.com/auth/classroom.rosters",
        "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    ]

    # Gemini AI
    GEMINI_API_KEY = "AIzaSyDu8ynmY4ud9M25lmxfvG43-rV9fw90mvQ"
    GEMINI_MODEL = "gemini-2.5-flash"

    # Dev only — remove in production
    OAUTHLIB_INSECURE_TRANSPORT = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT", "1")
