import io
import logging
import PyPDF2
from services.classroom import download_drive_file

logger = logging.getLogger(__name__)


def extract_text_from_file(credentials, file_id, mime_type=None):
    """
    Download a Drive file and extract its text content.
    Supports: PDF, plain text, Google Docs exports.
    """
    fh = download_drive_file(credentials, file_id)

    # Try PDF first
    try:
        reader = PyPDF2.PdfReader(fh)
        if len(reader.pages) > 0:
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            if text.strip():
                logger.info(f"Extracted {len(text)} chars from PDF (file_id={file_id})")
                return text.strip()
    except Exception:
        fh.seek(0)

    # Fallback: plain text / UTF-8
    try:
        fh.seek(0)
        text = fh.read().decode("utf-8", errors="ignore")
        if text.strip():
            logger.info(f"Extracted {len(text)} chars as plain text (file_id={file_id})")
            return text.strip()
    except Exception as e:
        logger.error(f"Could not extract text from file {file_id}: {e}")

    return None


def get_submission_text(credentials, submission):
    """
    Walk all attachments in a submission and return combined text.
    Returns (text, file_names) tuple.
    """
    attachments = submission.get("assignmentSubmission", {}).get("attachments", [])
    all_text = []
    file_names = []

    for attachment in attachments:
        if "driveFile" in attachment:
            drive_file = attachment["driveFile"]
            file_id = drive_file["id"]
            title = drive_file.get("title", "Unnamed File")
            file_names.append(title)

            text = extract_text_from_file(credentials, file_id)
            if text:
                all_text.append(f"[File: {title}]\n{text}")
            else:
                logger.warning(f"No text extracted from {title} ({file_id})")

    combined = "\n\n".join(all_text)
    return combined or None, file_names
