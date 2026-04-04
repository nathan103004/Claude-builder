import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import auth, ocr, sessions, rvsq_router
from routers.chat import router as chat_router

load_dotenv()

app = FastAPI(title="SantéNav API")

_frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(auth.router)
app.include_router(ocr.router)
app.include_router(sessions.router)
app.include_router(rvsq_router.router, prefix="/rvsq")
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup_checks():
    import warnings
    if os.getenv("JWT_SECRET", "") in ("", "dev-secret-change-in-production"):
        warnings.warn(
            "JWT_SECRET is not set or is the insecure default. "
            "Set a strong random secret before deploying to production.",
            stacklevel=2,
        )


@app.on_event("shutdown")
def shutdown_cleanup():
    from rvsq.session_store import delete_all_sessions
    delete_all_sessions()
