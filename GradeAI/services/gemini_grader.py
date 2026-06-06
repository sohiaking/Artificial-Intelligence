import json
import logging
import re
import requests
from flask import current_app

logger = logging.getLogger(__name__)


def grade_submission(answer_text, assignment_title="", assignment_description=""):
    api_key = current_app.config["GEMINI_API_KEY"]
    model_name = current_app.config["GEMINI_MODEL"]

    print(f"[GEMINI] Using model: {model_name}")
    print(f"[GEMINI] Key prefix: {api_key[:10]}")
    print(f"[GEMINI] Text length: {len(answer_text)}")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )

    prompt = f"""You are an expert AI teacher and academic evaluator.

Assignment: {assignment_title or "General Assignment"}
{f"Description: {assignment_description}" if assignment_description else ""}

Student's Answer:
---
{answer_text[:8000]}
---

Evaluate the student's answer and respond ONLY with a valid JSON object.
No markdown, no backticks, no explanation — raw JSON only.

Use this exact structure:
{{
  "marks": <integer 0-100>,
  "grade_letter": "<A+|A|B+|B|C+|C|D|F>",
  "rubric": {{
    "content_accuracy":    {{ "score": <0-30>, "max": 30, "comment": "<brief>" }},
    "depth_of_analysis":   {{ "score": <0-25>, "max": 25, "comment": "<brief>" }},
    "structure_clarity":   {{ "score": <0-20>, "max": 20, "comment": "<brief>" }},
    "language_expression": {{ "score": <0-15>, "max": 15, "comment": "<brief>" }},
    "originality":         {{ "score": <0-10>, "max": 10, "comment": "<brief>" }}
  }},
  "strengths":        ["<strength 1>", "<strength 2>"],
  "improvements":     ["<area 1>", "<area 2>"],
  "overall_feedback": "<2-3 sentence constructive comment>",
  "plagiarism_flag":  <true|false>
}}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 8000
        }
    }

    try:
        import re as _re
        import time

        # Parse retry delay from error message if present
        def _parse_retry_seconds(msg):
            match = _re.search(r'retry in ([\d.]+)s', str(msg))
            return float(match.group(1)) if match else 15

        # Try 2.5-flash first, fall back to 1.5-flash on quota/overload
        models_to_try = [model_name, "gemini-2.5-flash"]
        resp = None

        for attempt_model in models_to_try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{attempt_model}:generateContent?key={api_key}"
            )
            for attempt in range(3):
                print(f"[GEMINI] Trying {attempt_model} attempt {attempt + 1}")
                resp = requests.post(url, json=payload, timeout=60)
                print(f"[GEMINI] Status: {resp.status_code}")
                if resp.status_code == 200:
                    break
                elif resp.status_code in (429, 503):
                    wait = _parse_retry_seconds(resp.text) + 2
                    print(f"[GEMINI] Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                else:
                    break
            if resp and resp.status_code == 200:
                break

        if resp.status_code != 200:
            error_msg = resp.json().get("error", {}).get("message", resp.text)
            raise RuntimeError(f"Gemini API error {resp.status_code}: {error_msg}")

        data = resp.json()
        print(f"[GEMINI] Response keys: {list(data.keys())}")

        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"[GEMINI] Raw response (first 200 chars): {raw[:200]}")

        # Strip accidental markdown fences
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

        result = json.loads(raw)
        print(f"[GEMINI] Parsed marks: {result.get('marks')}")

        if "grade_letter" not in result:
            result["grade_letter"] = marks_to_grade(result.get("marks", 0))

        return result

    except json.JSONDecodeError as e:
        print(f"[GEMINI] JSON parse error: {e}")
        print(f"[GEMINI] Raw was: {raw[:500]}")
        return {
            "marks": 0,
            "grade_letter": "N/A",
            "rubric": {},
            "strengths": [],
            "improvements": [],
            "overall_feedback": f"Could not parse response: {raw[:300]}",
            "plagiarism_flag": False,
        }

    except Exception as e:
        print(f"[GEMINI] EXCEPTION TYPE: {type(e).__name__}")
        print(f"[GEMINI] EXCEPTION MSG:  {str(e)}")
        import traceback
        traceback.print_exc()
        raise RuntimeError(str(e))


def marks_to_grade(marks):
    if marks >= 95: return "A+"
    if marks >= 85: return "A"
    if marks >= 75: return "B+"
    if marks >= 65: return "B"
    if marks >= 55: return "C+"
    if marks >= 45: return "C"
    if marks >= 35: return "D"
    return "F"
