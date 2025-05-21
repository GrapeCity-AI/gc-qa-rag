# GC-QA-RAG

[中文版](./README.md) | English Version

![license](https://img.shields.io/badge/license-MIT-blue)
![RAG](https://img.shields.io/badge/tech-RAG-important)
![Enterprise](https://img.shields.io/badge/validated-Enterprise-success)

🌟 **Core Value**

-   **QA Pre-generation Technology**  
    Adopts an innovative Q&A pair generation approach that constructs knowledge bases more accurately compared to traditional text segmentation techniques, significantly improving retrieval and question-answering effectiveness.
-   **Enterprise Scenario Validation**  
    Successfully deployed in real business scenarios, enabling seamless upgrades from traditional search to intelligent search with noticeable improvements in user acceptance and satisfaction.
-   **Open-Source Practice Support**  
    Provides comprehensive technical tutorials and open-source code to help developers quickly build high-quality enterprise AI knowledge base systems that are easy to implement.

## Overview

GC-QA-RAG is a Retrieval-Augmented Generation (RAG) system designed for GrapeCity's product ecosystem (including products like Huozige, WYN, SpreadJS, and GCExcel). The system enhances knowledge management efficiency and user support experience through intelligent document processing, efficient knowledge retrieval, and precise Q&A capabilities.

This system innovatively employs QA pre-generation technology, overcoming several limitations of traditional text segmentation methods in knowledge base construction. Practical validation shows that this technical solution significantly improves retrieval effectiveness, offering new insights for RAG technology practices.

Staying true to its "Empower Developers" philosophy, GrapeCity has open-sourced the complete GC-QA-RAG project:

-   For beginners, we provide detailed getting-started guides to help quickly master QA-RAG system construction.
-   For developers facing challenges with traditional architectures, our design documentation serves as a reference to optimize and upgrade existing knowledge bases.

This project also shares GrapeCity's practical experience in RAG knowledge base product design, aiming to provide valuable references for related fields in product and technical exploration.

![alt text](./docs/image-1.png)

## Project Background

As an enterprise solution provider, GrapeCity has accumulated a large user base for its products. In daily usage, users need quick access to accurate product information, but existing help documentation and technical communities face the following challenges:

-   Content is scattered across multiple platforms (approximately 4,000 documents, 2,000 tutorial posts, and 50,000 topic threads).
-   Traditional keyword search yields limited results, struggling to meet precise query needs.

Leveraging AI large model technology, we developed the GC-QA-RAG system to:

-   Provide smarter, more efficient product Q&A services.
-   Optimize technical support processes and improve service efficiency.

> Learn more in [Project Background](./docs/0-项目概述/1_项目背景.md).

## Product Design

GC-QA-RAG adopts a hybrid design of "traditional search interface + intelligent Q&A," combining the efficiency of search engines with the intelligence of AI. Through in-depth evaluation of conversational AI assistants, we found that traditional search interfaces better meet users' core needs for information retrieval efficiency, while the smart answer area provides an AI-enhanced interactive experience.

![alt text](./docs/image-2.png)

> Learn more in [Product Design](./docs/0-项目概述/2_产品设计.md).

### Core Features

-   **Dual-Page Structure**: A clean Home page focuses on the search entry, while the Search page displays smart answers and categorized results.
-   **Intelligent Q&A System**: Supports typewriter-style word-by-word output and follow-up questions for limited multi-turn conversations.
-   **Optimized Search Results**:
    -   Four tab categories (All/Help Docs/Support Center/Tutorials).
    -   Pre-generated detailed answers with "Expand for more" options.
    -   Pagination-free design for improved browsing efficiency.
-   **Enhanced Interactions**:
    -   Answer quality feedback (Helpful/Unhelpful).
    -   One-click text/image copying.
    -   Real-time display of result counts by category.

### User Experience

The product features a clear interface hierarchy and intelligent interaction design, maintaining search efficiency while offering AI-enhanced functionality. The default single-search mode ensures fast responses, follow-up questions cater to deeper exploration, and visual context management helps users maintain operational awareness. This balanced design allows users to quickly access core information while enabling deeper AI interactions as needed.

## Technical Architecture

GC-QA-RAG adopts a three-layer architecture for clarity, efficiency, and scalability:

### Construction Layer - ETL

-   Document parsing: Supports multiple document types (product manuals, forum posts, etc.).
-   QA generation: Automatically generates Q&A pairs from document content.
-   Vectorization: Converts text into high-dimensional vectors for semantic retrieval.
-   Indexing: Builds efficient retrieval indexes and payloads.

### Retrieval Layer - Retrieval

-   Query rewriting: Optimizes user queries for better retrieval accuracy.
-   Hybrid retrieval: Combines keyword and semantic search.
-   RRF ranking: Optimizes results with relevance ranking algorithms.
-   Result fusion: Integrates multi-source retrieval results.

### Generation Layer - Generation

-   Q&A mode: Connects to text-based large models for direct answers.
-   Reasoning mode: Uses inference models for "think-then-answer" responses.
-   Multi-turn dialogue: Supports context-aware continuous conversations.
-   Answer optimization: Ensures accuracy and readability.

> Learn more in [Technical Architecture](./docs/0-项目概述/3_技术架构.md).

## Technical Challenges

In building an enterprise-grade RAG knowledge base system, we faced fundamental challenges in knowledge representation. These stem from the inherent spatiotemporal characteristics of knowledge, which present significant difficulties at the current stage of AI technology development.

### Spatial Semantic Ambiguity

**Issue**:  
Naming conflicts exist across different product modules. For example, in Huozige's low-code platform:

-   "Pivot Table" in the Page module.
-   "Pivot Table" in the Report module.
-   "Pivot Table" in the Table Report module.
-   Excel's "Pivot Table" (internal model knowledge).

**Impact**:  
Such conflicts confuse technical support staff and pose challenges for AI semantic understanding.

### Temporal Version Management

**Issue**:  
Feature variations exist across versions, such as:

-   Multiple version documents for a single feature in the knowledge base.
-   Users may still use older versions and need specific version details.

**Impact**:  
Version differences complicate accurate matching of features in users' actual environments, increasing retrieval difficulty.

## Implementation Results

GC-QA-RAG has achieved encouraging results in real business scenarios:

-   **User Adoption & Retention**  
    Post-launch, user visits grew steadily and stabilized, indicating a solid user base and habitual usage. Retention data reflects high engagement, with many users adopting the system for daily Q&A.

-   **Continuous Optimization**  
    A robust feedback mechanism collects input from end-users and support teams, guiding iterative improvements.

-   **User Recognition**  
    The system earned high praise, with its innovative approach attracting developer interest. Technical principles became a hot topic for client discussions, with several expressing intent to adopt similar solutions.

-   **Business Value**  
    The system significantly improved support efficiency and self-service capabilities. Knowledge access innovations led to measurable process optimizations, validated by positive user feedback.

These outcomes validate the product and technical approach while laying a foundation for future growth. We believe the QA pre-generation method holds broad relevance for document-based knowledge bases. We remain committed to open collaboration with users and developers to advance this technology.

> Learn more in [Implementation Results](./docs/0-项目概述/5_落地效果.md).

## License

MIT
