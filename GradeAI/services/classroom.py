from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
#  Service builders
# ──────────────────────────────────────────────

def get_classroom_service(credentials):
    return build("classroom", "v1", credentials=credentials)


def get_drive_service(credentials):
    return build("drive", "v3", credentials=credentials)


# ──────────────────────────────────────────────
#  Courses
# ──────────────────────────────────────────────

def get_courses(credentials):
    service = get_classroom_service(credentials)
    try:
        result = service.courses().list(courseStates=["ACTIVE"]).execute()
        return result.get("courses", [])
    except Exception as e:
        logger.error(f"Error fetching courses: {e}")
        raise


def get_course_info(credentials, course_id):
    service = get_classroom_service(credentials)
    try:
        return service.courses().get(id=course_id).execute()
    except Exception as e:
        logger.error(f"Error fetching course info for {course_id}: {e}")
        raise


# ──────────────────────────────────────────────
#  Coursework
# ──────────────────────────────────────────────

def get_coursework(credentials, course_id):
    service = get_classroom_service(credentials)
    try:
        result = service.courses().courseWork().list(courseId=course_id).execute()
        return result.get("courseWork", [])
    except Exception as e:
        logger.error(f"Error fetching coursework for {course_id}: {e}")
        raise


def get_work_info(credentials, course_id, work_id):
    service = get_classroom_service(credentials)
    try:
        return service.courses().courseWork().get(courseId=course_id, id=work_id).execute()
    except Exception as e:
        logger.error(f"Error fetching work info for {work_id}: {e}")
        raise


# ──────────────────────────────────────────────
#  Submissions
# ──────────────────────────────────────────────

def get_submissions(credentials, course_id, work_id):
    service = get_classroom_service(credentials)
    try:
        result = service.courses().courseWork().studentSubmissions().list(
            courseId=course_id,
            courseWorkId=work_id
        ).execute()
        return result.get("studentSubmissions", [])
    except Exception as e:
        logger.error(f"Error fetching submissions for work {work_id}: {e}")
        raise


# ──────────────────────────────────────────────
#  Student profiles
# ──────────────────────────────────────────────

def get_student_profile(credentials, user_id):
    service = get_classroom_service(credentials)
    try:
        profile = service.userProfiles().get(userId=user_id).execute()
        return profile.get("name", {}).get("fullName", "Unknown Student")
    except Exception as e:
        logger.warning(f"Could not fetch student profile for {user_id}: {e}")
        return "Unknown Student"


# ──────────────────────────────────────────────
#  Drive file download
# ──────────────────────────────────────────────

def download_drive_file(credentials, file_id):
    service = get_drive_service(credentials)
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh
    except Exception as e:
        logger.error(f"Error downloading Drive file {file_id}: {e}")
        raise


# ──────────────────────────────────────────────
#  Grade posting  ← FIXED
# ──────────────────────────────────────────────

def post_grade_to_classroom(credentials, course_id, work_id, submission_id, marks):
    """
    Push AI grade back to Google Classroom.

    Correct flow required by the API:
      1. PATCH studentSubmission with updateMask=draftGrade
      2. Call return_() to publish → this sets assignedGrade and notifies the student

    Setting assignedGrade directly (without return_) causes 403
    @ProjectPermissionDenied on unverified / testing-mode projects.
    """
    service = get_classroom_service(credentials)

    # ── Step 1: write draft grade ──────────────────────────────────────
    try:
        print(f"[CLASSROOM] Posting grade {marks} → "
              f"course={course_id}  work={work_id}  sub={submission_id}")

        patched = service.courses().courseWork().studentSubmissions().patch(
            courseId=course_id,
            courseWorkId=work_id,
            id=submission_id,
            updateMask="draftGrade",
            body={"draftGrade": float(marks)}
        ).execute()

        print(f"[CLASSROOM] ✓ draftGrade set → {patched.get('draftGrade')}")

    except Exception as e:
        print(f"[CLASSROOM] ✗ PATCH (draftGrade) failed: {type(e).__name__}: {e}")
        logger.error(f"Failed to patch draftGrade for submission {submission_id}: {e}")
        raise

    # ── Step 2: return submission (publishes grade to student) ─────────
    try:
        service.courses().courseWork().studentSubmissions().return_(
            courseId=course_id,
            courseWorkId=work_id,
            id=submission_id,
            body={}
        ).execute()

        print(f"[CLASSROOM] ✓ Submission returned — grade now visible to student")
        return True

    except Exception as e:
        print(f"[CLASSROOM] ✗ return_() failed: {type(e).__name__}: {e}")
        logger.error(f"Failed to return submission {submission_id}: {e}")
        raise