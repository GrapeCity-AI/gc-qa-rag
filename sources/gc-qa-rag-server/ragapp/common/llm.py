import json


async def get_llm_full_result(chat_method, *args, **kwargs):
    """
    A generic async method to call chat_method and process the results.

    :param chat_method: An async function responsible for generating the result stream.
    :param args: Positional arguments passed to chat_method.
    :param kwargs: Keyword arguments passed to chat_method.
    :return: The concatenated complete result string.
    """

    async def wrapper():
        result_gen = await chat_method(*args, **kwargs)
        result = ""

        async for text in result_gen:
            result += text
        return result

    return await wrapper()


async def get_llm_sse_result(chat_method, *args, **kwargs):
    async def wrapper():
        result_gen = await chat_method(*args, **kwargs)

        async for text in result_gen:
            # Format the text as SSE compliant JSON
            sse_message = f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
            yield sse_message

    return wrapper()
