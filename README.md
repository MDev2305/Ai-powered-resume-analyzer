# AI-Powered Resume Analyzer

## Brief Overview

An AI-based application that analyzes resumes and provides feedback using Qwen3 through Ollama. It can also compare a resume with a job description to evaluate how well the candidate matches the role.

## Key Functionality

- Upload a resume in PDF format
- Extract text from the resume
- Optionally paste or upload a job description
- Generate an overall resume score
- Assess ATS compatibility
- Identify strengths, weaknesses, and missing skills
- Compare the resume with a job description
- Provide suggestions for improvement

## Technologies Used

- Python
- FastAPI
- PyMuPDF
- Ollama
- Qwen3 8B
- Pytest

## Project Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r backend/requirements.txt

4. Make sure Ollama is installed and running.
5. Download the Qwen3 model:
  ollama pull qwen3:8b

## How to Run

Start the FastAPI server:
uvicorn backend.main:app --reload

Open the API documentation:
http://127.0.0.1:8000/docs

## How to Use
1. Open POST /upload-resume.
2. Click Try it out.
3. Upload a resume PDF.
4. Optionally paste a job description or upload a job description PDF.
5. Click Execute.
6. View the generated resume analysis.

## Testing
Run:
 python -m pytest