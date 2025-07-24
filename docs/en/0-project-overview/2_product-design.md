# Product Design

During the product design process, we went through multiple iterations and optimizations, ultimately determining a design solution that balances user experience and technical feasibility. Below we introduce our design philosophy.

## Initial Concept: Conversational AI Assistant

Initially, we planned to develop a conversational AI assistant named "GrapeCity AI Assistant." This format is closer to users' daily usage habits, such as the interactive methods of ChatGPT web version or WeChat instant messaging tools. However, after in-depth research, we discovered some significant shortcomings of conversational assistants:

1. **Information Display Priority Issues**  
   In conversational interfaces, AI answers are the main content, while search results are usually placed in sidebars or collapsed areas. However, for users, the truly high-value content is the search results themselves, with AI answers serving more as summaries and quick previews. If users need to wait for AI to generate answers, they may feel it's time-consuming and inefficient, especially when answers deviate, which would further deteriorate the experience.

2. **Limitations of Multi-turn Conversation**  
   While multi-turn conversation design seems smooth and natural, it doesn't fully match the current technical status of large models. Large models are more suitable for working within a clear topic scope when processing context. If users ask multiple cross-domain questions in one context, it can easily lead to model confusion and reduced answer quality. Additionally, as conversation turns increase, model response speed gradually slows down, while users may find it difficult to perceive the reasons behind this change. Even with a "new conversation" button, users find it difficult to judge when to switch contexts.

Based on the above issues, we decided to abandon the conversational interface and adopt a traditional search engine interface that better aligns with user search habits while incorporating intelligent Q&A functionality.

## Final Design Solution: Traditional Search Interface + Intelligent Q&A

We ultimately chose a hybrid design solution that combines the efficiency of traditional search engines with the intelligent characteristics of AI Q&A. The following are specific design details:

### 1. Interface Structure

The product interface is divided into two main pages: `Home` and `Search`.

#### **Home Page**

-   **Title**: Centered display of "GrapeCity AI Search".
-   **Product Switcher**: Located below the title, supports users switching between four core products (Forguncy, Wyn, SpreadJS, GcExcel).
-   **Input Box**: A multi-line text box prompting users "Enter your product questions, press Enter to send, Shift+Enter for line break." The bottom right corner has an arrow send button.
-   **Overall Layout**: Elements are centered and arranged intuitively.

#### **Search Page**

-   **Top Navigation**:
    -   Top left displays "GrapeCity AI Search".
    -   Below is the product switcher, consistent with the Home page.
-   **Search Box**: Users trigger search after entering keywords.
-   **Intelligent Answer Area**: Located below the search box, outputting AI answers character by character through typewriter effect.
-   **Search Results List**: Located below the intelligent answer area, divided into four tabs:
    -   **All**: Shows all relevant search results.
    -   **Help Documents**: Shows QA pairs from product help documentation.
    -   **Help Center**: Shows QA pairs from help posts in the technical community.
    -   **Topic Tutorials**: Shows QA pairs from topic tutorials in the technical community.

### 2. Search Results Optimization

To improve the practicality and usability of search results, we made the following designs:

-   **Tab Quantity Hints**: Each tab's top right corner displays the number of search results in that category. If there are no relevant results, the tab will be grayed out and disabled.
-   **Detailed Answers for Help Documents**: For QA pairs from help documents, we pre-generated more detailed answers using large models in the background. Users can click the "expand more" button after simple answers to view detailed content without needing to jump to original documents for more information.
-   **No Pagination Design**: To simplify user experience, we limited the number of search results and directly displayed all results, avoiding traditional search pagination operations.

### 3. Intelligent Answer Area

The intelligent answer area is the core highlight of the entire design. The following are its specific functions and interaction details:

-   **Loading State**:
    -   When the large model hasn't generated an answer, it displays a horizontal bar text area with loading animation on the left and a "stop generation" button in the top right corner. The button position is fixed above the text growth direction, ensuring users can accurately locate it.
-   **Answer Generation**:
    -   When the large model starts outputting text, the loading animation disappears, and users can see character-by-character generated answer content. Users can choose to wait for completion or click "stop generation" at any time to terminate output.
-   **Action Buttons**:
    -   After answer generation is complete, a group of action buttons appears below, including:
        -   **Helpful**: User feedback that the answer is helpful.
        -   **Not Helpful**: User marks the answer as inaccurate.
        -   **Copy**: Quickly copy answer content.
        -   **Follow-up**: Expands a collapsed multi-line text input box, allowing users to ask follow-up questions in the same context.
        -   **Copy Image**: New feature for quickly capturing images of AI answer content.
    -   Bottom left displays the disclaimer: "The above content is generated by AI for reference only."

### 4. Multi-turn Conversation Support

To balance the needs of multi-turn conversation with single-search efficiency, we adopted the following design:

-   **Follow-up Function**:
    -   A "Follow-up" button is set below the intelligent answer area. When users click it, a collapsed multi-line text input box expands.
    -   After users enter follow-up questions, the system automatically collapses previous answer content and adds new questions, intelligent answer areas, and search result lists vertically.
-   **Context Management**:
    -   Users can view previous questions and answers by scrolling the page, clearly aware they are within a single context.
    -   If users want to switch topics, they simply return to the top input box and enter new keywords to start a fresh search.

# Summary

In summary, we created a simple and efficient product by integrating the advantages of traditional search with intelligent Q&A:

-   **Interface**: Home page focuses on search, search results page displays intelligent answers alongside categorized lists (documents/community/tutorials).
-   **Experience**: AI generates answers character by character, supports follow-up questions and quick operations; search results expand directly without pagination.
-   **Balance**: Default single search ensures efficiency, follow-up function meets deep exploration needs.

This design not only ensures information acquisition efficiency but also achieves intelligent interactive experience, providing users with higher quality information services.
