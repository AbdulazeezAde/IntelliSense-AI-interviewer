from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router as api_router
from .ws import router as ws_router
from .tts.api import router as tts_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="InterviewSense AI Backend")

# Serve the simple client demo (Siri-like) at /client/
app.mount("/client", StaticFiles(directory="app/client", html=True), name="client")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")
app.include_router(ws_router, prefix="/v1")
app.include_router(tts_router, prefix="/v1/tts")

@app.get("/")
async def root():
    return {"status": "ok", "service": "InterviewSense AI Backend"}
