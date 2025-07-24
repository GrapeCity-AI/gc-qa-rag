# Project Background

## 1. Current Status and Challenges

As an enterprise-level development tool and solution provider, GrapeCity has established a comprehensive knowledge service system, including:

-   **Standardized Documentation**: Product help documents, API documentation
-   **Community Resources**: GCDN technical community (including help center, topic tutorials, technical discussions, and other sub-sections)
-   **Search Platform**: Existing "GrapeCity Search Center" supports cross-platform content retrieval (official website, blogs, community, videos, etc.)

Although the existing system supports fuzzy search and exact search, the accuracy of keyword queries is insufficient, leading to poor user experience. This is specifically manifested in the following typical scenarios:

-   **Product Learning**: Users have difficulty precisely locating function descriptions in help documents
-   **Solution Search**: Users cannot efficiently find solutions that match their problems
-   **Problem Deduplication**: Technical support personnel find it difficult to quickly confirm whether a problem already has a solution

## 2. Technical Exploration

With the rapid development of artificial intelligence technology, especially large language model technology, we envisioned a **Product Intelligent Assistant** that could provide instant and accurate product Q&A services to users like an expert. This vision is based on the following technical research results:

-   **LLM Advantages**: Possess powerful natural language understanding and extensive knowledge coverage capabilities
-   **RAG Value**: By introducing external knowledge sources, effectively supplement LLM knowledge limitations and improve Q&A accuracy

### Necessity of Self-developed RAG

During the technology selection process, we evaluated multiple open-source and commercial RAG solutions and found that they could not directly adapt to our data structure and business requirements. Additionally, in order to deeply master cutting-edge technology, accumulate R&D experience, and achieve flexible expansion, we decided to independently develop a RAG system. The main reasons include:

1. **Significant Content Structure Differences**  
   Help documents and forum posts have significantly different formats, making it difficult for universal solutions to adapt.
2. **Rich RAG Technical Pathways**  
   Different enhancement strategies need to be verified one by one to select the most suitable technical route.
3. **Frequent Dynamic Updates**  
   Forum content is continuously updated, requiring research into efficient incremental update mechanisms to ensure knowledge base timeliness.
4. **Flexible Product Design Adaptation**  
   Self-developed solutions can better fit actual scenarios and support future feature evolution.
5. **Controllable Performance and Maintenance**  
   Self-built systems have advantages in deployment efficiency and long-term operation and maintenance costs.

### Exploration of QA Pre-generation Technology

In traditional RAG solutions, users' original questions are directly matched and retrieved with text paragraphs in documents. This approach has a fundamental problem: **user questions** and **text paragraphs as answers** have structural differences in semantic expression, creating misaligned matching situations.

Specifically:

-   User questions are usually concise interrogative sentences (such as "How to set responsive layout?")
-   Answer paragraphs in documents are often descriptive statements (such as "Find layout setting options in the property panel, supporting three modes...")
-   This semantic gap between interrogative and declarative sentences limits the accuracy of direct matching

During our research on large language models, we discovered their excellent **information extraction** capabilities, which can convert knowledge points in natural language text into structured forms. Therefore, we proposed a new approach: **question-to-question matching** — using large language models to generate corresponding "preset questions" for each document section, then performing precise matching between user questions and these preset questions.

-   Traditional approach: User question ↔ Answer text (semantic misalignment)
-   Improved approach: User question ↔ Preset question (semantic consistency)

Furthermore, we process original documents into standard QA pair forms (one question + one answer), where one document can often be broken down into multiple knowledge points, generating multiple QA pairs. After extensive optimization, we successfully achieved this goal and made it adaptable to various types and sizes of documents.

Additionally, we found that when **user questions simultaneously match preset questions and corresponding answers**, the retrieval effect is better. This is because answers contain more information dimensions, especially user input information. Relevant optimization details will be elaborated in the subsequent "Technical Principles" chapter.

## 4. Project Decision

Based on preliminary technical validation results, we formulated a phased implementation plan:

**Short-term Goals** (3-6 months):

-   Build intelligent Q&A systems for four core products: Forguncy, Wyn, SpreadJS, and GcExcel
-   Cover core content from help documents and technical communities

**Long-term Vision**:

-   Establish a sustainably evolving product knowledge hub system
-   Drive continuous system iteration and optimization through user feedback

## Appendix - First Batch of Supported Products

This intelligent assistant initially covers GrapeCity's four core product lines, as follows:

| Product            | Type                              | Core Capabilities                                                  | Official Website                                                              |
| ------------------ | --------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| **Forguncy**       | Low-code Development Platform     | Enterprise application rapid construction, visual development      | [Visit](https://www.grapecity.com.cn/solutions/huozige)                       |
| **Wyn Enterprise** | Embedded Business Intelligence    | Self-service data analysis, multi-dimensional report display       | [Visit](https://www.grapecity.com.cn/solutions/wyn)                           |
| **SpreadJS**       | Spreadsheet Control               | Pure front-end spreadsheet processing, Excel compatibility         | [Visit](https://www.grapecity.com.cn/developer/spreadjs)                      |
| **GcExcel**        | Server-side Spreadsheet Component | High-performance batch document generation, cloud Excel processing | [Visit](https://www.grapecity.com.cn/developer/grapecitydocuments/excel-java) |
