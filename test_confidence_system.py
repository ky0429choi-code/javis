"""
JARVIS 종적 신뢰도 시스템 통합 테스트.
스키마, 수집기, 보고서 생성기, DB 초기화를 검증합니다.
"""

import sys
import os
import json

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

def test_1_schemas():
    """Test 1: 스키마 유효성 검증"""
    print("\n" + "─"*60)
    print("🧪 Test 1: 스키마 유효성 검증")
    print("─"*60)
    
    from app.schemas.confidence import (
        StepConfidence, PipelineConfidence, CompletionReport,
        ConfidenceTrend, ConfidenceSummary, PipelineComponent,
        score_to_level, score_to_stars
    )
    
    # StepConfidence 생성
    step = StepConfidence(
        component=PipelineComponent.EXECUTOR,
        score=0.85,
        reason="3단계 분해 성공",
        latency_ms=1200,
        retries=1,
        provider="local_ollama"
    )
    assert 0 <= step.score <= 1.0
    assert step.status_emoji == "🟢"
    print(f"  ✅ StepConfidence: score={step.score}, emoji={step.status_emoji}")
    
    # PipelineConfidence 생성 + 가중 평균 계산
    pipeline = PipelineConfidence(
        task_id="TEST-001",
        goal="테스트 작업",
    )
    pipeline.steps = [
        StepConfidence(component=PipelineComponent.PLANNER, score=0.95, latency_ms=100),
        StepConfidence(component=PipelineComponent.EXECUTOR, score=0.82, latency_ms=3200, retries=1),
        StepConfidence(component=PipelineComponent.REVIEWER, score=0.90, latency_ms=450),
        StepConfidence(component=PipelineComponent.WIKI, score=0.80, latency_ms=800),
    ]
    overall = pipeline.calculate_overall()
    assert 0.80 < overall < 0.95, f"Expected 0.80~0.95, got {overall}"
    print(f"  ✅ PipelineConfidence: overall={overall:.4f}")
    
    # CompletionReport 생성
    report = CompletionReport.from_pipeline(pipeline)
    assert report.task_id == "TEST-001"
    assert report.overall_score == overall
    assert report.level in ("high", "excellent")
    assert len(report.stars) == 5
    print(f"  ✅ CompletionReport: level={report.level}, stars={report.stars}")
    
    # 점수 변환 유틸리티
    assert score_to_level(0.95).value == "excellent"
    assert score_to_level(0.75).value == "high"
    assert score_to_level(0.45).value == "low"
    assert score_to_level(0.15).value == "critical"
    print(f"  ✅ score_to_level: 모든 등급 변환 정상")
    
    assert "★" in score_to_stars(0.8)
    print(f"  ✅ score_to_stars: {score_to_stars(0.8)}")
    
    # ConfidenceTrend
    trend = ConfidenceTrend(
        component="executor",
        period="7d",
        current_ema=0.85,
        previous_ema=0.78,
        direction="improving",
        sample_count=15
    )
    assert trend.direction_emoji == "↑"
    print(f"  ✅ ConfidenceTrend: {trend.direction} {trend.direction_emoji}")
    
    print("\n  ✅ Test 1 PASSED: 모든 스키마 검증 완료")
    return True


def test_2_database():
    """Test 2: DB 테이블 초기화 검증"""
    print("\n" + "─"*60)
    print("🧪 Test 2: DB 테이블 초기화 검증")
    print("─"*60)
    
    from app.memory.repository import initialize_database, Repository
    
    initialize_database()
    
    repo = Repository()
    with repo.connect() as con:
        # confidence_log 테이블 존재 확인
        cursor = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='confidence_log'"
        )
        assert cursor.fetchone() is not None, "confidence_log 테이블 없음"
        print("  ✅ confidence_log 테이블 존재")
        
        # completion_reports 테이블 존재 확인
        cursor = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='completion_reports'"
        )
        assert cursor.fetchone() is not None, "completion_reports 테이블 없음"
        print("  ✅ completion_reports 테이블 존재")
        
        # 인덱스 확인
        cursor = con.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_conf_%'"
        )
        indexes = [r[0] for r in cursor.fetchall()]
        assert len(indexes) >= 3, f"인덱스 부족: {indexes}"
        print(f"  ✅ 인덱스 확인: {indexes}")
    
    print("\n  ✅ Test 2 PASSED: DB 초기화 완료")
    return True


def test_3_confidence_collector():
    """Test 3: 신뢰도 수집기 검증"""
    print("\n" + "─"*60)
    print("🧪 Test 3: 신뢰도 수집기 검증")
    print("─"*60)
    
    from app.core.confidence_collector import get_confidence_collector
    
    collector = get_confidence_collector()
    
    # 스텝 기록
    score1 = collector.record_step(
        task_id="TEST-COLLECTOR-001",
        component="planner",
        success=True,
        latency_ms=150,
        retries=0,
        provider="local_ollama",
        reason="test_planning_ok",
    )
    assert 0.9 <= score1 <= 1.0, f"Expected high score, got {score1}"
    print(f"  ✅ record_step (성공, 빠름): score={score1}")
    
    score2 = collector.record_step(
        task_id="TEST-COLLECTOR-001",
        component="executor",
        success=True,
        latency_ms=8000,   # 느림
        retries=2,          # 2회 재시도
        provider="groq",
        reason="test_execution_slow",
    )
    assert score2 < score1, f"Expected lower score, got {score2}"
    print(f"  ✅ record_step (성공, 느림, 재시도): score={score2}")
    
    score3 = collector.record_step(
        task_id="TEST-COLLECTOR-001",
        component="reviewer",
        success=False,
        latency_ms=500,
        retries=3,
        reason="test_review_failed",
    )
    assert score3 < 0.5, f"Expected very low score, got {score3}"
    print(f"  ✅ record_step (실패): score={score3}")
    
    # 컴포넌트 종적 신뢰도
    info = collector.get_component_confidence("planner", days=1)
    assert info["sample_count"] >= 1
    assert info["ema"] > 0
    print(f"  ✅ get_component_confidence: ema={info['ema']:.4f}, samples={info['sample_count']}")
    
    # 시스템 요약
    summary = collector.get_system_summary(days=1)
    assert "overall_health" in summary
    assert "component_scores" in summary
    print(f"  ✅ get_system_summary: health={summary['overall_health']}, score={summary['overall_score']:.4f}")
    
    # EMA 계산 검증
    ema = collector._calculate_ema([0.8, 0.85, 0.9, 0.87, 0.92])
    assert 0.8 < ema < 1.0
    print(f"  ✅ EMA 계산: {ema:.4f}")
    
    # 동적 프로바이더 우선순위
    priority = collector.get_dynamic_provider_priority()
    assert isinstance(priority, list)
    assert len(priority) > 0
    print(f"  ✅ 동적 우선순위: {priority}")
    
    print("\n  ✅ Test 3 PASSED: 신뢰도 수집기 정상 작동")
    return True


def test_4_completion_reporter():
    """Test 4: 완료보고서 생성기 검증"""
    print("\n" + "─"*60)
    print("🧪 Test 4: 완료보고서 생성기 검증")
    print("─"*60)
    
    from app.schemas.confidence import StepConfidence, PipelineConfidence, PipelineComponent
    from app.core.completion_reporter import get_completion_reporter
    from app.core.confidence_collector import get_confidence_collector
    
    reporter = get_completion_reporter()
    collector = get_confidence_collector()
    
    # 테스트 파이프라인 생성
    pipeline = PipelineConfidence(
        task_id="TEST-REPORT-001",
        goal="종적 신뢰도 시스템 테스트",
        created_at="2026-04-19T23:00:00",
    )
    pipeline.steps = [
        StepConfidence(component=PipelineComponent.PLANNER, score=0.95, latency_ms=120, reason="3단계 분해 성공"),
        StepConfidence(component=PipelineComponent.EXECUTOR, score=0.82, latency_ms=3200, retries=1, reason="1회 재시도"),
        StepConfidence(component=PipelineComponent.REVIEWER, score=0.90, latency_ms=450, reason="Ruff pass"),
        StepConfidence(component=PipelineComponent.WIKI, score=0.80, latency_ms=800, reason="지식 저장됨"),
    ]
    pipeline.duration_ms = 4570
    pipeline.provider_used = "local_ollama"
    
    # 보고서 생성
    report = reporter.generate_report(pipeline)
    
    assert report.task_id == "TEST-REPORT-001"
    assert report.overall_score > 0
    assert len(report.report_md) > 100
    assert "파이프라인 스코어카드" in report.report_md
    assert len(report.step_details) == 4
    print(f"  ✅ 보고서 생성 완료: score={report.overall_score:.4f}")
    print(f"  ✅ 마크다운 길이: {len(report.report_md)}자")
    print(f"  ✅ 등급: {report.level}, 별점: {report.stars}")
    
    # DB에서 조회
    stored = collector.get_report_by_task("TEST-REPORT-001")
    assert stored is not None
    assert stored["task_id"] == "TEST-REPORT-001"
    print(f"  ✅ DB 저장 확인")
    
    # 보고서 목록 조회
    reports = collector.get_completion_reports(limit=5)
    assert len(reports) > 0
    print(f"  ✅ 보고서 목록: {len(reports)}건")
    
    # 일일 리포트
    daily_md = reporter.generate_daily_summary()
    assert "일일 신뢰도 보고서" in daily_md
    print(f"  ✅ 일일 보고서 생성: {len(daily_md)}자")
    
    # 주간 트렌드
    weekly_md = reporter.generate_weekly_trend()
    assert "주간 신뢰도 트렌드" in weekly_md
    print(f"  ✅ 주간 트렌드 생성: {len(weekly_md)}자")
    
    print("\n  ✅ Test 4 PASSED: 완료보고서 생성기 정상 작동")
    return True


def main():
    """전체 테스트 실행"""
    print("\n" + "█"*60)
    print("🎯 JARVIS 종적 신뢰도 시스템 통합 테스트")
    print("█"*60)
    
    results = {}
    tests = [
        ("스키마 유효성", test_1_schemas),
        ("DB 초기화", test_2_database),
        ("신뢰도 수집기", test_3_confidence_collector),
        ("완료보고서 생성", test_4_completion_reporter),
    ]
    
    for name, test_fn in tests:
        try:
            results[name] = test_fn()
        except Exception as e:
            print(f"\n  ❌ {name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # 결과 요약
    print("\n" + "█"*60)
    print("📊 테스트 결과 요약")
    print("█"*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, ok in results.items():
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status} | {name}")
    
    print(f"\n  결과: {passed}/{total} PASSED")
    
    if passed == total:
        print("  🎉 모든 테스트 통과!")
    else:
        print("  ⚠️ 일부 테스트 실패")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
