import io
import base64
from pathlib import Path
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/convert/")
async def convert_image(file: UploadFile = File(...), format: str = Form(...)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        target_format = format.upper()
        ext = target_format.lower()
        
        if target_format in ["JPG", "JPEG"]:
            img = img.convert("RGB")
            target_format = "JPEG"
            ext = "jpg"
        
        # Process image purely in memory (no disk writing)
        buffer = io.BytesIO()
        img.save(buffer, format=target_format)
        buffer.seek(0)
        
        # Convert to base64 data URL
        base64_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
        mime_type = "jpeg" if ext == "jpg" else ext
        data_url = f"data:image/{mime_type};base64,{base64_img}"
        
        return {"preview_url": data_url, "filename": f"converted.{ext}"}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/delete/{filename}")
async def delete_image(filename: str):
    # No files on disk to remove; simply acknowledge to let frontend reset UI
    return {"message": "Deleted successfully"}