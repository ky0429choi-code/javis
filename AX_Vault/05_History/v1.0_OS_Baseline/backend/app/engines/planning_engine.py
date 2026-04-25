class PlanningEngine:
    def build(self, intent: dict) -> dict:
        mode = intent["mode"]
        if mode == "chat":
            steps = ["질문 이해", "자연스럽게 응답"]
        else:
            steps = ["요청 구조화", "필요 자료 확인", "초안 생성", "검토/승인 판단"]
        return {"steps": steps, "mode": mode}
