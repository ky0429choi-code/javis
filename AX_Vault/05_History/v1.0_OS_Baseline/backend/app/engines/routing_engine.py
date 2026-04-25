class RoutingEngine:
    def select(self, intent: dict) -> dict:
        text = intent["goal"]
        mode = intent["mode"]
        if mode == "chat":
            return {"brain": "gemma", "reason": "일상 대화/가벼운 응답"}
        if any(k in text for k in ["코드", "api", "서버", "파일 경로", "수정"]):
            return {"brain": "qwen", "reason": "코드/도구/실행 보조"}
        if any(k in text for k in ["설계", "구조", "비판", "리스크", "계획"]):
            return {"brain": "gpt_oss", "reason": "구조 판단/계획/비판"}
        return {"brain": "gemma", "reason": "일반 초안/요약"}
