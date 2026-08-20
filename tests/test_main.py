import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

import fitz
from fastapi.testclient import TestClient
from main import app, extract_text_from_pdf

client = TestClient(app)


def test_home():
    """
    Tests the root endpoint of the FastAPI backend.

    It checks that the API returns a successful response
    and shows the expected message when the root endpoint is called.
    """
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Resume Analyzer Backend is running!"
    }


def test_extract_text_from_pdf():
    """
    Tests the PDF text extraction function.

    A small test PDF is created with sample resume text.
    The function then extracts the text from the PDF,
    and the test checks whether the expected text was extracted.
    """
    
    # Create a small PDF for testing.
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 50), "Test resume content")

    pdf_contents = pdf.tobytes()
    pdf.close()

    # Extract text from the test PDF.
    text = extract_text_from_pdf(pdf_contents)

    assert "Test resume content" in text


def test_upload_resume_requires_job_description():
    """
    Tests that a job description is required when uploading a resume.

    The API should return an error if a resume is uploaded
    without providing a job description.
    """
    # Create a small test PDF.
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 50), "Test resume content")

    pdf_contents = pdf.tobytes()
    pdf.close()

    # Send the resume without a job description.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "test_resume.pdf",
                pdf_contents,
                "application/pdf"
            )
        }
    )

    # The API should reject the request because the job description is missing.
    assert response.status_code == 422