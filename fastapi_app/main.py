import logging
import os
import random
import time
from typing import Optional

import httpx
import uvicorn
from fastapi import FastAPI, Response, Request


PORT = int(os.environ.get("PORT", "8000"))
TARGET_ONE_ORIGIN = os.environ.get(
    "TARGET_ONE_ORIGIN", "http://app-b.demo.svc.cluster.local"
)
TARGET_TWO_ORIGIN = os.environ.get(
    "TARGET_TWO_ORIGIN", "http://app-c.demo.svc.cluster.local"
)

app = FastAPI()


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def getForwardHeaders(request: Request) -> dict[str, str]:
    """Returns a header dict that Istio needs for tracing"""

    headers_to_propagate = [
        "x-request-id",
        "x-b3-traceid",
        "x-b3-spanid",
        "x-b3-parentspanid",
        "x-b3-sampled",
        "x-b3-flags",
    ]

    headers = {}

    for ihdr in headers_to_propagate:
        val = request.headers.get(ihdr)
        if val is not None:
            headers[ihdr] = val

    return headers


# logger middleware
@app.middleware("http")
async def logger(req: Request, call_next):
    log.info(f"{req.method} {req.url} {req.headers}")
    res = await call_next(req)
    return res


@app.get("/")
async def read_root():
    log.debug("Hello World")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    log.debug("items")
    return {"item_id": item_id, "q": q}


@app.get("/io_task")
async def io_task():
    time.sleep(0.1)
    log.debug("io task")
    return "IO bound task finish!"


@app.get("/cpu_task")
async def cpu_task():
    for i in range(1000):
        n = i * i * i
    log.debug("cpu task")
    return "CPU bound task finish!"


@app.get("/random_status")
async def random_status(res: Response):
    res.status_code = random.choice([200, 200, 300, 400, 500])
    log.debug("random status")
    return {"path": "/random_status"}


@app.get("/random_sleep")
async def random_sleep():
    log.debug("random sleep")
    time.sleep(random.randint(0, 5))
    return {"path": "/random_sleep"}


@app.get("/sleep")
async def random_sleep(t: Optional[float] = 1.0):
    log.debug(f"sleeping {t} sec...")
    time.sleep(t)
    return {"path": "/sleep", "t": t}


@app.get("/error_test")
async def random_sleep():
    log.debug("got error!!!!")
    raise ValueError("value error")


@app.get("/chain")
async def chain(req: Request):
    headers = getForwardHeaders(req)

    async with httpx.AsyncClient() as client:
        await client.get(f"http://localhost:{PORT}/", headers=headers)
    async with httpx.AsyncClient() as client:
        await client.get(f"{TARGET_ONE_ORIGIN}/io_task", headers=headers)
    async with httpx.AsyncClient() as client:
        await client.get(f"{TARGET_TWO_ORIGIN}/cpu_task", headers=headers)
    log.info("Chain Finished")
    return {"path": "/chain"}


if __name__ == "__main__":
    log.info(f"Running on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
