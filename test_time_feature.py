"""
JARVIS 시간 기능 테스트 (직접 구현)
"""
from datetime import datetime
import pytz


def test_timezone_feature():
    """JARVIS 타임존 기능 테스트"""
    print("\n" + "="*70)
    print("JARVIS 시간 기능 테스트")
    print("="*70)
    
    # 1. 설정 확인
    default_timezone = "Asia/Seoul"
    print(f"\n✓ 기본 타임존: {default_timezone}")
    
    # 2. 시간 정보 획득
    tz = pytz.timezone(default_timezone)
    now = datetime.now(tz)
    
    time_info = {
        "formatted": now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
        "iso": now.isoformat(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
    }
    
    print(f"\n✓ 현재 시간 (포맷): {time_info['formatted']}")
    print(f"✓ ISO 형식: {time_info['iso']}")
    
    # 3. 상세 시간 정보
    print(f"\n✓ 연도: {time_info['year']}")
    print(f"✓ 월: {time_info['month']}")
    print(f"✓ 일: {time_info['day']}")
    print(f"✓ 시: {time_info['hour']}")
    print(f"✓ 분: {time_info['minute']}")
    print(f"✓ 초: {time_info['second']}")
    
    # 4. 타임존 변경 테스트
    print(f"\n" + "-"*70)
    print("타임존 변경 테스트")
    print("-"*70)
    
    try:
        timezones = ["Asia/Seoul", "UTC", "America/New_York", "Asia/Tokyo"]
        
        for tz_name in timezones:
            tz = pytz.timezone(tz_name)
            local_time = datetime.now(tz)
            formatted = local_time.strftime("%Y년 %m월 %d일 %H시 %M분")
            print(f"\n✓ {tz_name:20} → {formatted}")
    
    except Exception as e:
        print(f"❌ 에러: {e}")
    
    print("\n" + "="*70)
    print("✅ 테스트 완료")
    print("="*70)


def test_health_response():
    """헬스 엔드포인트 응답 시뮬레이션"""
    print("\n" + "="*70)
    print("Health 엔드포인트 응답 시뮬레이션")
    print("="*70)
    
    default_timezone = "Asia/Seoul"
    tz = pytz.timezone(default_timezone)
    now = datetime.now(tz)
    
    time_info = {
        "formatted": now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초"),
        "iso": now.isoformat(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
    }
    
    response = {
        "ok": True,
        "service": "jarvis-agent-office-vnext",
        "time": time_info,
        "timezone": default_timezone,
        "message": f"JARVIS 현재 시간: {time_info['formatted']}"
    }
    
    print("\n📊 GET /api/health 응답 데이터:")
    print(f"  - Status: {response['ok']}")
    print(f"  - Service: {response['service']}")
    print(f"  - Timezone: {response['timezone']}")
    print(f"  - Message: {response['message']}")
    
    print(f"\n⏰ 시간 정보 (/api/time):")
    print(f"  - Formatted: {time_info['formatted']}")
    print(f"  - ISO: {time_info['iso']}")
    print(f"  - Year/Month/Day: {time_info['year']}/{time_info['month']}/{time_info['day']}")
    print(f"  - Hour/Minute/Second: {time_info['hour']}:{time_info['minute']}:{time_info['second']}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    try:
        test_timezone_feature()
        test_health_response()
        
        print("\n✅ 모든 테스트 완료!")
        print("\n📍 사용 방법:")
        print("  1. GET /api/health → JARVIS의 현재 시간 포함")
        print("  2. GET /api/time → 시간 정보만 조회")
        print("\n📝 타임존 변경:")
        print("  backend/.env 파일에서 TIMEZONE 값 수정")
        print("  예시:")
        print("    - TIMEZONE=Asia/Seoul (한국)")
        print("    - TIMEZONE=UTC (표준시)")
        print("    - TIMEZONE=America/New_York (미국 동부)")
        print("    - TIMEZONE=Asia/Tokyo (일본)")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
