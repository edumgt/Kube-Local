from fastapi import FastAPI
import os
import time

app = FastAPI()

SLOW_START = os.getenv("SLOW_START", "0") == "1"
STARTUP_SLEEP = int(os.getenv("STARTUP_SLEEP", "0"))


@app.on_event("startup")
def startup_hook():
    if SLOW_START and STARTUP_SLEEP > 0:
        time.sleep(STARTUP_SLEEP)


@app.get("/")
def root():
    return {"msg": "hello"}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    return {"ready": True}
