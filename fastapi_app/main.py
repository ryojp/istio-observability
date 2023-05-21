import logging
import os
import random
import time
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, Response, Request

PORT = int(os.environ.get("PORT", "8000"))
TARGET_ONE_ORIGIN = os.environ.get("TARGET_ONE_ORIGIN", "http://app-b.demo.svc.cluster.local")
TARGET_TWO_ORIGIN = os.environ.get("TARGET_TWO_ORIGIN", "http://app-c.demo.svc.cluster.local")

app = FastAPI()


# logger middleware
@app.middleware("http")
async def logger(req: Request, call_next):
    logging.info(f"{req.method} {req.url} {req.headers}")
    res = await call_next(req)
    return res


@app.get("/")
async def read_root():
    logging.debug("Hello World")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    logging.debug("items")
    return {"item_id": item_id, "q": q}


@app.get("/io_task")
async def io_task():
    time.sleep(0.01)
    logging.debug("io task")
    return "IO bound task finish!"


@app.get("/cpu_task")
async def cpu_task():
    for i in range(1000):
        n = i*i*i
    logging.debug("cpu task")
    return "CPU bound task finish!"


@app.get("/random_status")
async def random_status(response: Response):
    response.status_code = random.choice([200, 200, 300, 400, 500])
    logging.debug("random status")
    return {"path": "/random_status"}


@app.get("/random_sleep")
async def random_sleep(response: Response):
    logging.debug("random sleep")
    time.sleep(random.randint(0, 5))
    return {"path": "/random_sleep"}


@app.get("/sleep")
async def random_sleep(response: Response, t: Optional[float] = 1.0):
    logging.debug(f"sleeping {t} sec...")
    time.sleep(t)
    return {"path": "/sleep", "t": t}


@app.get("/error_test")
async def random_sleep(response: Response):
    logging.debug("got error!!!!")
    raise ValueError("value error")


@app.get("/chain")
async def chain(response: Response):

    async with httpx.AsyncClient() as client:
        await client.get(f"http://localhost:{PORT}/")
    async with httpx.AsyncClient() as client:
        await client.get(f"{TARGET_ONE_ORIGIN}/io_task")
    async with httpx.AsyncClient() as client:
        await client.get(f"{TARGET_TWO_ORIGIN}/cpu_task")
    logging.info("Chain Finished")
    return {"path": "/chain"}

if __name__ == "__main__":
    logging.info(f"Running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
