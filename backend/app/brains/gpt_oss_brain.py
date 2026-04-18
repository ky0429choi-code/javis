from app.brains.base import BaseBrain

class GptOssBrain(BaseBrain):
    name = "gpt_oss"
    model_env_key = "gpt_oss_model"

    async def run(self, prompt: str, system: str | None = None) -> str:
        system = system or "너는 자비스의 논리/추론/기획 보조 두뇌다. 정밀하고 전문적으로 응답하라."
        return await super().run(prompt, system)
