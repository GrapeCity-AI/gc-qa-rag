import json
import logging
from openai import AsyncOpenAI
from ragapp.common.config import app_config

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=app_config.llm_summary.api_key,
    base_url=app_config.llm_summary.api_base,
)
model_name = app_config.llm_summary.model_name


async def chat(messages):
    completion = await client.chat.completions.create(
        model=model_name,
        messages=messages,
        top_p=0.7,
        temperature=0.7,
        stream=True,
    )

    async for chunk in completion:
        text = chunk.choices[0].delta.content
        if text is not None and len(text):
            yield text


async def summary_hits(keyword, messages, hits):
    hits_text = json.dumps(hits, ensure_ascii=False, default=vars)

    hits_prompt = f"""你正在和用户对话，请综合参考上下文以及下面的用户问题和知识库检索结果，回答用户的问题。回答时附上文档链接。
## 用户问题
{keyword}

## 知识库检索结果
{hits_text}
"""

    messages_with_hits = [
        {
            "role": "system",
            "content": "你是一个乐于解答各种问题的助手。",
        }
    ] + messages

    messages_with_hits[-1]["content"] = hits_prompt
    logger.info(
        "summary_hits words: "
        + str(len(json.dumps(messages_with_hits, ensure_ascii=False, default=vars)))
    )
    return chat(messages_with_hits)
