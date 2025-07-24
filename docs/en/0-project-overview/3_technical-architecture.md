# Technical Architecture

## Architecture Overview - RAG Solution Based on QA Pre-generation

This system adopts a typical RAG (Retrieval-Augmented Generation) three-stage architecture, divided into three core stages: construction (ETL), retrieval (Retrieve), and generation (Generate):

-   **Construction (ETL)**: Extract knowledge from original documents, generate structured Q&A pairs, vectorize and store them in vector databases;
-   **Retrieval**: When users ask questions, combine keyword and semantic understanding with hybrid ranking strategies to quickly locate the most relevant knowledge points;
-   **Generation**: Based on large language models and retrieval results, generate natural language answers.

The entire process achieves high availability, scalability, and good engineering implementation capability through modular design.

## Knowledge Construction (ETL)

ETL is the foundational component of the entire system, aiming to transform unstructured original documents into knowledge points usable for retrieval. This process mainly includes the following steps:

### Document Acquisition

Knowledge sources include official help documents, help posts and tutorial posts from technical forums:

-   Official help documents: approximately 4,000 articles
-   Technical forum - Help Center: approximately 50,000 posts
-   Technical forum - Topic Tutorials: approximately 4,000 posts

Future plans to expand the following content sources:

-   API interface documentation
-   Public course video transcripts
-   Product plugin descriptions, app marketplace product materials
-   Success case analyses

Supports scheduled incremental crawling mechanisms, with shorter crawling cycles for frequently updated content to ensure knowledge base timeliness.

### Chunking

Unlike traditional paragraph segmentation methods, we adopted a "QA chunking" method based on large language models, converting document content into multiple question-answer pairs (QA Pairs). This approach focuses more on actual knowledge points, improving the effectiveness of subsequent retrieval and generation.

The specific process is as follows:

1. Use LLM to convert original documents into structured Q&A pairs;
2. Conduct quality verification on generated QAs, manually spot-check some samples to verify accuracy;
3. Output standardized JSON format for convenient subsequent processing.

Compared to coarse-grained text paragraphs, QA pair format is closer to users' actual query intentions, helping improve the recall rate and relevance of retrieval systems.

### Text Embedding

To improve retrieval accuracy and robustness, we adopt a "bidirectional vectorization" strategy, using both sparse vectors (BM25) and dense semantic vectors (Dense Vector) for multi-dimensional representation.

Additionally, we introduced multiple enhancement mechanisms during the vectorization process:

#### Summary Generation

Generate a brief summary created by large language models for each QA pair, describing the background information of its document context, used to help subsequent generation models better understand context.

#### Full Answer Extension

For important or high-frequency questions, generate an additional detailed answer version stored as payload for frontend display or to provide richer context support for the generation phase.

#### Prefix Mechanism

To avoid "spatial aliasing" phenomena caused by similar questions in different documents, we add the category and title of the document containing the QA as a prefix to the original text before vectorization.

Example template:

```
[Category/Title] + Question
[Forguncy/Connect to External Database/Connect to Oracle] What needs to be done before connecting to Oracle database?
```

This strategy can effectively distinguish questions with the same semantic meaning but different application scenarios, improving retrieval precision.

#### Vector Fields

Generate four types of vector features:

-   Prefix_Question_Dense
-   Prefix_Answer_Dense
-   Prefix_Question_Sparse
-   Prefix_Answer_Sparse

#### Payload Fields

Each knowledge entry contains the following metadata for subsequent retrieval and generation use:

-   `Question`: Questions users might ask
-   `Answer`: Concise standard answer
-   `FullAnswer`: Detailed explanation version
-   `Summary`: Context summary
-   `Url`: Original article link
-   `Title`: Article title
-   `Category`: Category classification
-   `Date`: Creation time (Unix timestamp)

Through the above design, our vectorization solution considers both keyword matching and semantic understanding, significantly improving retrieval effectiveness while providing richer context support for the generation stage.

### Payload Example

```json
{
    "Question": "What needs to be done before connecting to Oracle database?",
    "Answer": "Oracle needs to be configured first, and only after configuration is complete can you connect to Oracle.",
    "FullAnswer": "# Preparation for Connecting to Oracle Database Before connecting to Oracle database, some necessary configuration steps need to be completed......",
    "Summary": "This document introduces how to connect to Oracle database, including steps for configuring Oracle and specific operations for connecting Oracle in Forguncy......",
    "Url": "https://www.grapecity.com.cn/solutions/huozige/help/docs/connecttoexternaldatabase/connecttooracle",
    "Title": "Connect to Oracle",
    "Category": "Forguncy Chinese Documentation/Chapter 15 Connect to External Database",
    "Date": 1746093654
}
```

## Retrieval Mechanism

The retrieval stage aims to find the most relevant knowledge entries from the knowledge base for user questions. We adopt a multi-channel hybrid retrieval strategy combined with RRF (Reciprocal Rank Fusion) algorithm for fusion ranking, ensuring relevance and diversity of returned results.

### Hybrid Retrieval Strategy

We employ two mainstream retrieval methods:

-   **Sparse Retrieval (BM25)**: Based on inverted index and keyword frequency, suitable for queries with clear keywords;
-   **Dense Retrieval (Dense Vector)**: Based on semantic vectors, suitable for fuzzy semantic understanding and complex expressions.

Each retrieval path independently obtains TopK=40 results, and finally uses RRF algorithm for fusion ranking, selecting the final TopK=8 optimal results to return.

Retrieval input path as follows:

```
UserInput → [Question(BM25 & Dense), Answer(BM25 & Dense)]{TopK=40} → RRF Fusion Ranking → Hits{TopK=8}
```

We simultaneously retrieve both question and answer fields of QAs to improve overall recall rate. For example, if a user's question expression leans toward answer content, it can still be correctly matched and returned.

Currently, no time decay factor is introduced because multiple versions of product documents coexist, and users may still need information from older versions.

## Generation Mechanism

In the generation stage, the system generates natural and fluent Chinese answers based on retrieved relevant knowledge combined with large language model capabilities.

### Input Structure

The system receives the following two main inputs:

-   User question (User Input)
-   Retrieval results (Hits from Retrieval)

These pieces of information are integrated into prompts and input to large language models for reasoning and answer generation.

### Prompt Template Example

```python
"""
You are conversing with users. Please comprehensively refer to the context and the user questions and knowledge base retrieval results below to answer user questions. Attach document links when answering.
## User Question
{keyword}

## Knowledge Base Retrieval Results
{hits_text}
"""
```

### Reasoning Mode

In addition to direct answer output, we also support "reasoning mode," where reasoning-type LLMs explicitly output intermediate reasoning processes, enhancing user trust and transparency in answers.

### Multi-turn Q&A Support

The system supports multi-turn conversation scenarios and can automatically identify what users really want to ask based on historical conversation context.

Implementation process as follows:

```
Historical Conversation → [LLM Prompt] → Rewritten Question → [Rewritten Question + Retrieval Results] → [LLM Prompt] → Generate Final Answer
```

Guide model to identify user intent through the following prompt:

```python
"""
You are a question generator. You need to identify the question users want to query from the following conversation and directly output that text, which will be used to retrieve relevant knowledge in the knowledge base.
## Conversation Content
{contents}
"""
```

## Summary

Through detailed design and implementation of the above technical architecture, we built a complete RAG knowledge retrieval and Q&A system based on QA pre-generation. From document parsing, QA pair generation, vector index construction, to multi-path hybrid retrieval and large model-based answer generation, all modules work collaboratively to achieve high-quality knowledge service output.

Throughout the entire process, we not only introduced advanced text processing and semantic understanding technologies but also significantly improved system accuracy, robustness, and practicality through Prefix mechanisms, Full Answer extensions, RRF fusion ranking, and other methods.

## Looking Forward to the Next Stage: Engineering Implementation Solution

After completing the design and validation of core functions, the next step will focus on the **engineering implementation solution** of this system, ensuring its availability, stability, and scalability in actual production environments.

In the "Engineering Solution" chapter, the following content will be introduced in detail:

### 1. System Deployment Architecture

-   Overall system structure diagram (including knowledge base construction module, retrieval service, generation service, LLM middleware, etc.)
-   Call relationships and data flow between components
-   Microservice splitting and containerized deployment recommendations

### 2. Core Component Description

-   **Knowledge Retrieval and Q&A Service**: Vector retrieval based on Qdrant + MySQL metadata auxiliary queries
-   **Server Application**: Provides unified API interfaces externally, coordinates retrieval and generation processes
-   **Client Application**: Intelligent Q&A components integrated into product UI
-   **ETL Application**: Scheduled task-driven QA extraction and index update module
-   **Third-party LLM Service Integration**: Such as Tongyi Qianwen, DeepSeek, etc., supporting flexible configuration and switching

### 3. Performance Optimization Strategies

-   Asynchronous processing and caching mechanisms (such as Redis caching high-frequency question results)
-   Vector index preloading and memory mapping optimization
-   Load balancing design for retrieval and generation tasks

### 4. Rate Limiting and Fault Tolerance Mechanisms

-   Request frequency control (Rate Limiting) and token bucket algorithm implementation
-   LLM call failure retry, timeout circuit breaker and degradation strategies
-   Error log collection and monitoring alert system integration

### 5. User Experience Enhancement Measures

-   Response latency optimization (such as preloading, asynchronous loading of partial context)
-   Multi-turn conversation state management and intent recognition optimization
-   Visual feedback mechanisms (users can rate answer quality or provide corrections)
