from app.brains.base import BaseBrain

class QwenBrain(BaseBrain):
    name = "qwen"
    model_env_key = "qwen_model"

    async def run(self, prompt: str, system: str | None = None) -> str:
        system = system or "너는 자비스의 코딩/테크니컬 보조 두뇌다. 정확한 코드와 구조를 제안하라."
        return await super().run(prompt, system)
