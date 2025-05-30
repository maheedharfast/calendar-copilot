from pkg.log.logger import Logger
from openai import AsyncOpenAI
from enum import Enum
from typing import Optional
gemini_model_map = {

    "GEMINI_2_0_PRO_EXP": "gemini-2.0-pro-exp-02-05",
    "GEMINI_2_5_FLASH":"gemini-2.5-flash-preview-04-17"
}
class LLMModel(Enum):
    GEMINI_2_0_PRO_EXP: str = "GEMINI_2_0_PRO_EXP"
    GEMINI_2_5_FLASH: str = "GEMINI_2_5_FLASH"

class LLMClient:

    def __init__(self, gemini_api_key:str, logger: Logger):
        self.logger = logger
        self.gemini_client: AsyncOpenAI = AsyncOpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    async def get_response(self, prompt: str, model: LLMModel, system_msg: str = "",
                           temperature: float = 0.3, max_tokens: int = 8000, response_format: Optional[dict] = None) -> str:
        if response_format is None:
            response_format = {"type": "text"}
        messages: list[dict] = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]
        try:
            model_value = gemini_model_map.get(model.value)
            response = await self.gemini_client.chat.completions.create(
                model=model_value,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,

            )
            response_text = response.choices[0].message.content
            return response_text
        except Exception as e:
            self.logger.error(f"Error in LLMClient.get_response: {e}")
            raise e


