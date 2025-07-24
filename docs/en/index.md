# GC-QA-RAG

![license](https://img.shields.io/badge/license-MIT-blue)
![RAG](https://img.shields.io/badge/tech-RAG-important)
![Enterprise](https://img.shields.io/badge/validated-Enterprise-success)

🌟 **Core Values**

-   **QA Pre-generation Technology**  
    Adopts innovative question-answer pair generation methods. Compared to traditional text chunking techniques, it can build knowledge bases more precisely and significantly improve retrieval and Q&A effectiveness.
-   **Enterprise-level Scenario Validation**  
    Has been deployed and applied in real business scenarios, achieving seamless upgrade from traditional search to intelligent search, with significantly improved user acceptance and satisfaction.
-   **Open Source Practice Support**  
    Provides complete technical tutorials and open source code to help developers quickly build high-quality enterprise-level AI knowledge base systems that are easy to deploy.

## Overview

GC-QA-RAG is a Retrieval Augmented Generation (RAG) system designed for GrapeCity's product ecosystem (including Forguncy, Wyn, SpreadJS, and GCExcel, etc.). Through intelligent document processing, efficient knowledge retrieval, and precise Q&A capabilities, this system effectively improves knowledge management efficiency and user support experience.

This system innovatively adopts QA pre-generation technology, overcoming several limitations of traditional text chunking methods in knowledge base construction. Through practical validation, this technical approach can significantly improve retrieval effectiveness and provide new insights for technical practices in the RAG field.

GrapeCity, adhering to the philosophy of "empowering developers", now completely open-sources the GC-QA-RAG project:

-   For beginners, we provide detailed getting-started guides to help you quickly master the construction methods of QA-RAG systems
-   For developers facing traditional architecture challenges, our architecture design documentation can provide reference to help optimize and upgrade existing knowledge bases

This project also shares GrapeCity's practical experience in RAG knowledge base product design, hoping to provide valuable reference for product and technical exploration in related fields.

![alt text](image-1.png)

## Project Background

As an enterprise solution provider, GrapeCity has accumulated a large user base. In daily use, users need to quickly obtain accurate product information, but existing help documentation and technical communities face the following challenges:

-   Content is scattered across multiple platforms (approximately 4,000 documents, 2,000 tutorial posts, and 50,000 topic posts)
-   Traditional keyword search has limited effectiveness and cannot meet precise query requirements

Based on AI large model technology, we developed the GC-QA-RAG system, aiming to:

-   Provide more intelligent and efficient product problem-solving services
-   Optimize technical support processes and improve service efficiency

> View [Project Background](./0-project-overview/1_project-background.md) for more details.

## Product Design

GC-QA-RAG adopts a hybrid design pattern of "traditional search interface + intelligent Q&A", aiming to combine the efficiency of search engines with the intelligent capabilities of AI. After in-depth evaluation of conversational AI assistants, we found that traditional search interfaces better meet users' core needs for information acquisition efficiency, while providing AI-enhanced interactive experience through intelligent answer areas.

![alt text](image-2.png)

> View [Product Design](./0-project-overview/2_product-design.md) for more details.

### Core Features

-   **Dual-page Structure**: Clean Home page focuses on search entry, Search page presents intelligent answers and categorized search results
-   **Intelligent Q&A System**: Supports typewriter effect character-by-character output, provides follow-up functionality for limited multi-turn conversations
-   **Optimized Search Results**:
    -   Four-category tab classification display (All/Help Documents/Help Center/Featured Tutorials)
    -   Pre-generated detailed answers support "expand more" viewing
    -   No pagination design improves browsing efficiency
-   **Interaction Enhancement**:
    -   Answer quality feedback (helpful/not helpful)
    -   One-click copy text/images
    -   Real-time display of result counts for each category

### User Experience

The product provides AI-enhanced functionality while maintaining search efficiency through clear interface hierarchy and intelligent interaction design. The default single-search mode ensures response speed, follow-up functionality meets deep exploration needs, and visual context management helps users maintain operational awareness. This balanced design allows users to quickly obtain core information while enabling deeper intelligent interaction as needed.

## Technical Architecture

GC-QA-RAG adopts a three-tier architecture design to ensure the system is clear, efficient, and scalable:

### Construction Layer - ETL

-   Document Parsing: Supports various types of documents (product documentation, forum posts, etc.)
-   QA Generation: Automatically generates question-answer pairs based on document content
-   Vectorization: Converts text into high-dimensional vectors to support semantic retrieval
-   Index Construction: Builds efficient retrieval indexes and payloads

### Retrieval Layer - Retrieval

-   Query Rewriting: Optimizes user queries to improve retrieval accuracy
-   Hybrid Retrieval: Combines keyword and semantic retrieval
-   RRF Ranking: Optimizes results based on relevance ranking algorithms
-   Result Fusion: Integrates multi-source retrieval results

### Generation Layer - Generation

-   Q&A Mode: Interfaces with text large models to directly answer user questions
-   Thinking Mode: Interfaces with reasoning large models to think before answering
-   Multi-turn Dialogue: Supports context-related continuous conversations
-   Answer Optimization: Ensures accuracy and readability of responses

> View [Technical Architecture](./0-project-overview/3_technical-architecture.md) for more details.

## Technical Challenges

In building enterprise-level RAG knowledge base systems, we face fundamental challenges in knowledge representation. These challenges mainly stem from the inherent spatiotemporal characteristics of knowledge itself, which present significant difficulty in solving at the current stage of AI technology development.

### Spatial Semantic Ambiguity Issues

**Problem Description**:  
There are functional naming conflicts across different modules in products. Taking the Forguncy low-code platform as an example, the following situations occur in its documentation:

-   "Pivot Table" function in the page module
-   "Pivot Table" function in the report module
-   "Pivot Table" function in the table report module
-   "Pivot Table" function in Excel (large model internal knowledge)

**Impact**:  
This naming conflict not only causes confusion for technical support personnel but also poses significant challenges to AI systems' semantic understanding.

### Temporal Version Management Issues

**Problem Description**:  
The same functionality has feature differences across different versions, typically manifested as:

-   The knowledge base contains documentation for multiple versions of the same functionality
-   Users may still be using older versions and only need to understand feature characteristics of specific versions

**Impact**:  
This version difference makes it complex to accurately match functional characteristics in users' actual environments, increasing the difficulty of knowledge retrieval.

## Implementation Results

The GC-QA-RAG system has achieved encouraging application results in actual business scenarios, mainly reflected in the following aspects:

-   **User Acceptance and Stickiness**  
    After the system went online, user visits showed steady growth and gradually stabilized, indicating that the product has formed a stable user base and usage habits. User retention data reflects high usage stickiness, with many users having adopted the system as a daily tool for problem-solving.

-   **Continuous Product Optimization**  
    We have established a comprehensive user feedback mechanism, regularly collecting usage experiences and improvement suggestions from end users and technical support teams. This valuable practical feedback provides clear direction for system iteration and drives continuous improvement of product functionality.

-   **User Community Recognition**  
    The system has received high praise from the user community, and its underlying technical innovation concepts have also attracted widespread attention from professional developer users. The technical principles and implementation solutions have become hot topics for customer consultation and discussion, with multiple customers and teams expressing interest in leveraging related experience.

-   **Business Value Demonstration**  
    From actual usage effects, the system has significantly improved technical support efficiency and user self-service capabilities. Knowledge acquisition innovation brings perceivable process optimization, and positive user evaluations fully confirm its effectiveness.

These achievements not only validate the feasibility of the product and technical roadmap but also lay a solid foundation for future development. At the same time, we believe that the QA pre-generation solution has universal reference value for document-based knowledge bases. We will continue to maintain an open attitude, working hand-in-hand with the user community and professional developers to jointly promote continuous technological advancement.

> View [Implementation Results](./0-project-overview/5_implementation-results.md) for more details.

## License

MIT
