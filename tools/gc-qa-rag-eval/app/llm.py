import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict

from openai import OpenAI
from app.question import Question
from app.query import KnowledgeBaseClient


class LLMInterface(ABC):
    model_name: str
    model_display_name: str
    options: dict = {}

    @abstractmethod
    def generate_answer(self, question: Question, context: List[Dict] = None) -> str:
        """Generate an answer to a question"""
        pass
    
    @abstractmethod
    def generate_answer_agentic(self, question: Question, kb_client: KnowledgeBaseClient) -> str:
        """Generate an answer using agentic mode with function calling"""
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
        
    def _get_search_function_schema(self) -> Dict:
        """Define the search function schema for function calling"""
        return {
            "name": "search_knowledge_base",
            "description": "Search the knowledge base（RAG vector database） for relevant information to answer the question. You can call this multiple times with different querys to gather comprehensive information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The natural language question query string to search for relevant information"
                    }
                },
                "required": ["query"]
            }
        }
    
    def _handle_search_function_call(self, function_call, kb_client: KnowledgeBaseClient, question: Question) -> str:
        """Handle the search function call and return results"""
        try:
            arguments = json.loads(function_call.arguments)
            keyword = arguments.get("query", "")
            product = question.product
            
            self.logger.debug(f"Function call: search_knowledge_base(keyword='{keyword}', product='{product}')")
            
            # Call the knowledge base
            results = kb_client.search(keyword, product)
            
            # Format results for the model
            if results:
                return json.dumps(results, ensure_ascii=False, indent=2)
            else:
                return "没有找到相关信息"
                
        except Exception as e:
            self.logger.error(f"Error handling search function call: {e}")
            return f"搜索过程中出现错误: {str(e)}"

    def generate_answer_agentic(self, question: Question, kb_client: KnowledgeBaseClient) -> str:
        """Generate answer using agentic mode with function calling"""
        try:
            self.logger.debug(f"[{self.model_display_name}] Generating agentic answer: {question.content}")
            
            # Prepare options text
            options_text = ""
            if question.options:
                options_text = "\n".join([f"{k[-1]}. {v}" for k, v in question.options.items()])
            
            # Prepare format instruction based on question type
            if question.type.value == "单选题":
                format_tip = "请先分析，然后输出最符合的选项字母，如：<答案>A</答案>。"
            elif question.type.value == "多选题":
                format_tip = "请先分析，然后输出所有符合的选项字母，按顺序组合，用英文逗号。如：<答案>A,B</答案>。"
            elif question.type.value == "判断题":
                format_tip = "请只输出'对'或'错'。"
            else:
                format_tip = "请直接作答。"
                
            system_prompt = f"""你是一个具有高度自主能动性的问题解决专家。
## 注意事项：
1. 你拥有search_knowledge_base工具，应该像人类专家通过RAG搜索引擎解决复杂问题一样。
2. 最终答案的字母选项请务必使用<答案></答案>标签包裹，如果是多个选项，字母之间用英文逗号分隔。

## 答题要求：
{format_tip}
"""

            user_prompt = f"""现在请深度分析并解决以下问题：

## 题型
{question.type.value}

## 题目内容
{question.content}

## 候选选项
{options_text}

最终答案的字母选项请务必使用<答案></答案>标签包裹，如果是多个选项，字母之间用英文逗号分隔。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            tools = [{"type": "function", "function": self._get_search_function_schema()}]
            
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                self.logger.debug(f"[{self.model_display_name}] Agentic iteration {iteration}")
                
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    **self.options
                )
                
                message = completion.choices[0].message
                messages.append(message)
                
                # Check if model wants to call functions
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == "search_knowledge_base":
                            function_result = self._handle_search_function_call(
                                tool_call.function, kb_client, question
                            )
                            
                            # Add function result to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": function_result
                            })
                else:
                    # Model finished without function calls, return the answer
                    answer = message.content or ""
                    self.logger.debug(f"[{self.model_display_name}] Agentic answer generation completed")
                    return answer
            
            # If max iterations reached, get final answer
            final_completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages + [{"role": "user", "content": "请基于已搜索的信息给出最终答案。"}],
                **self.options
            )
            
            return final_completion.choices[0].message.content or ""
            
        except Exception as e:
            self.logger.exception(f"[{self.model_display_name}] Exception in agentic mode: {e}")
            return ""

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


class OpenRouterImplementation(OpenAIImplementation):
    def __init__(
        self,
        model_name,
        model_display_name: str = None,
        api_key: str = "",
        api_base: str = "https://openrouter.ai/api/v1",
        options: dict = None,
    ):
        super().__init__(
            model_name=model_name,
            model_display_name=model_display_name,
            api_key=api_key,
            api_base=api_base,
            options=options,
        )
        self.logger = logging.getLogger(__name__)
