# Document Chunking

This chapter introduces the document chunking principles of the GC-QA-RAG intelligent Q&A system, explaining how to chunk knowledge points from original documents and store them in a vector database.

## 1. Original Approach

Our initial concept was very straightforward: **use the entire document as input and have a large language model automatically generate question-answer pairs (QA Pairs)** to support subsequent knowledge retrieval and Q&A system construction.

```prompt
## Task Requirements
Extract knowledge points from the following document as QA pairs and output in the specified format.
{Content}

## Output Format
[{"Question":"string","Answer":"string"}]
```

However, in practical application, we found this approach had significant limitations, specifically manifested as:

### Short Document Processing Issues

When processing brief texts containing only 1-2 sentences (such as product feature descriptions, API brief descriptions), the model tends to generate Q&A pairs that exceed the scope of the original text, leading to information fabrication. For example, for a simple description like "supports multiple data formats," the model might fabricate specific format lists and other content not mentioned in the original text.

### Long Document Processing Bottlenecks

For long documents like technical whitepapers, the number of Q&A pairs output by the model has an obvious ceiling effect:

-   Stable output range: 10-15 QA pairs
-   Beyond the threshold, issues appear:
    -   Question repetition (same knowledge points with different expressions)
    -   Selective information loss (ignoring important content details)
    -   Answer deviation (over-generalization or supplementing external knowledge)

These limitations directly affected the completeness and accuracy of the knowledge base, prompting us to deeply address two core problems:

1. **Precise Control for Short Documents**:
   How to establish constraint mechanisms to ensure generated Q&A pairs are strictly limited to the scope of original text information, eliminating information fabrication?

2. **Complete Coverage for Long Documents**:
   How to break through quantity limitations and ensure every key detail in long documents can be accurately extracted and converted into Q&A pairs, achieving comprehensive knowledge point coverage without omissions?

## 2. Short Document Processing Strategy: Dynamic Control Based on Sentence Count

For short documents, we propose a strong hypothesis: **each sentence corresponds to an independent knowledge point that can be converted into a QA pair**. Based on this, we designed a method to estimate the number of QAs to generate based on sentence count.

### Core process as follows:

1. Use a Chinese sentence splitter to break the document into a sentence list;
2. Calculate total sentence count `N`;
3. Dynamically set expected generation count `QA_Count = N` and inject it into the prompt;
4. The model generates no fewer than `QA_Count` QA pairs according to explicit instructions.

Example prompt template as follows:

```python
single_group_template = """
Need to generate no fewer than {{QA_Count}} Q&A pairs for the document...
Document content: {{Content}}
"""
```

### Chinese Text Processing Optimization:

Considering that Chinese technical documents may contain code snippets or special symbols (such as "." appearing in variable names), we made the following processing during sentence segmentation:

-   Mainly use "。", "？", "！" etc. as sentence break markers;
-   Preserve statements containing special characters without splitting;
-   Automatically filter blank sentences and invalid paragraphs.

This strategy significantly improved the completeness and accuracy of information extraction for short documents.

## 3. Long Document Processing Solution: Two-stage Memory-Focus Dialogue Mechanism

For long documents, direct truncation leads to information loss, while one-time full-text input easily causes attention dispersion and fragmented generated content. We propose an innovative **two-stage memory-focus dialogue mechanism**.

The core idea is:

> **In the first round of dialogue, simulate "long-term memory" by implanting full-text background into the model; in the second round, send only the current segment, guiding it to focus on local content for QA extraction.**

### Implementation method as follows:

#### First Stage: Knowledge Memory (User Instruction)

```python
multi_group_template1 = "Please remember the following technical document..."
```

#### Second Stage: Focused Generation (User Instruction)

```python
multi_group_template2 = "Extract QA pairs from the current document segment..."
```

#### Construct Complete Dialogue History:

```python
messages = [
    {"role": "user", "content": self.prompt_config.multi_group_template1},   # Full-text memory
    {"role": "assistant", "content": self.prompt_config.assistant_response}, # Response confirmation
    {"role": "user", "content": self.prompt_config.multi_group_template2}    # Local generation
]
```

### Processing Flow Summary:

1. Group the document by sentences (default 10 sentences per group);
2. Execute the above two-stage dialogue for each group;
3. Merge results from all groups to form the final QA library.

This mechanism not only solves the context coverage problem but also improves the model's focus and generation quality on local content.

## 4. Detailed Implementation

### (1) Text Preprocessing Flow

| Step                  | Description                                                                                    |
| --------------------- | ---------------------------------------------------------------------------------------------- |
| HTML Parsing          | Use BeautifulSoup to extract body content from class="main\_\_doc"                             |
| Sentence Segmentation | Segment by Chinese punctuation (periods, question marks, etc.) and filter blank sentences      |
| Dynamic Grouping      | Default 10 sentences per group, merge groups with fewer than 5 sentences to the previous group |

### (2) Unified Output Format

Each group's output is in standardized JSON format with two key fields:

```json
{
  "Summary": "Introduction to Forguncy layout types and characteristics",
  "PossibleQA": [
    {
      "Question": "What layout methods does Forguncy support?",
      "Answer": "Supports three methods: responsive layout, fixed layout, etc."
    },
    ...
  ]
}
```

### (3) JSON Extraction and Error Handling

To handle potential format errors when large models generate JSON (such as unclosed quotes, unmatched brackets, etc.), we designed the `extract_qa_object` function for error tolerance.

1. **Priority JSON Block Extraction**: Try to extract standard JSON content wrapped in ` ```json ... ``` ` from the response;
2. **Force Conversion to JSON Object**: If no JSON content is extracted, treat the entire response as JSON and attempt forced parsing;
3. **Fallback to Regex Extraction on Parse Failure**: Use regular expressions to manually match fields like `"Question"` and `"Answer"` to construct structured output;
4. **Exception Catching**: Use try-except structures to prevent program interruption from model generation failures;

```python
try:
    response = chat_to_llm(prompt)
    return extract_qa_object(response)
except Exception as e:
    logger.error(f"Error generating QA: {e}")
    return {"Summary": "", "PossibleQA": []}
```

(Detailed implementation can be found in the relevant chapters of the development tutorial or project source code.)

## 5. Feature Extensions

Beyond basic QA generation, we further implemented several practical extension features:

### 1. Summary Generation

-   Generate a concise summary for each group;
-   Store in vector database payload field;
-   Improve model understanding efficiency and document recommendation accuracy.

### 2. Answer Extension (Full Answer)

-   Generate more detailed explanations for key QA pairs;
-   Also stored in vector database payload field;
-   Used for frontend display or assisting models in answering complex questions.

### 3. Synonym Question Augmentation (Question Variants)

-   Generate multiple different expressions for each question;
-   Significantly improve retrieval system recall rate;
-   Suitable for scenarios with diverse user questioning patterns.

## 6. Engineering Recommendations

| Dimension       | Recommended Value                                |
| --------------- | ------------------------------------------------ |
| Model Selection | At least 70B parameter scale (e.g., Qwen2.5-72B) |
| Temperature     | 0.7 (balance creativity and rigor)               |
| Top-P           | 0.7 (control output diversity)                   |
| Maximum Tokens  | ≥2048 (ensure output length)                     |

> ⚠️ Note: Small models have limited knowledge scope and are prone to hallucinations. It's recommended to include manual spot-checking mechanisms in QA quality assessment to evaluate technical limitations. This project's overall error rate is controlled at 5%~10% for reference.

## 7. Applicability and Scalability Analysis

This solution has good universality and adaptability, suitable for:

-   **Wide Document Types**: Technical documents, legal regulations, knowledge encyclopedias, FAQ pages, etc.;
-   **Good Scale Flexibility**: Limited by model maximum context length (typically 8k~128k tokens);
-   **Easy Adaptation and Extension**: Support different business needs by modifying prompt templates.

## 8. Practical Application Example

Here's a complete processing workflow example:

```python
# Input document
doc = "Forguncy supports three layout methods...Responsive layout automatically adjusts according to device dimensions...Fixed layout maintains pixel-level precision..."

# Group processing
groups = split_text_into_sentence_groups(doc)

# QA generation
generator = QAGenerator()
result = generator.generate_by_groups(doc, groups)

# Output result
{
    "Summary": "Introduction to Forguncy layout types and characteristics",
    "PossibleQA": [
        {
            "Question": "What layout methods does Forguncy support?",
            "Answer": "Supports three methods: responsive layout, fixed layout, etc."
        },
        {
            "Question": "What are the characteristics of responsive layout?",
            "Answer": "Automatically adjusts according to device dimensions"
        }
    ]
}
```

This solution integrates multiple key technologies including **sentence-level processing, context memory, structured output, error control, and feature extensions**, providing good universality and engineering practical value, effectively improving the accuracy and user experience of knowledge retrieval Q&A.

## 9. Subsequent Content

After introducing the complete QA pre-generation chunking solution, we now have the capability to produce high-quality structured knowledge corpora. Next, we will enter the core component of the RAG knowledge base retrieval system—**"Vector Retrieval Technical Solution"**.

In this section, we will focus on:

-   How to build a knowledge base based on generated QAs, i.e., how to vectorize QA pairs;
-   What key metadata (such as summaries, answer extensions, tags, etc.) is stored in vector payload fields to enhance retrieval and Q&A capabilities;
-   How the retrieval stage combines keyword matching with semantic similarity to implement **Hybrid Search**, further improving recall rate and accuracy.

Please see the detailed analysis in the next chapter.
