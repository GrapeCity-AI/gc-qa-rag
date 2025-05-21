from openai import OpenAI
from etlapp.common.config import app_config
from typing import List, Dict


class LLMClient:
    def __init__(
        self,
        api_key: str = app_config.llm.api_key,
        api_base: str = app_config.llm.api_base,
        model_name: str = app_config.llm.model_name,
        system_prompt: str = "你是一个乐于解答各种问题的助手。",
        temperature: float = 0.7,
        top_p: float = 0.7,
    ):
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.top_p = top_p

    def _create_completion(self, messages: List[Dict[str, str]]) -> str:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            top_p=self.top_p,
            temperature=self.temperature,
        )
        return completion.choices[0].message.content

    def chat(self, content: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content},
        ]
        return self._create_completion(messages)

    def chat_with_messages(self, messages: List[Dict[str, str]]) -> str:
        return self._create_completion(messages)


# Create a default instance
llm_client = LLMClient()


def chat_to_llm(content: str) -> str:
    return llm_client.chat(content)


def chat_to_llm_with_messages(messages: List[Dict[str, str]]) -> str:
    return llm_client.chat_with_messages(messages)
