from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import auth, ocr, sessions, rvsq_router
from routers.chat import router as chat_router

load_dotenv()

app = FastAPI(title="SantéNav API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ocr.router)
app.include_router(sessions.router)
app.include_router(rvsq_router.router, prefix="/rvsq")
app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("shutdown")
def shutdown_cleanup():
    from rvsq.session_store import delete_all_sessions
    delete_all_sessions()
