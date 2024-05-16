from fastapi import Body, FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import asyncio
import websockets

from fastapi import FastAPI, File, UploadFile
import shutil
from pathlib import Path

from routers import tesserract

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads/ocr", StaticFiles(directory="uploads/ocr"), name="uploads")
templates = Jinja2Templates(directory="templates")

app.include_router(tesserract.router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", context={"request": request})
