import json
import logging
from openai import AsyncOpenAI
from ragapp.common.config import app_config

# Initialize logger
logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=app_config.llm_think.api_key,
    base_url=app_config.llm_think.api_base,
)
model_name = app_config.llm_think.model_name


async def think(messages):
    completion = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=True,
    )

    think_started = False
    content_started = False

    async for chunk in completion:
        reasoning_content = chunk.choices[0].delta.reasoning_content
        if reasoning_content is not None and len(reasoning_content):
            if not think_started:
                yield "> "
                think_started = True
            yield reasoning_content.replace("\n", "\n> ")

        content = chunk.choices[0].delta.content
        if content is not None and len(content):
            if not content_started:
                yield "\r\n---\r\n"
                content_started = True
            yield content


async def summary_hits_think(keyword, messages, hits, extra_instruction=""):
    hits_text = json.dumps(hits, ensure_ascii=False, default=vars)

    extra_part = ""
    if extra_instruction:
        extra_part = f"\n## 回答要求\n{extra_instruction}\n"

    hits_prompt = f"""你正在和用户对话，请综合参考上下文以及下面的用户问题和知识库检索结果，回答用户的问题。回答时附上文档链接。
{extra_part}## 用户问题
{keyword}

## 知识库检索结果
{hits_text}
"""

    # deepseek-R1's system prompt should be empty
    messages_with_hits = [
        {
            "role": "system",
            "content": "",
        }
    ] + messages

    messages_with_hits[-1]["content"] = hits_prompt
    logger.debug(
        "summary_hits words: "
        + str(len(json.dumps(messages_with_hits, ensure_ascii=False, default=vars)))
    )
    return think(messages_with_hits)
