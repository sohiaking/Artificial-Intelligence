from flask import Blueprint, redirect, session, request, url_for, render_template_string
from services.google_auth import create_flow, credentials_to_dict
import requests as http_requests
import logging

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/")
def index():
    if "credentials" in session:
        return redirect(url_for("dashboard.courses"))
    return render_template_string(LOGIN_PAGE)


@auth_bp.route("/login")
def login():
    session.clear()
    flow = create_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    session["state"] = state
    if flow.code_verifier:
        session["code_verifier"] = flow.code_verifier
    return redirect(auth_url)


@auth_bp.route("/callback")
def callback():
    if "error" in request.args:
        logger.warning(f"OAuth error: {request.args.get('error')}")
        return redirect(url_for("auth.index"))

    flow = create_flow()
    flow.code_verifier = session.get("code_verifier")

    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception as e:
        logger.error(f"Token fetch failed: {e}")
        return redirect(url_for("auth.index"))

    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)

    # Fetch user info
    try:
        userinfo = http_requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"}
        ).json()
        session["user"] = {
            "name": userinfo.get("name", "Teacher"),
            "email": userinfo.get("email", ""),
            "picture": userinfo.get("picture", ""),
        }
    except Exception as e:
        logger.warning(f"Could not fetch user info: {e}")
        session["user"] = {"name": "Teacher", "email": "", "picture": ""}

    return redirect(url_for("dashboard.courses"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.index"))


LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GradeAI — Login</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0d0f14;
    --surface: #161922;
    --border: #252a36;
    --accent: #6ee7b7;
    --accent2: #818cf8;
    --text: #e2e8f0;
    --muted: #64748b;
  }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .bg-grid {
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(var(--border) 1px, transparent 1px),
      linear-gradient(90deg, var(--border) 1px, transparent 1px);
    background-size: 48px 48px;
    opacity: 0.4;
  }

  .glow {
    position: fixed;
    width: 600px; height: 600px;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.12;
    pointer-events: none;
  }
  .glow-1 { top: -200px; left: -100px; background: var(--accent2); }
  .glow-2 { bottom: -200px; right: -100px; background: var(--accent); }

  .card {
    position: relative; z-index: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 56px 48px;
    width: 100%;
    max-width: 440px;
    text-align: center;
    animation: fadeUp 0.6s ease both;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .logo {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 32px;
  }

  .logo-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--accent2), var(--accent));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
  }

  .logo-text {
    font-family: 'DM Serif Display', serif;
    font-size: 26px;
    background: linear-gradient(90deg, var(--accent2), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    color: var(--text);
    margin-bottom: 10px;
  }

  p {
    color: var(--muted);
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 36px;
  }

  .btn-google {
    display: flex; align-items: center; justify-content: center; gap: 12px;
    width: 100%;
    padding: 15px 24px;
    background: white;
    color: #1f2937;
    border: none; border-radius: 12px;
    font-family: 'DM Sans', sans-serif;
    font-size: 15px; font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    transition: transform 0.15s, box-shadow 0.15s;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  }

  .btn-google:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
  }

  .btn-google svg { width: 20px; height: 20px; }

  .features {
    display: flex; flex-direction: column; gap: 10px;
    margin-top: 32px; padding-top: 32px;
    border-top: 1px solid var(--border);
    text-align: left;
  }

  .feature {
    display: flex; align-items: center; gap: 10px;
    font-size: 13px; color: var(--muted);
  }

  .feature-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
  }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="glow glow-1"></div>
<div class="glow glow-2"></div>

<div class="card">
  <div class="logo">
    <div class="logo-icon">🎓</div>
    <span class="logo-text">GradeAI</span>
  </div>

  <h1>AI-Powered Grading</h1>
  <p>Connect your Google Classroom and let Gemini AI evaluate student submissions with detailed rubric-based feedback.</p>

  <a href="/login" class="btn-google">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
    Continue with Google
  </a>

  <div class="features">
    <div class="feature"><div class="feature-dot"></div>Rubric-based scoring across 5 criteria</div>
    <div class="feature"><div class="feature-dot"></div>Strengths & improvement suggestions</div>
    <div class="feature"><div class="feature-dot"></div>Plagiarism flag detection</div>
    <div class="feature"><div class="feature-dot"></div>Works with PDF & text submissions</div>
  </div>
</div>
</body>
</html>
"""
