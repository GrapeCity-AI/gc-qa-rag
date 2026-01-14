import asyncio
import json
import re
import logging
from openai import AsyncOpenAI
from ragapp.common.llm import get_llm_full_result
from ragapp.services.summary import summary_hits
from ragapp.services.search import search_sementic_hybrid
from ragapp.services.think import summary_hits_think
from ragapp.common.config import app_config

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=app_config.llm_research.api_key,
    base_url=app_config.llm_research.api_base,
)
model_name = app_config.llm_research.model_name


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


async def split_questions(keyword, messages, hits):
    hits_text = json.dumps(hits, ensure_ascii=False, default=vars)

    hits_prompt = f"""请综合参考上下文以及下面的用户问题和知识库检索结果，把用户的问题拆解为若干个子问题，输出子问题列表，输出为JSON格式。
## 输出格式
```json
["子问题...","子问题..."]
```

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
    logger.debug(
        "summary_hits words: "
        + str(len(json.dumps(messages_with_hits, ensure_ascii=False, default=vars)))
    )
    return chat(messages_with_hits)


async def research_hits(client, keyword, messages, hits, product, extra_instruction=""):
    logger.info(f"Researching hits for keyword: {keyword}")

    # hits = search_sementic_hybrid(client, keyword, product)

    # Generate questions
    questions_str = await get_llm_full_result(split_questions, keyword, messages, hits)
    questions = json.loads(extract_json_content(questions_str))
    logger.debug(f"Generated sub-questions: {questions}")

    # Process sub question
    async def process_sub_question(sub_question):
        logger.debug(f"Processing sub-question: {sub_question}")

        sub_hits = search_sementic_hybrid(client, sub_question, product)
        sub_answer = await get_llm_full_result(
            summary_hits, sub_question, messages, sub_hits, extra_instruction
        )
        return sub_question, sub_answer

    # Parallel execute
    sub_answers = {}
    tasks = [process_sub_question(sub_question) for sub_question in questions]
    results = await asyncio.gather(*tasks)

    # Merge answers
    for sub_question, sub_answer in results:
        sub_answers[sub_question] = sub_answer
        messages.insert(-1, {"role": "user", "content": sub_question})
        messages.insert(-1, {"role": "assistant", "content": sub_answer})

    # Summary the final answer
    return await summary_hits_think(keyword, messages, hits, extra_instruction)


def extract_json_content(text):
    pattern = r"```json(.*?)```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1)
    else:
        return text
