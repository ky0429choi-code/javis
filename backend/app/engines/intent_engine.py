class IntentEngine:
    def resolve(self, message: str, mode: str, context: dict) -> dict:
        task_keywords = ["업무", "보고", "파일", "생성", "삭제", "수정", "정리", "분석"]
        detected_mode = mode
        if mode == "chat" and any(k in message for k in task_keywords):
            detected_mode = "task"
        return {
            "goal": message,
            "mode": detected_mode,
            "constraints": context.get("constraints", []),
            "user_kpi": context.get("user_kpi"),
        }
