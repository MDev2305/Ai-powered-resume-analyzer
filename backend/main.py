from fastapi import FastAPI, UploadFile, File
import fitz

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

    return {
        "filename": file.filename,
        "text": text
    }