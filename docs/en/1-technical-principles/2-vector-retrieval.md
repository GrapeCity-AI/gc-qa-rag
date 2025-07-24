# Vector Retrieval

This chapter introduces the core retrieval technology principles of the GC-QA-RAG intelligent Q&A system, including vectorization strategies, hybrid retrieval mechanisms, RRF fusion ranking, and other key implementation details.

## 1. Retrieval Process Overview

The system adopts a typical RAG (Retrieval-Augmented Generation) three-stage architecture. The goal of the retrieval stage is: **When users ask questions, combine keywords with semantic understanding to quickly locate the most relevant knowledge points, providing support for subsequent generation of high-quality answers.**

The retrieval process is as follows:

1. User inputs a question;
2. System vectorizes the question (dense + sparse);
3. Parallel retrieval of "question" and "answer" fields in the knowledge base;
4. Use RRF (Reciprocal Rank Fusion) algorithm to fuse multi-path retrieval results and return TopK optimal answers.

## 2. Hybrid Retrieval Mechanism

### 2.1 Multi-channel Retrieval

The system adopts **Hybrid Search**, utilizing both sparse vectors (BM25) and dense vectors (Dense Embedding) to retrieve "question" and "answer" fields:

-   **Sparse Retrieval (BM25)**: Suitable for queries with clear keywords, strong recall capability;
-   **Dense Retrieval (Dense Vector)**: Based on semantic similarity, suitable for complex expressions and fuzzy queries.

Each retrieval path obtains TopK=40 candidate results.

### 2.2 Retrieval Fields

Each knowledge entry contains four types of vector features:

-   Prefix_Question_Dense
-   Prefix_Answer_Dense
-   Prefix_Question_Sparse
-   Prefix_Answer_Sparse

During retrieval, user questions are matched against both "preset questions" and "answer" fields' dense/sparse vectors, greatly improving recall rate and relevance.

### 2.3 RRF Fusion Ranking

Multi-path retrieval results are fused and ranked through the RRF (Reciprocal Rank Fusion) algorithm, ultimately selecting TopK=8 optimal results to return. RRF effectively balances the advantages of different retrieval channels, improving the diversity and accuracy of final results.

## 3. Retrieval Implementation Details

### 3.1 Vectorization and Querying

-   User questions first generate dense vectors and sparse vectors (such as BM25 weights) through embedding models;
-   During retrieval, four vector paths are used as queries: "question dense", "answer dense", "question sparse", "answer sparse", calling the vector database's (such as Qdrant) multi-path prefetch interface;
-   Retrieval results are fused through RRF, deduplicated, and returned.

### 3.2 Code Implementation Key Points

Taking search.py as an example, the core retrieval logic is as follows:

-   `get_embedding_pair`: Generate dense and sparse vectors for input questions;
-   `search_sementic_hybrid_single`: For a single knowledge base collection, perform prefetch retrieval with four vector paths and fuse ranking through RRF;
-   `search_sementic_hybrid`: Parallel retrieval across all knowledge bases (such as documents, forum Q&A, tutorials), merging results;
-   `distinct_search_hits`: Deduplicate retrieval results to ensure each knowledge point is unique.

### 3.3 Retrieval Process Diagram

```
User Question
   │
   ├─> Generate dense/sparse vectors
   │
   ├─> [Question Dense] ─┐
   ├─> [Answer Dense] ─┼─> Multi-path retrieval (TopK=40)
   ├─> [Question Sparse] ─┤
   └─> [Answer Sparse] ─┘
         │
   └─> RRF fusion ranking → TopK=8
         │
   └─> Return retrieval results
```

## 4. Structure and Usage of Retrieval Results

Each retrieval result contains:

-   Question: Preset question
-   Answer: Standard answer
-   FullAnswer: Detailed explanation
-   Summary: Context summary
-   Url, Title, Category, Date and other metadata

This information is not only used for direct display but also provides rich context for subsequent large model answer generation.

## 5. Technical Advantages and Optimization Points

-   **Multi-path hybrid retrieval**: Balances keyword and semantic understanding, greatly improving recall rate and accuracy;
-   **RRF fusion ranking**: Effectively fuses multi-channel results, improving diversity and relevance;
-   **Prefix mechanism**: Through document category/title prefixes, avoids semantic aliasing and improves retrieval precision;
-   **Efficient deduplication**: Ensures each knowledge point is unique, avoiding interference from duplicate information.

## 6. Summary

This system achieves efficient and precise knowledge retrieval capabilities through multi-channel hybrid retrieval, RRF fusion ranking, and rich vectorization and metadata design, providing a solid foundation for intelligent Q&A systems.
