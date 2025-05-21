import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict

from openai import OpenAI
from app.question import Question


class LLMInterface(ABC):
    model_name: str
    model_display_name: str
    options: dict = {}

    @abstractmethod
    def generate_answer(self, question: Question, context: List[Dict] = None) -> str:
        """Generate an answer to a question"""
        pass


class OpenAIImplementation(LLMInterface):
    def __init__(
        self,
        model_name: str,
        model_display_name: str = None,
        api_key: str = None,
        api_base: str = None,
        options: dict = None,
    ):
        self.model_name = model_name
        self.model_display_name = model_display_name or model_name
        self.client = OpenAI(api_key=api_key, base_url=api_base)
        self.logger = logging.getLogger(__name__)
        self.options = options or {}

    def generate_answer(self, question: Question, context: List[Dict] = None) -> str:
        """Call OpenAI API to generate an answer"""
        try:
            self.logger.debug(
                f"[{self.model_display_name}] Generating answer: {question.content}"
            )
            context_text = ""
            if context:
                context_text = json.dumps(context, ensure_ascii=False)
            options_text = ""
            if question.options:
                options_text = "\n".join(
                    [f"{k[-1]}. {v}" for k, v in question.options.items()]
                )
            if question.type.value == "单选题":
                format_tip = "请先分析，然后输出最符合的选项字母，如：<答案>A</答案>。"
            elif question.type.value == "多选题":
                format_tip = "请先分析，然后输出所有符合的选项字母，按顺序组合，用英文逗号。如：<答案>A,B</答案>。"
            elif question.type.value == "判断题":
                format_tip = "请只输出'对'或'错'。"
            else:
                format_tip = "请直接作答。"
            prompt = f"""请综合参考上下文以及下面的问题和知识库检索结果，回答问题。
## 要求
{format_tip}

## 题型
{question.type.value}

## 题干
{question.content}

## 候选项
{options_text}

## 已知信息（知识库检索结果）
{context_text}
"""
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                **self.options,
            )
            answer = self._fetch_answer(completion)
            self.logger.debug(
                f"[{self.model_display_name}] Answer generation completed"
            )
            return answer
        except Exception as e:
            self.logger.exception(
                f"[{self.model_display_name}] Exception occurred while generating answer: {e}"
            )
            return ""

    def _fetch_answer(self, completion):
        reasoning_content = ""  # Full reasoning process
        answer_content = ""  # Full reply
        is_answering = False  # Whether entering the reply phase
        for chunk in completion:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # Only collect reasoning content
            if (
                hasattr(delta, "reasoning_content")
                and delta.reasoning_content is not None
            ):
                if not is_answering:
                    print(delta.reasoning_content, end="", flush=True)
                reasoning_content += delta.reasoning_content

            # When content is received, start replying
            if hasattr(delta, "content") and delta.content:
                if not is_answering:
                    is_answering = True
                answer_content += delta.content
        return answer_content


class DashScopeImplementation(OpenAIImplementation):
    def __init__(
        self,
        model_name,
        model_display_name: str = None,
        api_key: str = "",
        dashscope_host: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        options: dict = None,
    ):
        super().__init__(
            model_name=model_name,
            model_display_name=model_display_name,
            api_key=api_key,
            api_base=dashscope_host,
            options=options,
        )
        self.logger = logging.getLogger(__name__)
