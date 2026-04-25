from app.brains.base import BaseBrain

class GemmaBrain(BaseBrain):
    name = "gemma"
    model_env_key = "gemma_model"

    async def run(self, prompt: str, system: str | None = None) -> str:
        system = system or "너는 자비스의 대화/요약 보조 두뇌다. 자연스럽고 간결하게 응답하라."
        return await super().run(prompt, system)
