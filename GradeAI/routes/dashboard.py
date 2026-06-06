from flask import Blueprint, session, redirect, url_for, render_template_string
from functools import wraps
from services.google_auth import dict_to_credentials
from services.classroom import get_courses, get_coursework, get_course_info
import logging

dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "credentials" not in session:
            return redirect(url_for("auth.index"))
        return f(*args, **kwargs)
    return decorated


def get_credentials():
    return dict_to_credentials(session["credentials"])


def get_user():
    return session.get("user", {"name": "Teacher", "email": "", "picture": ""})


@dashboard_bp.route("/courses")
@login_required
def courses():
    try:
        creds = get_credentials()
        course_list = get_courses(creds)
        error = None
    except Exception as e:
        logger.error(f"Courses error: {e}")
        course_list = []
        error = str(e)

    return render_template_string(COURSES_PAGE,
        title="Courses", user=get_user(),
        courses=course_list, error=error)


@dashboard_bp.route("/course/<course_id>")
@login_required
def course(course_id):
    try:
        creds = get_credentials()
        course_info = get_course_info(creds, course_id)
        works = get_coursework(creds, course_id)
        error = None
    except Exception as e:
        logger.error(f"Coursework error: {e}")
        course_info = {"name": "Unknown Course", "id": course_id}
        works = []
        error = str(e)

    return render_template_string(COURSEWORK_PAGE,
        title=course_info.get("name", "Course"),
        user=get_user(),
        course=course_info,
        works=works,
        error=error)


# ── Shared layout (no Jinja blocks — plain string concatenation) ──────────────

_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} — GradeAI</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<style>
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
  :root{
    --bg:#0d0f14;--surface:#161922;--surface2:#1e2330;
    --border:#252a36;--border2:#2f3748;
    --accent:#6ee7b7;--accent2:#818cf8;--accent3:#f472b6;
    --text:#e2e8f0;--text2:#94a3b8;--muted:#4b5563;
    --success:#22c55e;--warning:#f59e0b;--danger:#ef4444;
  }
  html,body{height:100%;}
  body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column;}
  nav{position:sticky;top:0;z-index:100;display:flex;align-items:center;justify-content:space-between;
      padding:14px 32px;background:rgba(13,15,20,.85);border-bottom:1px solid var(--border);backdrop-filter:blur(12px);}
  .nav-brand{display:flex;align-items:center;gap:10px;text-decoration:none;}
  .nav-icon{width:34px;height:34px;background:linear-gradient(135deg,var(--accent2),var(--accent));
            border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:17px;}
  .nav-logo-text{font-family:'DM Serif Display',serif;font-size:20px;
                 background:linear-gradient(90deg,var(--accent2),var(--accent));
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
  .nav-right{display:flex;align-items:center;gap:16px;}
  .nav-user{display:flex;align-items:center;gap:10px;font-size:14px;color:var(--text2);}
  .nav-avatar{width:32px;height:32px;border-radius:50%;border:2px solid var(--border2);object-fit:cover;}
  .nav-avatar-ph{width:32px;height:32px;border-radius:50%;
                 background:linear-gradient(135deg,var(--accent2),var(--accent));
                 display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:#fff;}
  .btn-logout{padding:7px 14px;border:1px solid var(--border2);border-radius:8px;background:transparent;
              color:var(--text2);font-size:13px;font-family:'DM Sans',sans-serif;cursor:pointer;text-decoration:none;
              transition:border-color .2s,color .2s;}
  .btn-logout:hover{border-color:var(--danger);color:var(--danger);}
  main{flex:1;max-width:1100px;width:100%;margin:0 auto;padding:40px 32px;}
  .breadcrumb{display:flex;align-items:center;gap:8px;margin-bottom:28px;font-size:13px;color:var(--text2);}
  .breadcrumb a{color:var(--text2);text-decoration:none;}
  .breadcrumb a:hover{color:var(--accent);}
  .breadcrumb-sep{color:var(--muted);}
  .page-header{margin-bottom:32px;}
  .page-header h1{font-family:'DM Serif Display',serif;font-size:32px;font-weight:400;color:var(--text);margin-bottom:6px;}
  .page-header p{color:var(--text2);font-size:15px;}
  .card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:24px;transition:border-color .2s,transform .2s;}
  .card.clickable{cursor:pointer;}
  .card.clickable:hover{transform:translateY(-2px);border-color:var(--accent2);}
  .card a{text-decoration:none;color:inherit;display:block;}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}
  .badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:20px;
         font-size:11px;font-weight:600;letter-spacing:.5px;text-transform:uppercase;}
  .badge-green{background:rgba(110,231,183,.12);color:var(--accent);border:1px solid rgba(110,231,183,.2);}
  .badge-blue{background:rgba(129,140,248,.12);color:var(--accent2);border:1px solid rgba(129,140,248,.2);}
  .badge-pink{background:rgba(244,114,182,.12);color:var(--accent3);border:1px solid rgba(244,114,182,.2);}
  .tag{display:inline-block;padding:2px 8px;background:var(--surface2);border:1px solid var(--border);
       border-radius:6px;font-size:12px;color:var(--text2);}
  .divider{border:none;border-top:1px solid var(--border);margin:20px 0;}
  .empty{text-align:center;padding:64px 32px;color:var(--text2);}
  .empty-icon{font-size:48px;margin-bottom:16px;}
  .empty h3{font-size:18px;margin-bottom:8px;color:var(--text);}
  .alert{padding:14px 18px;border-radius:12px;margin-bottom:24px;font-size:14px;border:1px solid;}
  .alert-error{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.25);color:#fca5a5;}
  .flex{display:flex;}.items-center{align-items:center;}.justify-between{justify-content:space-between;}
  .gap-2{gap:8px;}.mb-1{margin-bottom:4px;}.mb-3{margin-bottom:16px;}
  .text-sm{font-size:13px;}.text-xs{font-size:12px;}.text-muted{color:var(--text2);}
  .font-medium{font-weight:500;}.font-serif{font-family:'DM Serif Display',serif;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);}}
  .animate{animation:fadeUp .4s ease both;}
  .delay-1{animation-delay:.05s;}.delay-2{animation-delay:.10s;}.delay-3{animation-delay:.15s;}
</style>
</head>
<body>
<nav>
  <a href="/courses" class="nav-brand">
    <div class="nav-icon">🎓</div>
    <span class="nav-logo-text">GradeAI</span>
  </a>
  <div class="nav-right">
    {% if user %}
    <div class="nav-user">
      {% if user.picture %}
        <img src="{{ user.picture }}" class="nav-avatar" alt="{{ user.name }}">
      {% else %}
        <div class="nav-avatar-ph">{{ user.name[0] }}</div>
      {% endif %}
      <span>{{ user.name }}</span>
    </div>
    {% endif %}
    <a href="/logout" class="btn-logout">Sign out</a>
  </div>
</nav>
<main>
{% if error %}<div class="alert alert-error"> {{ error }}</div>{% endif %}
"""

_FOOT = "</main></body></html>"


# ── Courses page ──────────────────────────────────────────────────────────────

COURSES_PAGE = _HEAD + """
<div class="page-header animate">
  <h1>Your Classrooms</h1>
  <p>Select a course to view assignments and grade submissions.</p>
</div>

{% if courses %}
<div class="grid">
  {% for c in courses %}
  <div class="card clickable animate delay-{{ (loop.index % 3) + 1 }}">
    <a href="/course/{{ c.id }}">
      <div class="flex items-center justify-between mb-3">
        <span class="badge badge-green">Active</span>
        <span class="text-xs text-muted">{{ c.get('section', '') }}</span>
      </div>
      <h3 class="font-serif" style="font-size:20px;margin-bottom:8px;">{{ c.name }}</h3>
      {% if c.get('description') %}
        <p class="text-sm text-muted" style="line-height:1.5;">
          {{ c.description[:100] }}{% if c.description|length > 100 %}…{% endif %}
        </p>
      {% endif %}
      <div class="divider"></div>
      <div class="flex items-center gap-2 text-xs text-muted">
        <span>🏫 {{ c.get('room', 'No room') }}</span>
        <span style="margin-left:auto;">View Assignments →</span>
      </div>
    </a>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="empty">
  <div class="empty-icon">📚</div>
  <h3>No Active Courses</h3>
  <p>Your Google Classroom doesn't have any active courses yet.</p>
</div>
{% endif %}
""" + _FOOT


# ── Coursework page ───────────────────────────────────────────────────────────

COURSEWORK_PAGE = _HEAD + """
<div class="breadcrumb animate">
  <a href="/courses">Courses</a>
  <span class="breadcrumb-sep">›</span>
  <span>{{ course.name }}</span>
</div>

<div class="page-header animate">
  <h1>{{ course.name }}</h1>
  <p>Select an assignment to run AI grading on student submissions.</p>
</div>

{% if works %}
<div style="display:flex;flex-direction:column;gap:12px;">
  {% for w in works %}
  <div class="card animate delay-{{ (loop.index % 3) + 1 }}"
       style="display:flex;align-items:center;justify-content:space-between;gap:16px;">
    <div style="flex:1;">
      <div class="flex items-center gap-2 mb-1">
        {% if w.get('workType') == 'ASSIGNMENT' %}
          <span class="badge badge-blue">Assignment</span>
        {% elif w.get('workType') == 'SHORT_ANSWER_QUESTION' %}
          <span class="badge badge-pink">Quiz</span>
        {% else %}
          <span class="badge badge-blue">{{ w.get('workType', 'Work') }}</span>
        {% endif %}
        {% if w.get('dueDate') %}
          <span class="tag">
            Due: {{ w.dueDate.get('month','') }}/{{ w.dueDate.get('day','') }}/{{ w.dueDate.get('year','') }}
          </span>
        {% endif %}
      </div>
      <h3 class="font-medium" style="font-size:16px;">{{ w.title }}</h3>
      {% if w.get('description') %}
        <p class="text-sm text-muted" style="margin-top:4px;">
          {{ w.description[:120] }}{% if w.description|length > 120 %}…{% endif %}
        </p>
      {% endif %}
    </div>
    <a href="/grade/{{ course.id }}/{{ w.id }}"
       style="flex-shrink:0;padding:10px 20px;
              background:linear-gradient(135deg,#818cf8,#6ee7b7);
              border-radius:10px;color:#0d0f14;font-size:13px;font-weight:600;
              text-decoration:none;white-space:nowrap;transition:opacity .2s;"
       onmouseover="this.style.opacity=.8" onmouseout="this.style.opacity=1">
      Grade with AI →
    </a>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="empty">
  <div class="empty-icon">📝</div>
  <h3>No Assignments Found</h3>
  <p>This course doesn't have any assignments yet.</p>
</div>
{% endif %}
""" + _FOOT
