from openai import AsyncOpenAI
from ragapp.common.config import app_config

client = AsyncOpenAI(
    api_key=app_config.llm_query.api_key,
    base_url=app_config.llm_query.api_base,
)
model_name = app_config.llm_query.model_name


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


async def chat_for_query(contents):
    prompt = f"""你是一个问题生成器，你需要从下面的对话中识别出用户想要查询的问题，直接输出该文本，该文本将用于在知识库中检索相关知识。    

## 对话内容
{contents}
    """

    messages = [
        {
            "role": "system",
            "content": "你是一个乐于解答各种问题的助手。",
        },
        {"role": "user", "content": prompt},
    ]
    return chat(messages)
