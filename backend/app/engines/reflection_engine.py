class ReflectionEngine:
    def review(self, result: str, intent: dict) -> dict:
        return {
            "quality_note": "응답 후 승인/기록 필요 여부 확인",
            "needs_followup": intent.get("mode") == "task",
            "learning_policy": "자율 수집은 허용, 영구 반영은 승인/검증 후 허용",
        }
