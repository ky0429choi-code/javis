import httpx
from app.utils.settings import get_settings

settings = get_settings()

class BaseBrain:
    name = "base"
    model_env_key = ""

    @property
    def model_name(self) -> str:
        return getattr(settings, self.model_env_key, "latest")

    def fallback(self, user_text: str, mode: str = "chat") -> str:
        if mode == "chat":
            return "사장님, 현재 로컬 지능형 엔진(JARVIS)과의 연결이 원활하지 않습니다. 모델 서버가 구동 중인지, 혹은 .env 설정이 올바른지 확인해 주시겠습니까?"
        return f"자비스(폴백): 요청하신 [{user_text}] 작업을 초안 모드로 기록했습니다. 서버 연결 후 정식으로 처리하겠습니다."

    async def run(self, prompt: str, system: str, mode: str = "chat") -> str:
        base_url = settings.intelligence_engine_url
        if not base_url:
            return self.fallback(prompt, mode)
        
        url = base_url.rstrip("/") + "/v1/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        headers = {
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    return self.fallback(prompt, mode)
                data = res.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return reply or self.fallback(prompt, mode)
        except Exception as e:
            print(f"Brain Call Error ({self.name}): {e}")
            return self.fallback(prompt, mode)
