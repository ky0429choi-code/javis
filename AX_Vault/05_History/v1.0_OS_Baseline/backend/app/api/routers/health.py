from fastapi import APIRouter
from datetime import datetime
from app.utils.settings import get_settings
import os

router = APIRouter(tags=["health"])

def get_jarvis_time():
    """JARVIS의 현재 시간 반환 (타임존 적용)"""
    settings = get_settings()
    timezone_str = settings.timezone
    
    try:
        import pytz
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        return {
            "formatted": now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
            "iso": now.isoformat(),
            "timestamp": now.timestamp(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
        }
    except ImportError:
        # pytz가 없으면 시스템 시간 사용
        now = datetime.now()
        return {
            "formatted": now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
            "iso": now.isoformat(),
            "timestamp": now.timestamp(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
        }

@router.get("/health")
def health() -> dict:
    """헬스 체크 엔드포인트 - JARVIS 시간 정보 포함"""
    settings = get_settings()
    jarvis_time = get_jarvis_time()
    
    return {
        "ok": True,
        "service": "jarvis-agent-office-vnext",
        "time": jarvis_time,
        "timezone": settings.timezone,
        "message": f"JARVIS 현재 시간: {jarvis_time['formatted']}"
    }

@router.get("/time")
def get_time() -> dict:
    """시간 정보 전용 엔드포인트"""
    settings = get_settings()
    jarvis_time = get_jarvis_time()
    
    return {
        "current_time": jarvis_time["formatted"],
        "timezone": settings.timezone,
        "iso": jarvis_time["iso"],
        "timestamp": jarvis_time["timestamp"],
        "details": {
            "year": jarvis_time["year"],
            "month": jarvis_time["month"],
            "day": jarvis_time["day"],
            "hour": jarvis_time["hour"],
            "minute": jarvis_time["minute"],
            "second": jarvis_time["second"],
        }
    }
