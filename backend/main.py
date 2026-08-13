from fastapi import FastAPI, UploadFile, File
import fitz
import ollama

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Resume Analyzer Backend is running!"}


@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    contents = await file.read()

    pdf = fitz.open(stream=contents, filetype="pdf")

    text = ""

    for page in pdf:
        text += page.get_text()

    pdf.close()

    response = ollama.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": f"""
    Analyze this resume and provide:
    1. Resume score out of 100
    2. Strengths
    3. Weaknesses
    4. Missing skills
    5. Suggestions for improvement

    Resume:
    {text}
    """
            }
        ]
    )

    analysis = response["message"]["content"]

    return {
        "filename": file.filename,
        "text": text,
        "analysis": analysis
    }