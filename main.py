import os
import uuid
import io
import gc
from pathlib import Path
from fastapi import FastAPI, Request, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

app = FastAPI()


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "static" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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
            
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = OUTPUT_DIR / filename
        img.save(filepath, format=target_format)
        
        return {"preview_url": f"/static/output/{filename}", "filename": filename}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/delete/{filename}")
async def delete_image(filename: str):
    try:
        safe_filename = os.path.basename(filename)
        # Target the exact absolute path
        filepath = OUTPUT_DIR / safe_filename

        if not filepath.exists():
            return JSONResponse(status_code=404, content={"error": f"File '{safe_filename}' not found."})

        gc.collect()  # Release file locks
        os.remove(filepath)
        return {"message": "Deleted successfully"}

    except PermissionError:
        return JSONResponse(status_code=500, content={"error": "File is temporarily locked. Try again in a moment."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})