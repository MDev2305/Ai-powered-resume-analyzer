from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import fitz
import ollama
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    """
    Checks whether the Resume Analyzer backend is running.

    Returns a simple message to confirm that the API is working.
    """
    return {"message": "Resume Analyzer Backend is running!"}


def extract_text_from_pdf(contents):
    """
    Extracts text from an uploaded PDF.

    The function goes through each page of the PDF and
    combines all the extracted text into one string.

    Args:
        contents: The uploaded PDF file contents.

    Returns:
        The complete text extracted from the PDF.

    Raises:
        HTTPException: If the PDF cannot be opened or contains no text.
    """
    try:
        pdf = fitz.open(stream=contents, filetype="pdf")

        text = ""

        # Go through each page and collect its text.
        for page in pdf:
            text += page.get_text()

        pdf.close()

        # Check whether the PDF contains extractable text.
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="The PDF does not contain any extractable text."
            )

        return text

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read the PDF. Please upload a valid PDF file."
        )


@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_description: str | None = Form(None),
    job_description_file: UploadFile | None = File(None)
):
    """
    Uploads a resume and generates an AI-based analysis.

    The function extracts text from the uploaded resume and
    sends it to Qwen3 through Ollama.

    The job description is optional. The user can either
    paste the job description as text or upload it as a PDF.

    If a job description is provided, the AI compares the
    resume with the job description and identifies matching
    and missing skills.

    The analysis also includes an ATS compatibility assessment,
    resume strengths, weaknesses, and suggestions for improvement.

    Args:
        file: The resume PDF uploaded by the user.
        job_description: An optional job description pasted by the user.
        job_description_file: An optional job description uploaded as a PDF.

    Returns:
        The resume filename, extracted resume text, job description,
        and AI-generated analysis.
    """

    # Make sure a resume file was uploaded.
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please upload a resume PDF."
        )

    # Make sure the uploaded resume is a PDF.
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported."
        )

    # Read the uploaded resume PDF.
    contents = await file.read()

    # Make sure the uploaded file is not empty.
    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded resume file is empty."
        )

    # Extract text from the resume.
    text = extract_text_from_pdf(contents)

    # Start with the pasted job description, if one was provided.
    final_job_description = job_description

    # If a JD PDF was uploaded, extract its text.
    if job_description_file:
        # Make sure the uploaded job description is a PDF.
        if not job_description_file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only PDF job description files are supported."
            )

        jd_contents = await job_description_file.read()

        if not jd_contents:
            raise HTTPException(
                status_code=400,
                detail="The uploaded job description file is empty."
            )

        final_job_description = extract_text_from_pdf(jd_contents)

    # Ask the AI to return the analysis in a fixed JSON structure.
    analysis_request = f"""
Analyze this resume carefully and return the result ONLY as valid JSON.

Use exactly this structure:

{{
    "resume_score": 0,
    "ats_score": 0,
    "ats_feedback": "",
    "strengths": [],
    "weaknesses": [],
    "missing_skills": [],
    "suggestions": []
}}

Rules:

- resume_score must be a number from 0 to 100.
- ats_score must be a number from 0 to 100.

- ats_feedback must provide a detailed explanation of the ATS compatibility.
  Discuss:
  - resume structure
  - section organization
  - keyword usage
  - readability
  - formatting
  - possible ATS issues

- strengths must contain 4 to 6 detailed points.
  Each point should explain WHY the resume has that strength.
  Mention specific evidence from the resume whenever possible.

- weaknesses must contain 3 to 5 detailed points.
  Each point should explain the problem and why it may affect the resume.

- missing_skills must contain important skills or keywords that are
  missing or insufficiently represented in the resume.

- suggestions must contain 4 to 6 detailed and actionable suggestions.
  Explain what the candidate should improve and how.

- Do not give generic one-line answers.
- Use information from the actual resume.
- Do not invent skills or experience that are not present.
- Do not add Markdown.
- Do not add explanations outside the JSON.
"""

    # Add job comparison only when a job description is provided.
    if final_job_description:
        analysis_request += f"""
Also compare the resume with the following job description.

Add these fields to the JSON:

"jd_match_score": 0,
"matching_skills": [],
"jd_missing_skills": [],
"jd_analysis": ""

Rules:

- jd_match_score must be a number from 0 to 100.

- matching_skills must contain the skills and requirements
  that are present in both the resume and job description.
  Explain the relevance of the matches.

- jd_missing_skills must contain important skills or requirements
  from the job description that are missing from the resume.

- jd_analysis must provide a detailed explanation of how well
  the resume matches the job description.

- Mention specific technologies, skills, and requirements
  from the job description when explaining the match.

Job Description:
{final_job_description}
"""

    # Add the resume text to the AI prompt.
    analysis_request += f"""

Resume:
{text}
"""

    try:
        # Send the resume and analysis instructions to Qwen3.
        response = ollama.chat(
            model="qwen3:8b",
            messages=[
                {
                    "role": "user",
                    "content": analysis_request
                }
            ]
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to the local AI model. Please make sure Ollama is running and Qwen3:8b is available."
        )

    # Convert the AI's JSON response into Python data.
    try:
        # Convert the AI's JSON response into Python data.
        analysis = json.loads(response["message"]["content"])

    except (json.JSONDecodeError, KeyError, TypeError):
        raise HTTPException(
            status_code=502,
            detail="The AI model returned an invalid analysis response. Please try again."
        )

    return {
        "filename": file.filename,
        "text": text,
        "job_description": final_job_description,
        "analysis": analysis
    }