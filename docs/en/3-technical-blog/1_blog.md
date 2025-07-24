# From Keywords to Intelligent Q&A: How We Built a High-Precision RAG System with QA Pre-generation Technology

In the world of enterprise knowledge services, a precise and efficient search system is the cornerstone for improving user experience and internal efficiency. However, traditional keyword searches often fall into the trap of inaccurate matching. There seems to be an insurmountable "semantic gap" between users' concise questions and the detailed descriptive explanations in documents.

At GrapeCity, as an enterprise-level development tool and solution provider, we face the same challenge. To thoroughly solve user pain points in product learning, solution searching, and problem troubleshooting, we decided to leverage the powerful capabilities of large language models (LLM) to develop an **intelligent product assistant** that can provide instant and accurate Q&A like an expert.

This article will provide a complete retrospective of our journey from 0 to 1, sharing how we fundamentally improved RAG system retrieval accuracy through the innovative approach of **QA pre-generation**, and ultimately built a stable, efficient, and deployable engineering solution.

## I. Challenges and Vision: Why Must We Develop RAG In-house?

Our existing knowledge service system is quite comprehensive, including standardized documentation, GCDN technical community, and a search center supporting cross-platform retrieval. But user feedback is clear: **keyword query accuracy is insufficient**.

With the maturity of LLM and RAG (Retrieval-Augmented Generation) technology, we saw hope. However, existing open-source or commercial solutions were difficult to directly apply for four reasons:

1. **Heterogeneous Content Structure**: The rigorous format of help documents and the free-form nature of forum posts pose huge challenges for universal parsing solutions.
2. **Diverse Technical Pathways**: RAG enhancement strategies are numerous; we needed to find the most suitable technical route for our business.
3. **High-frequency Knowledge Base Updates**: Community content grows daily, requiring efficient incremental update mechanisms.
4. **Autonomous Control**: To achieve flexible feature iteration and controllable operational costs, in-house development was inevitable.

### Core Insight: From "Question ↔ Answer" to "Question ↔ Question"

Traditional RAG retrieval logic involves matching user **questions** against **text paragraphs (answers)** in the knowledge base. This has a fundamental misalignment:

-   **User Questions (Interrogative Sentences)**: "How to set responsive layout?"
-   **Document Answers (Declarative Sentences)**: "Find layout setting options in the property panel, supporting three modes..."

This difference in sentence structure and intent naturally limits semantic matching accuracy.

During exploration, we discovered that LLM's powerful information extraction capabilities could help us think differently. What if we could have LLM pre-read all documents and generate one or more **"standard questions"** for each knowledge point? This way, the retrieval process would change from "question-answer matching" to **"question-question matching"**.

-   **Traditional Approach**: User question ↔ Answer text (semantic misalignment)
-   **Improved Approach**: User question ↔ **Preset question** (semantic alignment)

This idea became the technical foundation of our entire project. Instead of simply segmenting documents into paragraphs, we process them into structured **QA pairs (Question-Answer Pairs)**. One document can be broken down into multiple knowledge points, generating multiple QA pairs - this is the core of our **"QA Pre-generation RAG"** solution.

## II. Technical Architecture: Layered Analysis of Our QA-RAG System

Our system follows the classic three-stage architecture of ETL, retrieval, and generation, but each phase incorporates targeted optimizations.

### Stage One: Knowledge Construction (ETL) - Carefully Crafted Knowledge "Raw Materials"

This is the foundation of the entire system. Our goal is to transform tens of thousands of documents and posts into high-quality, retrievable QA pairs.

**1. QA Slicing**
We abandoned traditional length or symbol-based slicing methods, directly using LLM to transform unstructured document content into structured QA pairs. This ensures each knowledge unit focuses on an independent, clear knowledge point.

**2. Text Embedding Enhancement**
To make retrieval more precise, we not only vectorize QA text but also introduce various enhancement mechanisms:

-   **Summary (Context Summary)**: Generate an additional summary of the containing document for each QA pair. This helps generation models better understand context when answering.
-   **Full Answer (Extended Answer)**: Generate a more detailed answer version for QA pairs from help documents. Users can click "expand" on the search results page to view without jumping, creating a smoother experience.
-   **Prefix Mechanism**: To resolve similar questions that might exist across different product documents (such as "data connection" features in various products), we add category and title prefixes to questions during vectorization.

```
    #### Example
    [Category/Title] + Question
    [Forguncy/Connect to External Database/Connect to Oracle] What needs to be done before connecting to Oracle database?
```

    This effectively distinguishes similar questions in different scenarios, avoiding "semantic space aliasing."

Finally, each knowledge point contains rich metadata and multi-dimensional vectors, laying the foundation for high-quality retrieval.

**Payload Example:**

```json
{
    "Question": "What needs to be done before connecting to Oracle database?",
    "Answer": "Oracle needs to be configured first, and only after configuration is complete can you connect to Oracle.",
    "FullAnswer": "# Preparation for Connecting to Oracle Database...",
    "Summary": "This document introduces how to connect to Oracle database...",
    "Url": "https://...",
    "Title": "Connect to Oracle",
    "Category": "Forguncy Chinese Documentation/Chapter 15 Connect to External Database",
    "Date": 1746093654
}
```

### Stage Two: Retrieval - Multi-path Recall and Intelligent Ranking

We adopt a **Hybrid Search** strategy, using both approaches to ensure recall rate and relevance.

1. **Sparse Retrieval (BM25)**: Based on keyword matching, fast and efficient.
2. **Dense Retrieval (Dense Vector)**: Based on semantic understanding, excels at handling fuzzy and complex queries.

We found that **retrieving both Question and Answer fields simultaneously** works best. Because user questions sometimes more closely resemble the answer's expression. Both retrieval paths recall Top 40 results respectively, then use **RRF (Reciprocal Rank Fusion) algorithm** for fusion ranking, ultimately selecting Top 8 optimal results for the generation stage.

### Stage Three: Generation - Reliable, Traceable Intelligent Answers

The generation stage aims to provide natural and accurate answers based on retrieval results.

**1. Refined Prompts**
We combine user questions with retrieved knowledge fragments into clear prompts, guiding LLM to generate answers.

```python
"""
You are conversing with users. Please comprehensively refer to the context as well as the user questions and knowledge base retrieval results below to answer user questions. Attach document links when answering.
## User Question
{keyword}

## Knowledge Base Retrieval Results
{hits_text}
"""
```

**2. Elegant Multi-turn Conversation Handling**
Instead of using cumbersome full historical record input, we use a **Question Rewriting** model to intelligently identify the **core question users really want to ask** from conversation history, then use this rewritten question for retrieval. This ensures both contextual coherence and efficiency.

## III. From Blueprint to Reality: Product Design and Engineering Implementation

Good technology needs good product design to carry it. We initially envisioned a ChatGPT-like conversational assistant, but after deep consideration, we chose a **"traditional search interface + intelligent Q&A"** hybrid mode.

**Why abandon pure conversational mode?**

1. **Information Priority**: For users, **search result lists** are the highest-value information source; AI's summary answers are auxiliary. Pure conversational interfaces would reverse priorities.
2. **Context Confusion**: Multi-turn conversations easily confuse LLM when handling cross-domain questions, and response speed slows with increasing turns, creating uncertainty for users.

**Final Design Solution:**

-   **Interface**: Home page focuses on search input; search results page displays **intelligent answer area** alongside **categorized result lists** (help documents, help center, topic tutorials) with clear priorities.
-   **Experience**: AI answers use typewriter effect for instant generation; search results display directly without pagination; provides "helpful/not helpful," "copy," "follow-up" and other quick operations.
-   **Balance**: Default single search ensures efficiency while "follow-up" function meets deep exploration needs. Each follow-up adds a new "question-answer-results" module to the page with clear visible context.

**Engineering Guarantees:**

To ensure stable system operation, we built a complete engineering solution:

-   **Deployment Architecture**: Using microservice principles, separating knowledge base construction (ETL) from Q&A services. Core components include Qdrant vector database, Server application, Client frontend, and unified LLM integration layer.
-   **Request Rate Limiting**: Using **moving window algorithm** for fine-grained rate limiting across different interfaces and time dimensions (minute/hour/day), preventing system overload from sudden traffic.
-   **Performance Targets**: Set clear performance metrics (e.g., retrieval response < 2s) and established comprehensive monitoring and alerting systems to ensure high availability.

## IV. Results and Value: Changes Brought by the Intelligent Assistant

After system launch, results were significant, bringing tangible value to users, technical support teams, and the company.

**1. Dramatically Improved User and Technical Support Efficiency**

-   User self-service capabilities significantly enhanced; common questions get instant answers, reducing average problem resolution time from hours to minutes.
-   Technical support teams freed from repetitive Q&A to focus on more complex issues.

**2. Significantly Optimized Operational Costs**

-   Reduced labor and training costs; knowledge managed uniformly in structured QA pair format with extremely high update and maintenance efficiency.

**3. Sharing Our Technical Exploration**

-   We successfully validated the enormous potential of QA-RAG technical approaches in enterprise-level knowledge services.
-   This complete practice from product design to engineering implementation provides a referenceable, reusable solution for the industry.

## V. Summary and Outlook

Starting from a simple idea to improve search accuracy, we experienced a complete journey from technology selection and architectural innovation to product refinement and engineering implementation. **QA pre-generation** as a core approach has proven to be an effective weapon for solving semantic misalignment problems in enterprise-level RAG scenarios.

Of course, this is just the beginning. In the future, we will continue expanding knowledge base breadth (such as API documentation, video tutorials), optimizing algorithmic depth, and continuously iterating product experience based on user feedback.

## We believe that through deep integration of technology and business, intelligent Q&A systems will become a solid bridge connecting users with product knowledge, helping enterprises build a sustainably evolving knowledge hub.

For more details, please visit GrapeCity's official website or follow our technical community.
