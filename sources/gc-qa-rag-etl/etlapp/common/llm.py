from openai import OpenAI
from etlapp.common.config import app_config
from typing import List, Dict
import time
import random


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
        print("🔧 [LLM-INIT] Initializing LLM client...")
        print(f"🔑 [LLM-INIT] API Key: {'***' + api_key[-4:] if api_key and len(api_key) > 4 else 'MISSING'}")
        print(f"🔗 [LLM-INIT] API Base: {api_base if api_base else 'MISSING'}")
        print(f"🤖 [LLM-INIT] Model: {model_name if model_name else 'MISSING'}")
        print(f"🎛️ [LLM-INIT] Temperature: {temperature}, Top-p: {top_p}")

        if not api_key:
            print("❌ [LLM-INIT] ERROR: API key is missing!")
        if not api_base:
            print("❌ [LLM-INIT] ERROR: API base URL is missing!")
        if not model_name:
            print("❌ [LLM-INIT] ERROR: Model name is missing!")

        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.top_p = top_p
        print("✅ [LLM-INIT] LLM client initialized successfully")

    def _create_completion(self, messages: List[Dict[str, str]], max_retries: int = 3) -> str:
        """Create completion with retry mechanism for handling rate limits and temporary failures"""

        print(f"🔗 [LLM] Making API call to: {self.client.base_url}")
        print(f"🤖 [LLM] Model: {self.model_name}")
        print(f"🎛️ [LLM] Temperature: {self.temperature}, Top-p: {self.top_p}")
        print(f"💬 [LLM] Message count: {len(messages)}")

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"🔄 [LLM] Retry attempt {attempt + 1}/{max_retries}")

                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    top_p=self.top_p,
                    temperature=self.temperature,
                )

                response_content = completion.choices[0].message.content
                print("✅ [LLM] API call successful")
                print(f"📊 [LLM] Usage - Prompt tokens: {completion.usage.prompt_tokens if completion.usage else 'N/A'}")
                print(f"📊 [LLM] Usage - Completion tokens: {completion.usage.completion_tokens if completion.usage else 'N/A'}")
                print(f"📄 [LLM] Response length: {len(response_content)} characters")

                return response_content

            except Exception as e:
                print(f"❌ [LLM] API call failed (attempt {attempt + 1}): {str(e)}")
                print(f"💣 [LLM] Exception type: {type(e).__name__}")

                # 检查是否是可重试的错误
                is_retryable = self._is_retryable_error(e)

                if hasattr(e, 'status_code'):
                    print(f"📡 [LLM] HTTP Status: {e.status_code}")
                if hasattr(e, 'response'):
                    print(f"📡 [LLM] Response body: {e.response}")

                # 如果是最后一次尝试或不可重试的错误，直接抛出
                if attempt == max_retries - 1 or not is_retryable:
                    print("💀 [LLM] Max retries reached or non-retryable error, giving up")
                    raise

                # 计算退避延迟（指数退避 + 随机抖动）
                base_delay = 2 ** attempt  # 1s, 2s, 4s
                jitter = random.uniform(0.1, 0.5)  # 随机抖动
                delay = base_delay + jitter

                print(f"⏳ [LLM] Waiting {delay:.1f}s before retry...")
                time.sleep(delay)

        # 理论上不会到达这里
        raise RuntimeError("Unexpected end of retry loop")

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_str = str(error).lower()

        # 速率限制错误 - 可重试
        if 'rate limit' in error_str or 'too many requests' in error_str:
            print("🚦 [LLM] Rate limit detected, will retry")
            return True

        # 临时服务器错误 - 可重试
        if hasattr(error, 'status_code'):
            if error.status_code in [429, 500, 502, 503, 504]:
                print(f"🔧 [LLM] Server error {error.status_code} detected, will retry")
                return True

        # 网络相关错误 - 可重试
        if 'timeout' in error_str or 'connection' in error_str:
            print("🌐 [LLM] Network error detected, will retry")
            return True

        # 其他错误 - 不可重试
        print("🚫 [LLM] Non-retryable error detected")
        return False

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
