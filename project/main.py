from fastapi import Body, FastAPI, Request, WebSocket
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from celery.result import AsyncResult
from worker import create_task, get_product_recommendation
import asyncio
import websockets

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")



@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("home.html", context={"request": request})


@app.post("/tasks", status_code=201)
def run_task(payload = Body(...)):
    task_type = payload["type"]
    task = create_task.delay(int(task_type))
    return JSONResponse({"task_id": task.id})


@app.get("/tasks/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)


@app.get("/product/recommendations/{product_id}")
def get_product_recommendations(product_id: int):
    task = get_product_recommendation.delay(product_id)
    return JSONResponse({"task_id": task.id})


@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()

    # Get the task result asynchronously
    result = AsyncResult(task_id, app=get_product_recommendation)

    while True:
        if result.ready():
            break
        await asyncio.sleep(1)

    # Task is ready, send the final result
    if result.successful():
        result = {
            "status": result.state,
            "result": result.result
        }
        await websocket.send_text(str(result))
        await websocket.close()
    else:
        await websocket.send_text(result.state)