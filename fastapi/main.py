from fastapi import FastAPI
import os
import time

app = FastAPI()

# 느린 기동을 흉내내고 싶으면 SLOW_START=1, STARTUP_SLEEP=30 같은 env로 조절
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