from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import chat, tasks, approvals, prompts, health, mobile, hybrid
from app.api.routers import confidence as confidence_router
from app.core.bootstrap import bootstrap_application
from app.utils.settings import get_settings
import os
import logging

logger = logging.getLogger(__name__)

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

# 🆕 하이브리드 리소스 관리 라우터 추가 (4/18/2026)
try:
    app.include_router(hybrid.router)
    logger.info("✅ 하이브리드 리소스 관리 시스템 활성화")
except Exception as e:
    logger.warning(f"⚠️ 하이브리드 시스템 로드 실패: {e}")

# 🆕 종적 신뢰도 시스템 라우터 추가 (4/19/2026)
try:
    app.include_router(confidence_router.router, prefix="/api")
    logger.info("✅ 종적 신뢰도 모니터링 시스템 활성화")
except Exception as e:
    logger.warning(f"⚠️ 신뢰도 시스템 로드 실패: {e}")

# 🆕 대시보드 시스템 라우터 추가 (4/21/2026)
try:
    from app.api.routers import dashboard
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
    logger.info("✅ 관리 대시보드 API 활성화")
except Exception as e:
    logger.warning(f"⚠️ 대시보드 시스템 로드 실패: {e}")

@app.get("/api")
def read_api_root():
    return {"status": "online", "message": "JARVIS API endpoint. Access /docs for API documentation."}

# Mount static files from frontend/dist
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

# 🆕 대시보드 정적 파일 서빙 (항상 활성)
app.mount("/dashboard_assets", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="dashboard_assets")

@app.get("/dashboard")
async def get_dashboard():
    dashboard_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    return FileResponse(dashboard_path)

if os.path.exists(frontend_dist):
    # React 프론트엔드 빌드가 존재할 경우
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dist, "static")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("dashboard"):
            return {"detail": "Endpoint not found"}
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {"status": "online", "message": "JARVIS Agent Office Backend is running. Frontend build missing."}
