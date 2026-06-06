BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} — GradeAI</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0d0f14;
    --surface: #161922;
    --surface2: #1e2330;
    --border: #252a36;
    --border2: #2f3748;
    --accent: #6ee7b7;
    --accent2: #818cf8;
    --accent3: #f472b6;
    --text: #e2e8f0;
    --text2: #94a3b8;
    --muted: #4b5563;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
    --radius: 12px;
  }

  html, body { height: 100%; }

  body {
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  /* ---- NAV ---- */
  nav {
    position: sticky; top: 0; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 32px;
    background: rgba(13, 15, 20, 0.85);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(12px);
  }

  .nav-brand {
    display: flex; align-items: center; gap: 10px;
    text-decoration: none;
  }

  .nav-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, var(--accent2), var(--accent));
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px;
  }

  .nav-logo-text {
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    background: linear-gradient(90deg, var(--accent2), var(--accent));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .nav-right {
    display: flex; align-items: center; gap: 16px;
  }

  .nav-user {
    display: flex; align-items: center; gap: 10px;
    font-size: 14px; color: var(--text2);
  }

  .nav-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    border: 2px solid var(--border2);
    object-fit: cover;
  }

  .nav-avatar-placeholder {
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(135deg, var(--accent2), var(--accent));
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 600; color: #fff;
  }

  .btn-logout {
    padding: 7px 14px;
    border: 1px solid var(--border2);
    border-radius: 8px;
    background: transparent;
    color: var(--text2);
    font-size: 13px; font-family: 'DM Sans', sans-serif;
    cursor: pointer; text-decoration: none;
    transition: border-color 0.2s, color 0.2s;
  }
  .btn-logout:hover { border-color: var(--danger); color: var(--danger); }

  /* ---- MAIN ---- */
  main {
    flex: 1;
    max-width: 1100px;
    width: 100%;
    margin: 0 auto;
    padding: 40px 32px;
  }

  /* ---- BREADCRUMB ---- */
  .breadcrumb {
    display: flex; align-items: center; gap: 8px;
    margin-bottom: 28px;
    font-size: 13px; color: var(--text2);
  }
  .breadcrumb a { color: var(--text2); text-decoration: none; }
  .breadcrumb a:hover { color: var(--accent); }
  .breadcrumb-sep { color: var(--muted); }
  .breadcrumb-current { color: var(--text); }

  /* ---- PAGE HEADER ---- */
  .page-header { margin-bottom: 32px; }
  .page-header h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 32px; font-weight: 400;
    color: var(--text);
    margin-bottom: 6px;
  }
  .page-header p { color: var(--text2); font-size: 15px; }

  /* ---- CARDS ---- */
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    transition: border-color 0.2s, transform 0.2s;
  }
  .card:hover { border-color: var(--border2); }
  .card.clickable { cursor: pointer; }
  .card.clickable:hover { transform: translateY(-2px); border-color: var(--accent2); }
  .card a { text-decoration: none; color: inherit; display: block; }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }

  /* ---- BADGE ---- */
  .badge {
    display: inline-flex; align-items: center;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .badge-green { background: rgba(110, 231, 183, 0.12); color: var(--accent); border: 1px solid rgba(110,231,183,0.2); }
  .badge-blue  { background: rgba(129, 140, 248, 0.12); color: var(--accent2); border: 1px solid rgba(129,140,248,0.2); }
  .badge-pink  { background: rgba(244, 114, 182, 0.12); color: var(--accent3); border: 1px solid rgba(244,114,182,0.2); }
  .badge-red   { background: rgba(239, 68, 68, 0.12);  color: var(--danger);  border: 1px solid rgba(239,68,68,0.2); }
  .badge-warn  { background: rgba(245, 158, 11, 0.12); color: var(--warning); border: 1px solid rgba(245,158,11,0.2); }

  /* ---- EMPTY STATE ---- */
  .empty {
    text-align: center; padding: 64px 32px;
    color: var(--text2);
  }
  .empty-icon { font-size: 48px; margin-bottom: 16px; }
  .empty h3 { font-size: 18px; margin-bottom: 8px; color: var(--text); }
  .empty p  { font-size: 14px; color: var(--text2); }

  /* ---- UTILS ---- */
  .tag {
    display: inline-block; padding: 2px 8px;
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; font-size: 12px; color: var(--text2);
  }

  .divider { border: none; border-top: 1px solid var(--border); margin: 24px 0; }

  .flex { display: flex; }
  .items-center { align-items: center; }
  .justify-between { justify-content: space-between; }
  .gap-2 { gap: 8px; }
  .gap-3 { gap: 12px; }
  .mb-1 { margin-bottom: 4px; }
  .mb-2 { margin-bottom: 8px; }
  .mb-3 { margin-bottom: 16px; }
  .mt-auto { margin-top: auto; }

  .text-sm   { font-size: 13px; }
  .text-xs   { font-size: 12px; }
  .text-muted { color: var(--text2); }
  .text-accent { color: var(--accent); }
  .font-medium { font-weight: 500; }
  .font-serif  { font-family: 'DM Serif Display', serif; }

  /* ---- ALERT ---- */
  .alert {
    padding: 14px 18px; border-radius: var(--radius);
    margin-bottom: 24px; font-size: 14px;
    border: 1px solid;
  }
  .alert-error {
    background: rgba(239,68,68,0.08);
    border-color: rgba(239,68,68,0.25);
    color: #fca5a5;
  }

  /* Fade in */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .animate { animation: fadeUp 0.4s ease both; }
  .delay-1 { animation-delay: 0.05s; }
  .delay-2 { animation-delay: 0.10s; }
  .delay-3 { animation-delay: 0.15s; }
</style>
{% block extra_styles %}{% endblock %}
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
        <div class="nav-avatar-placeholder">{{ user.name[0] }}</div>
      {% endif %}
      <span>{{ user.name }}</span>
    </div>
    {% endif %}
    <a href="/logout" class="btn-logout">Sign out</a>
  </div>
</nav>

<main>
  {% if error %}
  <div class="alert alert-error">⚠️ {{ error }}</div>
  {% endif %}

  {% block content %}{% endblock %}
</main>

{% block scripts %}{% endblock %}
</body>
</html>
"""
