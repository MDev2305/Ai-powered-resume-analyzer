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
    Verifies that the API returns a successful response
    and the expected message when the root endpoint is called.
    """
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Resume Analyzer Backend is running!"
    }


def test_extract_text_from_pdf():
    """
    Tests the PDF text extraction function.

    Creates a small test PDF, extracts its text,
    and verifies that the expected text is present.
    """
    # Create a temporary PDF for testing.
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((50, 50), "Test resume content")

    pdf_contents = pdf.tobytes()
    pdf.close()

    # Extract text from the test PDF.
    text = extract_text_from_pdf(pdf_contents)

    assert "Test resume content" in text