from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import chat, tasks, approvals, prompts, health, mobile
from app.core.bootstrap import bootstrap_application
from app.utils.settings import get_settings
import os

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bootstrap_application()

# Register API routers FIRST so they take precedence
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(mobile.router, prefix="/api")

@app.get("/api")
def read_api_root():
    return {"status": "online", "message": "JARVIS API endpoint. Access /docs for API documentation."}

# Mount static files from frontend/dist
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dist, "static")), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            # This shouldn't happen if routers are registered first, but safe fallback
            return {"detail": "API endpoint not found"}
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {"status": "online", "message": "JARVIS Agent Office Backend is running. Frontend build missing."}
