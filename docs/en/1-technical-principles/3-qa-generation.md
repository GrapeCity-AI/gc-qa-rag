# Q&A Generation

This chapter introduces the core principles and implementation details of the "Generation" stage in the gc-qa-rag intelligent Q&A system. The goal of this stage is: **Based on user questions and retrieved highly relevant knowledge, utilize large language models to generate natural, fluent, comprehensive summary answers**.

## 1. Generation Process Overview

The Q&A generation stage is the final component of the RAG (Retrieval-Augmented Generation) three-stage architecture. Its main process is as follows:

1. User inputs a question, system completes retrieval, obtaining TopK (e.g., 8) highly relevant knowledge entries (including questions, answers, detailed explanations, summaries, original links, and other metadata);
2. System integrates user questions with retrieval results, constructs standardized prompts, and inputs them to large language models (LLM);
3. LLM synthesizes context and knowledge base content to generate final answers, which can be returned to users with original links, detailed explanations, and other information.

## 2. Input Structure and Prompt Design

The generation stage mainly includes the following inputs:

-   **User Question** (User Input): Current user's natural language query;
-   **Retrieval Results** (Hits): Highly relevant knowledge entry list obtained through hybrid retrieval and RRF fusion ranking.

The system uses structured prompt templates to concatenate the above information and input it to LLM. For example:

```python
"""
You are conversing with users. Please comprehensively refer to the context as well as the user questions and knowledge base retrieval results below to answer user questions. Attach document links when answering.
## User Question
{keyword}

## Knowledge Base Retrieval Results
{hits_text}
"""
```

Where `hits_text` is the JSON serialized content of retrieval results, containing fields like "Question", "Answer", "FullAnswer", "Summary", "Url" for each knowledge entry.

## 3. Generation Service Implementation

The system calls LLM services asynchronously, supporting streaming output to improve response speed and user experience. Main implementation logic as follows:

-   Assemble message body (messages), including system prompt and user prompt;
-   Call LLM's chat/completions interface, set reasonable temperature, top_p parameters to balance creativity and accuracy;
-   Use streaming (stream=True) method to obtain model output, generating and returning to frontend simultaneously.

Related code implementation see `ragapp/services/summary.py`:

```python
async def summary_hits(keyword, messages, hits):
    hits_text = json.dumps(hits, ensure_ascii=False, default=vars)
    hits_prompt = f"""You are conversing with users. Please comprehensively refer to the context as well as the user questions and knowledge base retrieval results below to answer user questions. Attach document links when answering.
    ## User Question
    {keyword}
    ## Knowledge Base Retrieval Results
    {hits_text}
    """
    ...
    return chat(messages_with_hits)
```

## 4. Reasoning Mode

To enhance answer transparency and credibility, the system supports "reasoning mode" output. In this mode, LLM first outputs the reasoning process, then provides the final answer. For example:

-   Output reasoning steps with `> ` prefix;
-   Use separator `---` to distinguish reasoning from formal answers.

Related implementation see `ragapp/services/think.py`, adapted for large models supporting reasoning_content (such as deepseek-R1):

```python
async def think(messages):
    ...
    async for chunk in completion:
        reasoning_content = chunk.choices[0].delta.reasoning_content
        ...
        content = chunk.choices[0].delta.content
        ...
```

## 5. Multi-turn Conversation and Question Rewriting

The system supports multi-turn conversation scenarios and can automatically identify what users really want to ask based on historical conversation context. The specific process is:

1. Collect historical conversation content and input it to LLM question generator;
2. LLM outputs user's real intent question as input for retrieval and generation.

Related implementation see `ragapp/services/query.py`:

```python
async def chat_for_query(contents):
    prompt = f"""You are a question generator. You need to identify the question users want to query from the following conversation and directly output that text, which will be used to retrieve relevant knowledge in the knowledge base.
    ## Conversation Content
    {contents}
    """
    ...
    return chat(messages)
```

## 6. Generation Result Structure

The final generated answer includes not only direct responses but also:

-   Original links (Url), titles (Title), categories (Category) and other metadata from relevant knowledge entries;
-   Detailed explanations (FullAnswer), context summaries (Summary) and other auxiliary information;
-   Optional reasoning process (reasoning mode) for users.

## 7. Technical Advantages and Engineering Practices

-   **Structured Prompt Design**: Ensures LLM can fully utilize retrieved knowledge, improving answer accuracy;
-   **Streaming Output**: Optimizes user experience, reduces waiting time;
-   **Multi-turn Conversation Support**: Improves Q&A capabilities in complex scenarios;
-   **Reasoning Transparency**: Enhances user trust, facilitates result tracing.
