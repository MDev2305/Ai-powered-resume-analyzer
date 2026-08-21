import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

import fitz
import main
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


def test_upload_resume_without_job_description():
    """
    Tests that a resume can be uploaded without a job description.

    The job description is optional, so the request should be
    accepted even when no job description is provided.
    """

    # Create a small PDF to use as the test resume.
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 50), "Test resume content")

    pdf_contents = pdf.tobytes()
    pdf.close()

    # Replace the AI model call with a simple fake response.
    def fake_ollama_chat(*args, **kwargs):
        return {
            "message": {
                "content": "Test AI analysis"
            }
        }

    main.ollama.chat = fake_ollama_chat

    # Upload the resume without providing a job description.
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

    # The request should be accepted because the JD is optional.
    assert response.status_code == 200

    # The job description should be empty.
    assert response.json()["job_description"] is None

    # Check that the fake AI response was returned.
    assert response.json()["analysis"] == "Test AI analysis"


def test_upload_resume_with_job_description_pdf():
    """
    Tests that a resume and a job description PDF can be uploaded
    together successfully.

    The test creates two small PDF files: one for the resume and
    one for the job description. It then uploads both files and
    checks that the job description text is extracted correctly.

    A fake AI response is used so the test does not need to run
    the Qwen3 model during testing.
    """

    # Create a small PDF to use as the test resume.
    resume_pdf = fitz.open()
    resume_page = resume_pdf.new_page()
    resume_page.insert_text((50, 50), "Test resume content")

    resume_contents = resume_pdf.tobytes()
    resume_pdf.close()

    # Create a small PDF to use as the test job description.
    jd_pdf = fitz.open()
    jd_page = jd_pdf.new_page()
    jd_page.insert_text(
        (50, 50),
        "Python Machine Learning FastAPI NLP"
    )

    jd_contents = jd_pdf.tobytes()
    jd_pdf.close()

    # Replace the AI model call with a simple fake response.
    def fake_ollama_chat(*args, **kwargs):
        return {
            "message": {
                "content": "Test AI analysis"
            }
        }

    main.ollama.chat = fake_ollama_chat

    # Upload both the resume and the job description PDF.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "test_resume.pdf",
                resume_contents,
                "application/pdf"
            ),
            "job_description_file": (
                "test_job_description.pdf",
                jd_contents,
                "application/pdf"
            )
        }
    )

    # The request should be accepted successfully.
    assert response.status_code == 200

    # Check that the job description text was extracted from the PDF.
    assert "Python Machine Learning FastAPI NLP" in response.json()[
        "job_description"
    ]

    # Check that the fake AI response was returned.
    assert response.json()["analysis"] == "Test AI analysis"