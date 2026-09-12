import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

import fitz
import main
from fastapi.testclient import TestClient
from main import app, extract_text_from_pdf

client = TestClient(app)


def create_test_pdf(text):
    """
    Creates a small PDF containing the given text.

    This helper function is used by multiple tests to create
    sample PDF files without repeating the same code.
    """

    # Create a new PDF document.
    pdf = fitz.open()

    # Add a new page to the PDF.
    page = pdf.new_page()

    # Add the test text to the page.
    page.insert_text((50, 50), text)

    # Convert the PDF into bytes so it can be used in the tests.
    contents = pdf.tobytes()

    # Close the PDF after creating it.
    pdf.close()

    return contents


def fake_ollama_response():
    """
    Returns a fake structured AI response for testing.

    A fake response is used so the tests do not need to
    run the Qwen3 model during testing.
    """

    return {
        "message": {
            "content": """
{
    "resume_score": 80,
    "ats_score": 75,
    "ats_feedback": "Test ATS feedback",
    "strengths": ["Test strength"],
    "weaknesses": ["Test weakness"],
    "missing_skills": ["Git"],
    "suggestions": ["Test suggestion"]
}
"""
        }
    }


def fake_ollama_response_with_jd():
    """
    Returns a fake structured AI response containing
    job-description analysis.

    This response is used when testing resume and
    job-description comparison.
    """

    return {
        "message": {
            "content": """
{
    "resume_score": 80,
    "ats_score": 75,
    "ats_feedback": "Test ATS feedback",
    "strengths": ["Test strength"],
    "weaknesses": ["Test weakness"],
    "missing_skills": ["Git"],
    "suggestions": ["Test suggestion"],
    "jd_match_score": 85,
    "matching_skills": ["Python", "FastAPI"],
    "jd_missing_skills": ["Docker"],
    "jd_analysis": "Test job description analysis"
}
"""
        }
    }


def test_home():
    """
    Tests the root endpoint of the FastAPI backend.

    It checks that the API returns a successful response
    and shows the expected message when the root endpoint
    is called.
    """

    # Send a GET request to the root endpoint.
    response = client.get("/")

    # Check that the request was successful.
    assert response.status_code == 200

    # Check that the expected message is returned.
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
    pdf_contents = create_test_pdf("Test resume content")

    # Extract text from the test PDF.
    text = extract_text_from_pdf(pdf_contents)

    # Check whether the expected text was extracted.
    assert "Test resume content" in text


def test_extract_text_from_multiple_page_pdf():
    """
    Tests PDF text extraction when the PDF contains
    multiple pages.

    The text from all pages should be extracted correctly.
    """

    # Create a new PDF document.
    pdf = fitz.open()

    # Add text to the first page.
    page1 = pdf.new_page()
    page1.insert_text((50, 50), "First page content")

    # Add text to the second page.
    page2 = pdf.new_page()
    page2.insert_text((50, 50), "Second page content")

    # Convert the PDF into bytes.
    pdf_contents = pdf.tobytes()

    # Close the PDF.
    pdf.close()

    # Extract text from the PDF.
    text = extract_text_from_pdf(pdf_contents)

    # Check that text from both pages was extracted.
    assert "First page content" in text
    assert "Second page content" in text


def test_upload_resume_without_job_description():
    """
    Tests that a resume can be uploaded without a job description.

    The job description is optional, so the request should be
    accepted even when no job description is provided.

    A fake AI response is used so the test does not need
    to run the Qwen3 model.
    """

    # Create a small PDF to use as the test resume.
    pdf_contents = create_test_pdf("Test resume content")

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = lambda *args, **kwargs: fake_ollama_response()

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

    # The request should be accepted successfully.
    assert response.status_code == 200

    # The job description should be empty.
    assert response.json()["job_description"] is None

    # Check the structured AI response.
    assert response.json()["analysis"]["resume_score"] == 80
    assert response.json()["analysis"]["ats_score"] == 75


def test_upload_resume_with_pasted_job_description():
    """
    Tests that a resume can be uploaded with a job description
    provided as text.

    The pasted job description should be received by the backend
    and included in the analysis.
    """

    # Create a small PDF to use as the test resume.
    pdf_contents = create_test_pdf(
        "Python React FastAPI resume"
    )

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = (
        lambda *args, **kwargs: fake_ollama_response_with_jd()
    )

    # Upload the resume and provide a pasted job description.
    response = client.post(
        "/upload-resume",
        data={
            "job_description": (
                "Looking for a Python developer with "
                "FastAPI and Docker experience."
            )
        },
        files={
            "file": (
                "test_resume.pdf",
                pdf_contents,
                "application/pdf"
            )
        }
    )

    # The request should be accepted successfully.
    assert response.status_code == 200

    # Check that the job description was received correctly.
    assert "Python developer" in response.json()["job_description"]

    # Check the JD analysis fields.
    assert response.json()["analysis"]["jd_match_score"] == 85
    assert "Python" in response.json()["analysis"]["matching_skills"]
    assert "Docker" in response.json()["analysis"]["jd_missing_skills"]


def test_upload_resume_with_job_description_pdf():
    """
    Tests that a resume and a job description PDF can be
    uploaded together successfully.

    The test creates two PDF files: one for the resume and
    one for the job description.

    It then checks whether the job description text is
    extracted correctly.
    """

    # Create a small PDF to use as the test resume.
    resume_contents = create_test_pdf(
        "Test resume content"
    )

    # Create a small PDF to use as the test job description.
    jd_contents = create_test_pdf(
        "Python Machine Learning FastAPI NLP"
    )

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = (
        lambda *args, **kwargs: fake_ollama_response_with_jd()
    )

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

    # Check that the job description text was extracted.
    assert "Python Machine Learning FastAPI NLP" in response.json()[
        "job_description"
    ]

    # Check that the JD match score was returned.
    assert response.json()["analysis"]["jd_match_score"] == 85


def test_response_contains_resume_filename():
    """
    Tests that the uploaded resume filename is included
    in the API response.
    """

    # Create a small test resume PDF.
    pdf_contents = create_test_pdf("Test resume content")

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = lambda *args, **kwargs: fake_ollama_response()

    # Upload the test resume.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "my_resume.pdf",
                pdf_contents,
                "application/pdf"
            )
        }
    )

    # Check that the request was successful.
    assert response.status_code == 200

    # Check that the correct filename was returned.
    assert response.json()["filename"] == "my_resume.pdf"


def test_response_contains_extracted_resume_text():
    """
    Tests that the text extracted from the resume PDF
    is included in the API response.
    """

    # Create a PDF containing sample resume text.
    pdf_contents = create_test_pdf(
        "Python Developer Test Resume"
    )

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = lambda *args, **kwargs: fake_ollama_response()

    # Upload the resume.
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

    # Check that the request was successful.
    assert response.status_code == 200

    # Check that the extracted resume text was returned.
    assert "Python Developer Test Resume" in response.json()["text"]


def test_analysis_contains_required_resume_fields():
    """
    Tests that the AI response contains all the main
    resume analysis fields used by the application.
    """

    # Create a small test resume PDF.
    pdf_contents = create_test_pdf("Test resume content")

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = lambda *args, **kwargs: fake_ollama_response()

    # Upload the resume.
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

    # Get the analysis from the API response.
    analysis = response.json()["analysis"]

    # Check that all required resume analysis fields exist.
    assert "resume_score" in analysis
    assert "ats_score" in analysis
    assert "ats_feedback" in analysis
    assert "strengths" in analysis
    assert "weaknesses" in analysis
    assert "missing_skills" in analysis
    assert "suggestions" in analysis


def test_analysis_contains_job_description_fields():
    """
    Tests that the AI response contains the additional
    fields required when a job description is provided.
    """

    # Create a small test resume PDF.
    pdf_contents = create_test_pdf(
        "Python FastAPI resume"
    )

    # Replace the AI model call with a fake response.
    main.ollama_client.chat = (
        lambda *args, **kwargs: fake_ollama_response_with_jd()
    )

    # Upload the resume with a job description.
    response = client.post(
        "/upload-resume",
        data={
            "job_description": (
                "Looking for Python and FastAPI skills."
            )
        },
        files={
            "file": (
                "test_resume.pdf",
                pdf_contents,
                "application/pdf"
            )
        }
    )

    # Get the analysis from the API response.
    analysis = response.json()["analysis"]

    # Check that all JD-related analysis fields exist.
    assert "jd_match_score" in analysis
    assert "matching_skills" in analysis
    assert "jd_missing_skills" in analysis
    assert "jd_analysis" in analysis

def test_upload_non_pdf_resume():
    """
    Tests that the backend rejects a resume file that is not a PDF.

    The application only supports PDF resumes, so uploading
    another file type should return a 400 error.
    """

    # Upload a fake text file instead of a PDF.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "resume.txt",
                b"This is not a PDF file.",
                "text/plain"
            )
        }
    )

    # The backend should reject the file.
    assert response.status_code == 400

    # Check that the error message explains the problem.
    assert response.json()["detail"] == "Only PDF resume files are supported."


def test_upload_empty_resume():
    """
    Tests that the backend rejects an empty resume file.

    An empty file cannot be analyzed, so the backend should
    return a clear error message.
    """

    # Upload an empty PDF file.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "empty_resume.pdf",
                b"",
                "application/pdf"
            )
        }
    )

    # The backend should reject the empty file.
    assert response.status_code == 400

    # Check that the correct error message is returned.
    assert response.json()["detail"] == "The uploaded resume file is empty."


def test_upload_invalid_pdf_resume():
    """
    Tests that the backend handles a corrupted or invalid PDF.

    The file has a PDF extension but does not contain valid PDF data.
    The backend should return a useful error instead of crashing.
    """

    # Create invalid PDF content.
    invalid_pdf = b"This is not a real PDF document."

    # Upload the invalid PDF.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "broken_resume.pdf",
                invalid_pdf,
                "application/pdf"
            )
        }
    )

    # The backend should reject the invalid PDF.
    assert response.status_code == 400

    # Check that a meaningful error message is returned.
    assert response.json()["detail"] == (
        "Unable to read the PDF. Please upload a valid PDF file."
    )


def test_upload_non_pdf_job_description():
    """
    Tests that the backend rejects a job description file
    that is not in PDF format.
    """

    # Create a valid resume PDF.
    resume_contents = create_test_pdf("Test resume content")

    # Upload a text file as the job description.
    response = client.post(
        "/upload-resume",
        files={
            "file": (
                "test_resume.pdf",
                resume_contents,
                "application/pdf"
            ),
            "job_description_file": (
                "job_description.txt",
                b"This is not a PDF file.",
                "text/plain"
            )
        }
    )

    # The backend should reject the JD file.
    assert response.status_code == 400

    # Check that the correct error message is returned.
    assert response.json()["detail"] == (
        "Only PDF job description files are supported."
    )


def test_ollama_connection_error():
    """
    Tests how the backend handles an Ollama connection failure.

    A fake error is raised instead of contacting the real
    Qwen3 model. The backend should return a 503 error.
    """

    # Create a valid test resume PDF.
    pdf_contents = create_test_pdf("Test resume content")

    # Simulate Ollama being unavailable.
    def fake_ollama_error(*args, **kwargs):
        raise Exception("Ollama is not running")

    main.ollama_client.chat = fake_ollama_error

    # Upload the resume.
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

    # The backend should return a service unavailable error.
    assert response.status_code == 503

    # Check that the user receives a useful error message.
    assert "Unable to connect to the local AI model" in (
        response.json()["detail"]
    )


def test_invalid_ai_json_response():
    """
    Tests how the backend handles an invalid AI response.

    The AI is expected to return valid JSON. If it returns
    invalid JSON, the backend should return a 502 error
    instead of crashing.
    """

    # Create a valid test resume PDF.
    pdf_contents = create_test_pdf("Test resume content")

    # Simulate an AI response that is not valid JSON.
    def fake_invalid_json(*args, **kwargs):
        return {
            "message": {
                "content": "This is not valid JSON."
            }
        }

    main.ollama_client.chat = fake_invalid_json

    # Upload the resume.
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

    # The backend should return a bad gateway error.
    assert response.status_code == 502

    # Check that the error message explains the problem.
    assert response.json()["detail"] == (
        "The AI model returned an invalid analysis response. Please try again."
    )