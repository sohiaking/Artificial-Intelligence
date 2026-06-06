<div align="center">

<img src="https://img.shields.io/badge/-GradeAI-4f46e5?style=for-the-badge&logo=google-classroom&logoColor=white" height="40"/>

**AI-powered assignment grading system** that fetches student submissions from Google Classroom,
grades them using the Gemini API, and automatically pushes results back —
complete with rubric breakdowns, strengths, and improvement feedback.

<br/>

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=flat-square&logo=flask&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![Classroom](https://img.shields.io/badge/Google_Classroom_API-v1-34A853?style=flat-square&logo=google-classroom&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)

</div>

---

## <img src="https://img.shields.io/badge/-Features-6366f1?style=flat-square&logoColor=white" height="22"/>

| | Feature | Description |
|---|---|---|
| <img src="https://img.shields.io/badge/-Auth-4285F4?style=flat-square&logo=google&logoColor=white" height="18"/> | **Google Classroom Integration** | OAuth 2.0 login, fetches courses, assignments, and student submissions automatically |
| <img src="https://img.shields.io/badge/-AI-8B5CF6?style=flat-square&logo=google&logoColor=white" height="18"/> | **AI Grading via Gemini** | Each submission is graded with detailed rubric scoring, overall feedback, strengths, and areas to improve |
| <img src="https://img.shields.io/badge/-Sync-22c55e?style=flat-square&logo=checkmarx&logoColor=white" height="18"/> | **Automatic Grade Push** | Grades are posted back to Google Classroom as draft grades and returned to students |
| <img src="https://img.shields.io/badge/-Alert-ef4444?style=flat-square&logo=authelia&logoColor=white" height="18"/> | **Plagiarism Flagging** | Gemini flags suspicious submissions automatically |
| <img src="https://img.shields.io/badge/-UI-f59e0b?style=flat-square&logo=databricks&logoColor=white" height="18"/> | **Rich Grading Dashboard** | Visual score rings, rubric tables, stat cards, and per-student feedback cards |
| <img src="https://img.shields.io/badge/-Docs-64748b?style=flat-square&logo=files&logoColor=white" height="18"/> | **PDF & Text Extraction** | Reads student-submitted PDFs and Google Docs via Drive API |
| <img src="https://img.shields.io/badge/-Security-0ea5e9?style=flat-square&logo=letsencrypt&logoColor=white" height="18"/> | **Session-based Auth** | Secure OAuth flow with token refresh support |

---

## <img src="https://img.shields.io/badge/-Project_Structure-6366f1?style=flat-square" height="22"/>

```
ai_grading_system/
├── app.py                  # Flask app factory & entry point
├── config.py               # All configuration & OAuth scopes
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── client_secret.json      # Google OAuth credentials (not committed)
├── services/
│   ├── google_auth.py      # OAuth flow helpers & credential management
│   ├── classroom.py        # Classroom & Drive API calls (read + write grades)
│   ├── file_extractor.py   # PDF / Google Docs text extraction
│   └── gemini_grader.py    # Gemini AI grading logic
├── routes/
│   ├── auth.py             # Login / OAuth callback / logout
│   ├── dashboard.py        # Courses & assignments listing pages
│   └── grading.py          # AI grading results page & grade posting
└── templates/
    └── base.py             # Shared HTML layout
```

---

## <img src="https://img.shields.io/badge/-Setup_&_Installation-6366f1?style=flat-square" height="22"/>

### ![step](https://img.shields.io/badge/1-Clone_the_Repository-3b82f6?style=flat-square)

```bash
git clone https://github.com/sohiaking/gradeai.git
cd gradeai
```

### ![step](https://img.shields.io/badge/2-Create_a_Virtual_Environment-3b82f6?style=flat-square)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### ![step](https://img.shields.io/badge/3-Install_Dependencies-3b82f6?style=flat-square)

```bash
pip install -r requirements.txt
```

### ![step](https://img.shields.io/badge/4-Configure_Environment_Variables-3b82f6?style=flat-square)

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
FLASK_SECRET_KEY=your-random-secret-key
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLIENT_SECRET_FILE=client_secret.json
OAUTHLIB_INSECURE_TRANSPORT=1   # development only — remove in production
```

### ![step](https://img.shields.io/badge/5-Set_Up_Google_Cloud_Project-3b82f6?style=flat-square)

Follow these steps carefully — skipping any will cause `403 ProjectPermissionDenied` errors:

#### a) Create a Project & Enable APIs
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (or select an existing one)
3. Navigate to **APIs & Services → Library**
4. Enable both:
   - **Google Classroom API**
   - **Google Drive API**

#### b) Configure OAuth Consent Screen
1. Go to **APIs & Services → OAuth consent screen**
2. Choose **External** user type → click Create
3. Fill in app name, support email, developer email
4. On the **Scopes** step, add all scopes listed in the [Required Scopes](#required-oauth-scopes) section below
5. Add your teacher Google account under **Test users**
6. **Important:** Click **"Publish App"** to move from Testing → Production, otherwise grade writes will be blocked

#### c) Create OAuth 2.0 Credentials
1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth client ID**
3. Application type: **Web application**
4. Add to **Authorized redirect URIs**:
   ```
   http://127.0.0.1:5000/callback
   ```
5. Download the JSON file and save it as `client_secret.json` in the project root

### ![step](https://img.shields.io/badge/6-Run_the_App-3b82f6?style=flat-square)

```bash
python app.py
```

Visit `http://127.0.0.1:5000`

---

## <img src="https://img.shields.io/badge/-Required_OAuth_Scopes-6366f1?style=flat-square" height="22"/> <a name="required-oauth-scopes"></a>

These must be added to your OAuth consent screen **and** your `config.py`:

| Scope | Purpose |
|---|---|
| `openid` | Authentication |
| `userinfo.email` | User email |
| `userinfo.profile` | User profile & name |
| `classroom.courses.readonly` | List courses |
| `classroom.coursework.students` | ![critical](https://img.shields.io/badge/CRITICAL-Read_%26_write_grades-ef4444?style=flat-square) |
| `classroom.coursework.me` | Access own coursework |
| `classroom.student-submissions.students.readonly` | Read submissions |
| `classroom.rosters` | Read student roster |
| `drive.readonly` | Download submitted files |

```python
# config.py
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.student-submissions.students.readonly",
    "https://www.googleapis.com/auth/classroom.rosters",
    "https://www.googleapis.com/auth/drive.readonly",
]
```

---

## <img src="https://img.shields.io/badge/-How_Grading_Works-6366f1?style=flat-square" height="22"/>

```
Student submits assignment
        |
        v
GradeAI fetches submission via Classroom API
        |
        v
File content extracted (PDF -> text, Google Doc -> text)
        |
        v
Gemini AI grades the submission:
  [+] Overall marks (0-100)
  [+] Grade letter (A+, A, B, C, D, F)
  [+] Per-criterion rubric scores
  [+] Overall feedback paragraph
  [+] Strengths list
  [+] Areas to improve list
  [+] Plagiarism flag (if detected)
        |
        v
Grade pushed back to Classroom:
  Step 1 -> PATCH submission with draftGrade
  Step 2 -> return_() publishes grade to student
        |
        v
Results displayed on grading dashboard
```

---

## <img src="https://img.shields.io/badge/-Usage-6366f1?style=flat-square" height="22"/>

| Step | Action |
|---|---|
| ![1](https://img.shields.io/badge/1-Login-4285F4?style=flat-square&logo=google&logoColor=white) | Click "Sign in with Google" using your teacher account |
| ![2](https://img.shields.io/badge/2-Select_Course-34A853?style=flat-square&logo=google-classroom&logoColor=white) | Browse your active Google Classroom courses |
| ![3](https://img.shields.io/badge/3-Select_Assignment-f59e0b?style=flat-square) | Choose an assignment to grade |
| ![4](https://img.shields.io/badge/4-Grade_with_AI-8B5CF6?style=flat-square&logo=google&logoColor=white) | GradeAI fetches, grades, pushes, and displays results automatically |

---

## <img src="https://img.shields.io/badge/-Tech_Stack-6366f1?style=flat-square" height="22"/>

| Layer | Technology |
|---|---|
| ![backend](https://img.shields.io/badge/Backend-3776AB?style=flat-square&logo=python&logoColor=white) | Python 3.11+, Flask |
| ![ai](https://img.shields.io/badge/AI_Grading-4285F4?style=flat-square&logo=google&logoColor=white) | Google Gemini 2.5 Flash API |
| ![api](https://img.shields.io/badge/Google_APIs-34A853?style=flat-square&logo=google-classroom&logoColor=white) | Classroom API v1, Drive API v3 |
| ![auth](https://img.shields.io/badge/Auth-EA4335?style=flat-square&logo=google&logoColor=white) | OAuth 2.0 via `google-auth-oauthlib` |
| ![pdf](https://img.shields.io/badge/PDF-64748b?style=flat-square&logo=adobeacrobatreader&logoColor=white) | PyMuPDF / pdfplumber |
| ![frontend](https://img.shields.io/badge/Frontend-f59e0b?style=flat-square&logo=html5&logoColor=white) | Jinja2 templates, vanilla CSS & JS |

---

## <img src="https://img.shields.io/badge/-Requirements-6366f1?style=flat-square" height="22"/>

```
flask
google-auth
google-auth-oauthlib
google-api-python-client
requests
pymupdf
python-dotenv
```

---

## <img src="https://img.shields.io/badge/-Troubleshooting-ef4444?style=flat-square" height="22"/>

### ![err](https://img.shields.io/badge/403-ProjectPermissionDenied_when_posting_grades-ef4444?style=flat-square)

This is the most common issue. Work through this checklist in order:

- [ ] Google Classroom API is **Enabled** in Cloud Console
- [ ] `classroom.coursework.students` scope is added to the **OAuth consent screen** (not just `config.py`)
- [ ] Your teacher account is listed under **Test users** (if app is in Testing mode)
- [ ] OAuth app is **Published** (In Production) — Testing mode restricts write operations
- [ ] You cleared your session and **re-authenticated** after making any of the above changes

### ![err](https://img.shields.io/badge/Issue-Grades_not_appearing_in_Classroom-f59e0b?style=flat-square)

The grade posting flow requires two API calls — `PATCH draftGrade` then `return_()`.
If either fails, check the terminal logs for `[CLASSROOM] ✗` messages.

### ![err](https://img.shields.io/badge/Issue-No_readable_content_found-f59e0b?style=flat-square)

The student's submission format isn't supported. Currently supported: PDF files and Google Docs.
Direct text entries and other file types may need additional extractors in `file_extractor.py`.

### ![err](https://img.shields.io/badge/Issue-Token_or_scope_errors-f59e0b?style=flat-square)

Always clear your session after adding new scopes, then log in again:
```
http://127.0.0.1:5000/clear
```

---

## <img src="https://img.shields.io/badge/-Security_Notes-0ea5e9?style=flat-square&logo=letsencrypt&logoColor=white" height="22"/>

- **Never commit** `client_secret.json` or `.env` to version control — add both to `.gitignore`
- Set `OAUTHLIB_INSECURE_TRANSPORT=1` only in development; remove it in production
- Use a strong random value for `FLASK_SECRET_KEY` in production
- In production, serve over **HTTPS** and use a proper WSGI server (gunicorn, uWSGI)

---

## <img src="https://img.shields.io/badge/-License-22c55e?style=flat-square" height="22"/>

MIT License — see [LICENSE](LICENSE) for details.

---

## <img src="https://img.shields.io/badge/-Acknowledgements-6366f1?style=flat-square" height="22"/>

[![Classroom](https://img.shields.io/badge/Google_Classroom_API-Docs-34A853?style=flat-square&logo=google-classroom&logoColor=white)](https://developers.google.com/classroom)
[![Gemini](https://img.shields.io/badge/Google_Gemini_API-Docs-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![Flask](https://img.shields.io/badge/Flask-Docs-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
