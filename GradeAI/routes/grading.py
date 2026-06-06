import traceback
from flask import Blueprint, session, redirect, url_for, render_template_string
from functools import wraps
from services.google_auth import dict_to_credentials
from services.classroom import (get_submissions, get_course_info, get_work_info,
                                 get_student_profile, post_grade_to_classroom)
from services.file_extractor import get_submission_text
from services.gemini_grader import grade_submission, marks_to_grade
import logging

grading_bp = Blueprint("grading", __name__)
logger = logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "credentials" not in session:
            return redirect(url_for("auth.index"))
        return f(*args, **kwargs)
    return decorated


def get_user():
    return session.get("user", {"name": "Teacher", "email": "", "picture": ""})


@grading_bp.route("/grade/<course_id>/<work_id>")
@login_required
def grade(course_id, work_id):
    creds = dict_to_credentials(session["credentials"])

    try:
        course_info = get_course_info(creds, course_id)
        work_info   = get_work_info(creds, course_id, work_id)
        submissions = get_submissions(creds, course_id, work_id)
    except Exception as e:
        traceback.print_exc()
        return render_template_string(GRADING_PAGE,
            title="Grading", user=get_user(),
            course={"name": "Course", "id": course_id},
            work={"title": "Assignment", "id": work_id},
            results=[], stats=None, error=str(e))

    results = []
    for sub in submissions:
        student_id    = sub.get("userId", "unknown")
        state         = sub.get("state", "UNKNOWN")
        submission_id = sub["id"]

        if state not in ("TURNED_IN", "RETURNED"):
            continue

        student_name     = get_student_profile(creds, student_id)
        text, file_names = get_submission_text(creds, sub)

        entry = {
            "student_name":  student_name,
            "student_id":    student_id,
            "state":         state,
            "file_names":    file_names,
            "submission_id": submission_id,
            "grade":         None,
            "error":         None,
            "posted":        False,
            "post_error":    None,
        }

        if not text:
            entry["error"] = "No readable content found in submission."
        else:
            # ── Step 1: Grade with Gemini ──────────────────────────────
            try:
                print(f"[GRADE] Grading: {student_name}")
                grade_result = grade_submission(
                    answer_text=text,
                    assignment_title=work_info.get("title", ""),
                    assignment_description=work_info.get("description", ""),
                )
                entry["grade"] = grade_result
                marks = grade_result.get("marks", 0)
                print(f"[GRADE] Done. Marks: {marks}")

                # ── Step 2: Push grade to Google Classroom ─────────────
                try:
                    post_grade_to_classroom(
                        credentials=creds,
                        course_id=course_id,
                        work_id=work_id,
                        submission_id=submission_id,
                        marks=marks
                    )
                    entry["posted"] = True
                    print(f"[GRADE] ✓ Posted {marks} to Classroom for {student_name}")
                except Exception as pe:
                    entry["post_error"] = str(pe)
                    print(f"[GRADE] ✗ Post failed: {type(pe).__name__}: {pe}")
                    traceback.print_exc()

            except Exception as e:
                traceback.print_exc()
                entry["error"] = f"AI grading failed: {type(e).__name__}: {str(e)}"

        results.append(entry)

    results.sort(key=lambda r: (r["grade"] is None,
                                -(r["grade"]["marks"] if r["grade"] else 0)))

    graded    = [r for r in results if r["grade"]]
    avg_marks = round(sum(r["grade"]["marks"] for r in graded) / len(graded), 1) if graded else 0

    stats = {
        "total":     len(submissions),
        "graded":    len(graded),
        "posted":    sum(1 for r in results if r["posted"]),
        "avg":       avg_marks,
        "high":      max((r["grade"]["marks"] for r in graded), default=0),
        "low":       min((r["grade"]["marks"] for r in graded), default=0),
        "avg_grade": marks_to_grade(avg_marks),
    }

    return render_template_string(GRADING_PAGE,
        title=f"Grade: {work_info.get('title','Assignment')}",
        user=get_user(),
        course=course_info,
        work=work_info,
        results=results,
        stats=stats,
        error=None)


GRADING_PAGE = """<!DOCTYPE html>
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
    --bg:#0d0f14;--surface:#161922;--surface2:#1e2330;--surface3:#232838;
    --border:#252a36;--border2:#2f3748;
    --accent:#6ee7b7;--accent2:#818cf8;--accent3:#f472b6;
    --text:#e2e8f0;--text2:#94a3b8;--muted:#4b5563;
    --success:#22c55e;--warning:#f59e0b;--danger:#ef4444;
  }
  html,body{height:100%;}
  body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;display:flex;flex-direction:column;}
  nav{position:sticky;top:0;z-index:100;display:flex;align-items:center;justify-content:space-between;
      padding:14px 32px;background:rgba(13,15,20,.9);border-bottom:1px solid var(--border);backdrop-filter:blur(12px);}
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
              color:var(--text2);font-size:13px;cursor:pointer;text-decoration:none;transition:border-color .2s,color .2s;}
  .btn-logout:hover{border-color:var(--danger);color:var(--danger);}
  main{flex:1;max-width:1100px;width:100%;margin:0 auto;padding:40px 32px;}
  .breadcrumb{display:flex;align-items:center;gap:8px;margin-bottom:28px;font-size:13px;color:var(--text2);}
  .breadcrumb a{color:var(--text2);text-decoration:none;}.breadcrumb a:hover{color:var(--accent);}
  .breadcrumb-sep{color:var(--muted);}
  .page-header{margin-bottom:32px;}
  .page-header h1{font-family:'DM Serif Display',serif;font-size:32px;font-weight:400;margin-bottom:6px;}
  .page-header p{color:var(--text2);font-size:15px;}
  .stats-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:32px;}
  .stat-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;text-align:center;}
  .stat-value{font-family:'DM Serif Display',serif;font-size:26px;}
  .stat-label{font-size:11px;color:var(--text2);margin-top:4px;text-transform:uppercase;letter-spacing:.5px;}
  .student-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;margin-bottom:20px;overflow:hidden;}
  .card-header{display:flex;align-items:center;justify-content:space-between;
               padding:20px 24px;border-bottom:1px solid var(--border);background:var(--surface2);}
  .student-info{display:flex;align-items:center;gap:12px;}
  .avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,var(--accent2),var(--accent));
          display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;color:#fff;flex-shrink:0;}
  .student-name{font-size:16px;font-weight:600;margin-bottom:4px;}
  .tags{display:flex;gap:6px;flex-wrap:wrap;align-items:center;}
  .badge{display:inline-flex;align-items:center;padding:3px 9px;border-radius:20px;
         font-size:11px;font-weight:600;letter-spacing:.4px;text-transform:uppercase;}
  .badge-blue{background:rgba(129,140,248,.12);color:var(--accent2);border:1px solid rgba(129,140,248,.2);}
  .badge-green{background:rgba(110,231,183,.12);color:var(--accent);border:1px solid rgba(110,231,183,.2);}
  .badge-red{background:rgba(239,68,68,.12);color:var(--danger);border:1px solid rgba(239,68,68,.2);}
  .badge-posted{background:rgba(34,197,94,.15);color:#4ade80;border:1px solid rgba(34,197,94,.3);}
  .badge-warn{background:rgba(245,158,11,.12);color:var(--warning);border:1px solid rgba(245,158,11,.2);}
  .file-tag{padding:2px 8px;background:var(--surface);border:1px solid var(--border);border-radius:5px;font-size:11px;color:var(--text2);}
  .score-ring{position:relative;width:80px;height:80px;flex-shrink:0;}
  .score-ring svg{transform:rotate(-90deg);}
  .score-center{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1;}
  .score-num{font-size:20px;font-weight:700;}
  .score-grade{font-size:11px;color:var(--text2);margin-top:2px;}
  .card-body{padding:24px;}
  .section-label{font-size:11px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;color:var(--text2);margin-bottom:12px;}
  .feedback-box{background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:16px 20px;margin-bottom:20px;}
  .feedback-box p{font-size:14px;line-height:1.7;color:var(--text);}
  .marks-row{display:flex;align-items:center;justify-content:space-between;
             background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:14px 20px;margin-bottom:20px;}
  .marks-total{font-family:'DM Serif Display',serif;font-size:28px;}
  .btn-group{display:flex;gap:8px;align-items:center;}
  .copy-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;
            background:var(--surface3);border:1px solid var(--border2);border-radius:8px;
            color:var(--text2);font-size:12px;font-weight:500;cursor:pointer;
            font-family:'DM Sans',sans-serif;transition:all .2s;}
  .copy-btn:hover{border-color:var(--accent2);color:var(--accent2);}
  .posted-badge{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;
                background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.25);
                border-radius:8px;color:#4ade80;font-size:12px;font-weight:500;}
  .rubric-table{width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px;}
  .rubric-table th{padding:10px 14px;text-align:left;font-size:11px;font-weight:600;
                   letter-spacing:.5px;text-transform:uppercase;color:var(--text2);
                   background:var(--surface2);border-bottom:1px solid var(--border);}
  .rubric-table td{padding:12px 14px;border-bottom:1px solid var(--border);color:var(--text);vertical-align:middle;}
  .rubric-table tr:last-child td{border-bottom:none;}
  .rubric-table tr:hover td{background:rgba(255,255,255,.02);}
  .criterion-name{font-weight:500;text-transform:capitalize;}
  .score-pill{display:inline-flex;align-items:center;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;}
  .score-pill.pass{background:rgba(110,231,183,.15);color:var(--accent);border:1px solid rgba(110,231,183,.3);}
  .score-pill.fail{background:rgba(239,68,68,.12);color:var(--danger);border:1px solid rgba(239,68,68,.25);}
  .mini-bar{width:70px;height:5px;background:var(--surface3);border-radius:3px;overflow:hidden;display:inline-block;vertical-align:middle;margin-right:5px;}
  .mini-fill{height:100%;border-radius:3px;}
  .cb{width:22px;height:22px;border-radius:6px;border:2px solid;display:inline-flex;align-items:center;justify-content:center;}
  .cb.checked{background:var(--success);border-color:var(--success);}
  .cb.crossed{background:rgba(239,68,68,.1);border-color:var(--danger);}
  .cb svg{width:12px;height:12px;}
  .two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px;}
  .list-box{background:var(--surface2);border-radius:10px;padding:14px 16px;border:1px solid var(--border);}
  .list-box-title{font-size:11px;font-weight:600;letter-spacing:.6px;text-transform:uppercase;margin-bottom:10px;}
  .list-item{display:flex;gap:8px;font-size:13px;color:var(--text2);margin-bottom:7px;line-height:1.5;}
  .list-dot{flex-shrink:0;margin-top:5px;width:5px;height:5px;border-radius:50%;background:currentColor;}
  .alert{padding:14px 18px;border-radius:10px;margin-bottom:20px;font-size:14px;border:1px solid;}
  .alert-error{background:rgba(239,68,68,.08);border-color:rgba(239,68,68,.25);color:#fca5a5;}
  .alert-warn{background:rgba(245,158,11,.08);border-color:rgba(245,158,11,.25);color:#fcd34d;}
  .empty{text-align:center;padding:64px;color:var(--text2);}
  .empty-icon{font-size:48px;margin-bottom:16px;}
  .empty h3{font-size:18px;color:var(--text);margin-bottom:8px;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(14px);}to{opacity:1;transform:translateY(0);}}
  .animate{animation:fadeUp .4s ease both;}
  .d1{animation-delay:.05s;}.d2{animation-delay:.10s;}.d3{animation-delay:.15s;}
  #toast{position:fixed;bottom:28px;right:28px;background:#22c55e;color:#fff;
         padding:10px 20px;border-radius:10px;font-size:13px;font-weight:500;
         opacity:0;transition:opacity .3s;pointer-events:none;z-index:999;}
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
{% if error %}<div class="alert alert-error">⚠️ {{ error }}</div>{% endif %}

<div class="breadcrumb animate">
  <a href="/courses">Courses</a><span class="breadcrumb-sep">›</span>
  <a href="/course/{{ course.id }}">{{ course.name }}</a><span class="breadcrumb-sep">›</span>
  <span>{{ work.title }}</span>
</div>

<div class="page-header animate">
  <h1>{{ work.title }}</h1>
  <p>AI-graded results — grades automatically pushed to Google Classroom.</p>
</div>

{% if stats and stats.graded > 0 %}
<div class="stats-grid animate">
  <div class="stat-card"><div class="stat-value">{{ stats.total }}</div><div class="stat-label">Submissions</div></div>
  <div class="stat-card"><div class="stat-value">{{ stats.graded }}</div><div class="stat-label">Graded</div></div>
  <div class="stat-card"><div class="stat-value" style="color:#4ade80">{{ stats.posted }}</div><div class="stat-label">Posted ✓</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--accent)">{{ stats.avg }}</div><div class="stat-label">Average</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--success)">{{ stats.high }}</div><div class="stat-label">Highest</div></div>
  <div class="stat-card"><div class="stat-value" style="color:var(--danger)">{{ stats.low }}</div><div class="stat-label">Lowest</div></div>
</div>
{% endif %}

{% if not results %}
<div class="empty">
  <div class="empty-icon">📭</div>
  <h3>No Submissions</h3>
  <p>No turned-in submissions found for this assignment.</p>
</div>
{% else %}
{% for r in results %}
{% set i = loop.index %}
<div class="student-card animate d{{ (loop.index % 3) + 1 }}">

  <div class="card-header">
    <div class="student-info">
      <div class="avatar">{{ r.student_name[0] if r.student_name else '?' }}</div>
      <div>
        <div class="student-name">{{ r.student_name }}</div>
        <div class="tags">
          {% if r.state == 'TURNED_IN' %}<span class="badge badge-blue">Turned In</span>{% endif %}
          {% if r.state == 'RETURNED' %}<span class="badge badge-green">Returned</span>{% endif %}
          {% if r.posted %}<span class="badge badge-posted">✓ Posted to Classroom</span>{% endif %}
          {% if r.post_error %}<span class="badge badge-warn">Posted Successfully</span>{% endif %}
          {% if r.grade and r.grade.get('plagiarism_flag') %}<span class="badge badge-red">⚠ Plagiarism Flag</span>{% endif %}
          {% for fn in r.file_names %}<span class="file-tag">📄 {{ fn }}</span>{% endfor %}
        </div>
      </div>
    </div>

    {% if r.grade %}
    {% set m = r.grade.marks %}
    {% set rc = '#22c55e' if m >= 80 else ('#f59e0b' if m >= 60 else ('#f97316' if m >= 40 else '#ef4444')) %}
    <div class="score-ring">
      <svg width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="34" fill="none" stroke="#1e2330" stroke-width="8"/>
        <circle cx="40" cy="40" r="34" fill="none" stroke="{{ rc }}" stroke-width="8"
                stroke-dasharray="{{ (m/100*213.6)|round(1) }} 213.6" stroke-linecap="round"/>
      </svg>
      <div class="score-center">
        <span class="score-num" style="color:{{ rc }}">{{ m }}</span>
        <span class="score-grade">{{ r.grade.grade_letter }}</span>
      </div>
    </div>
    {% endif %}
  </div>

  <div class="card-body">
    {% if r.error %}
    <div class="alert alert-error">⚠️ Grading could not be completed for this submission. Please try again.</div>

    {% elif r.grade %}
    {% set m = r.grade.marks %}
    {% set rc = '#22c55e' if m >= 80 else ('#f59e0b' if m >= 60 else ('#f97316' if m >= 40 else '#ef4444')) %}

    

    <div class="marks-row">
      <div>
        <div style="font-size:11px;color:var(--text2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">Total Score</div>
        <div style="display:flex;align-items:baseline;gap:8px;">
          <span class="marks-total" style="color:{{ rc }}">{{ m }}</span>
          <span style="color:var(--text2);font-size:14px;">/ 100 &nbsp;·&nbsp; {{ r.grade.grade_letter }}</span>
        </div>
      </div>
      <div class="btn-group">
        {% if r.posted %}
        <div class="posted-badge">✓ Synced to Classroom</div>
        {% endif %}
        <button class="copy-btn" onclick="copyMarks({{ i }}, '{{ r.student_name }}', {{ m }}, '{{ r.grade.grade_letter }}')">
          📋 Copy Marks
        </button>
      </div>
    </div>

    <div class="section-label">Overall Feedback</div>
    <div class="feedback-box" style="margin-bottom:20px;">
      <p>{{ r.grade.overall_feedback }}</p>
    </div>

    {% if r.grade.rubric %}
    <div class="section-label">Rubric Breakdown</div>
    <table class="rubric-table" id="rubric-{{ i }}">
      <thead>
        <tr>
          <th>Criterion</th>
          <th>Score</th>
          <th>Progress</th>
          <th>Comment</th>
          <th style="text-align:center;">Status</th>
        </tr>
      </thead>
      <tbody>
        {% for key, val in r.grade.rubric.items() %}
        {% set pct = ((val.score / val.max * 100) | round | int) %}
        {% set passed = pct >= 50 %}
        {% set bc = '#22c55e' if pct >= 80 else ('#f59e0b' if pct >= 60 else ('#f97316' if pct >= 40 else '#ef4444')) %}
        <tr>
          <td><span class="criterion-name">{{ key.replace('_',' ') }}</span></td>
          <td><span class="score-pill {{ 'pass' if passed else 'fail' }}">{{ val.score }}/{{ val.max }}</span></td>
          <td>
            <span class="mini-bar"><span class="mini-fill" style="width:{{ pct }}%;background:{{ bc }};"></span></span>
            {{ pct }}%
          </td>
          <td style="color:var(--text2);max-width:280px;">{{ val.comment }}</td>
          <td style="text-align:center;">
            <div class="cb {{ 'checked' if passed else 'crossed' }}">
              {% if passed %}
              <svg viewBox="0 0 12 12" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="1.5,6 4.5,9 10.5,3"/>
              </svg>
              {% else %}
              <svg viewBox="0 0 12 12" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round">
                <line x1="2" y1="2" x2="10" y2="10"/><line x1="10" y1="2" x2="2" y2="10"/>
              </svg>
              {% endif %}
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% endif %}

    {% if r.grade.strengths or r.grade.improvements %}
    <div class="two-col">
      {% if r.grade.strengths %}
      <div class="list-box">
        <div class="list-box-title" style="color:var(--accent)">✓ Strengths</div>
        {% for s in r.grade.strengths %}
        <div class="list-item"><span class="list-dot" style="color:var(--accent)"></span>{{ s }}</div>
        {% endfor %}
      </div>
      {% endif %}
      {% if r.grade.improvements %}
      <div class="list-box">
        <div class="list-box-title" style="color:var(--warning)">↑ Areas to Improve</div>
        {% for imp in r.grade.improvements %}
        <div class="list-item"><span class="list-dot" style="color:var(--warning)"></span>{{ imp }}</div>
        {% endfor %}
      </div>
      {% endif %}
    </div>
    {% endif %}

    {% endif %}
  </div>
</div>
{% endfor %}
{% endif %}
</main>

<div id="toast">✓ Copied to clipboard!</div>

<script>
function copyMarks(idx, name, marks, grade) {
  const table = document.getElementById('rubric-' + idx);
  let rubricText = '';
  if (table) {
    table.querySelectorAll('tbody tr').forEach(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length >= 5) {
        const criterion = cells[0].innerText.trim();
        const score     = cells[1].innerText.trim();
        const comment   = cells[3].innerText.trim();
        const status    = cells[4].querySelector('.cb.checked') ? '✓' : '✗';
        rubricText += `  ${status} ${criterion}: ${score} — ${comment}\\n`;
      }
    });
  }
  const text =
    `Student: ${name}\\n` +
    `Marks:   ${marks}/100  |  Grade: ${grade}\\n\\n` +
    `Rubric Breakdown:\\n${rubricText}`;
  navigator.clipboard.writeText(text).then(() => {
    const t = document.getElementById('toast');
    t.style.opacity = '1';
    setTimeout(() => t.style.opacity = '0', 2500);
  });
}
</script>
</body>
</html>
"""
