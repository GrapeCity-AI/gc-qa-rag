"""
QA Enricher - Generates Question-Answer pairs from document chunks.

Uses LLM to generate QA pairs for each chunk, with two strategies:
- Single group: Direct QA generation from full content
- Multi group: Two-step approach (memorize full text, generate per-chunk QA)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_knowledge_service.abstractions.pipelines.steps import (
    IEnricher,
    ProcessingContext,
)
from ai_knowledge_service.abstractions.observability.context import ObservabilityContext
from ai_knowledge_service.implementations.llm.llm_client import LLMClient


@dataclass
class QAPair:
    """A question-answer pair."""
    question: str
    answer: str


@dataclass
class ChunkQA:
    """QA results for a single chunk."""
    chunk_id: str
    summary: str
    qa_pairs: List[QAPair] = field(default_factory=list)


@dataclass
class PromptConfig:
    """Configuration for QA generation prompts."""

    single_group_template: str = """## instruction
我在构建一个检索系统，需要提取下面文档中的知识点，文档为通用文本，需要总结并提炼，然后针对不同的角度各生成一个相似的问题及其答案，问题需要在源文档中找到答案，问题不少于{{QA_Count}}个，使用中文回答。

## output schema
始终以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。

## 要处理的文档
{{Content}}
"""

    multi_group_template1: str = """请记住下面的文本内容，它将对你后续要做的任务有帮助。
{{Content_Full}}
"""

    multi_group_template2: str = """## instruction
我在构建一个知识检索系统，需要提取下面文本片段中的知识点，需要先总结并提炼片段部分的概要，然后针对片段内不同的知识点各生成一个相关的问题及其答案，问题需要在源文档中找到答案，问题不少于{{QA_Count}}个，使用中文回答。

## 输出格式
始终直接以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。

## 文本片段
{{Content_Chunk}}
"""

    assistant_response: str = "好的，我将在后续任务参考上述文本。请告诉我你的具体任务。"
    system_prompt: str = "你是一个乐于解答各种问题的助手。"


class QAEnricher(IEnricher):
    """
    QA Enricher - Generates Question-Answer pairs from document chunks.

    Uses LLM to generate relevant QA pairs that can be used for:
    - Training data generation
    - Search enhancement
    - Knowledge extraction

    Supports two strategies:
    - Single group: For documents with 1 chunk
    - Multi group: For documents with multiple chunks (uses context)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the enricher.

        Args:
            llm_client: LLM client for generating QA pairs.
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._llm_client = llm_client
        self._prompt_config = PromptConfig()
        self._config: Dict[str, Any] = {}

    @property
    def step_type(self) -> str:
        """Get the step type identifier."""
        return "qa_enricher"

    @property
    def enrichment_type(self) -> str:
        """Get the type of enrichment produced."""
        return "qa"

    @property
    def requires_chunks(self) -> bool:
        """Check if this enricher requires chunks."""
        return True

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the enricher.

        Config options:
        - min_qa_count: int - Minimum QA pairs per chunk (default: 3)
        - max_qa_count: int - Maximum QA pairs per chunk (default: 10)
        - multi_chunk_threshold: int - Chunks needed for multi-group strategy (default: 2)
        - prompts: dict - Custom prompt templates
        """
        self._config = config

        # Update prompts if provided
        prompts = config.get("prompts", {})
        if "single_group_template" in prompts:
            self._prompt_config.single_group_template = prompts["single_group_template"]
        if "multi_group_template1" in prompts:
            self._prompt_config.multi_group_template1 = prompts["multi_group_template1"]
        if "multi_group_template2" in prompts:
            self._prompt_config.multi_group_template2 = prompts["multi_group_template2"]

        self._logger.debug(f"Configured with: {config}")

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Generate QA pairs for each chunk.

        Args:
            context: Processing context with chunks.
            observability: Observability context for metrics/tracing.

        Returns:
            Updated context with QA enrichments.
        """
        if context.should_skip:
            return context

        if context.chunks is None or len(context.chunks) == 0:
            context.add_error(
                step=self.step_type,
                error_type="MissingInput",
                message="No chunks available for QA generation",
                recoverable=True,
            )
            context.mark_skip("No chunks")
            return context

        try:
            # Get full document text for context
            full_text = ""
            if context.parsed_document:
                full_text = context.parsed_document.full_text

            # Choose strategy based on chunk count
            multi_chunk_threshold = self._config.get("multi_chunk_threshold", 2)

            if len(context.chunks) >= multi_chunk_threshold:
                qa_results = self._generate_multi_group_qa(context.chunks, full_text)
            else:
                qa_results = self._generate_single_group_qa(context.chunks, full_text)

            # Store results in enrichments
            context.set_enrichment(
                self.enrichment_type,
                {
                    "chunk_qa": [self._chunk_qa_to_dict(qa) for qa in qa_results],
                    "total_qa_pairs": sum(len(qa.qa_pairs) for qa in qa_results),
                },
            )

            self._logger.debug(
                f"Generated {sum(len(qa.qa_pairs) for qa in qa_results)} QA pairs "
                f"for {len(context.chunks)} chunks"
            )

        except Exception as e:
            context.add_error(
                step=self.step_type,
                error_type=type(e).__name__,
                message=f"Failed to generate QA pairs: {e}",
                recoverable=True,
            )
            # Don't skip - QA enrichment failure is not fatal
            self._logger.warning(f"QA generation error: {e}")

        return context

    def _generate_single_group_qa(
        self,
        chunks: List,
        full_text: str,
    ) -> List[ChunkQA]:
        """
        Generate QA using single-group strategy.

        Used when there's only one or few chunks.
        """
        results: List[ChunkQA] = []

        for chunk in chunks:
            content = chunk.content
            sentence_count = chunk.metadata.get("sentence_count", 5)

            # Build prompt
            prompt = self._prompt_config.single_group_template.replace(
                "{{QA_Count}}", str(max(3, sentence_count))
            ).replace("{{Content}}", content)

            # Generate QA
            try:
                response = self._llm_client.chat(prompt)
                qa_object = self._extract_qa_object(response)

                results.append(
                    ChunkQA(
                        chunk_id=chunk.id,
                        summary=qa_object.get("Summary", ""),
                        qa_pairs=self._extract_qa_pairs(qa_object.get("PossibleQA", [])),
                    )
                )
            except Exception as e:
                self._logger.warning(f"Failed to generate QA for chunk {chunk.id}: {e}")
                results.append(
                    ChunkQA(chunk_id=chunk.id, summary="", qa_pairs=[])
                )

        return results

    def _generate_multi_group_qa(
        self,
        chunks: List,
        full_text: str,
    ) -> List[ChunkQA]:
        """
        Generate QA using multi-group strategy.

        First sends full context to LLM, then generates QA for each chunk.
        This helps maintain consistency across chunks.
        """
        results: List[ChunkQA] = []

        for chunk in chunks:
            sentence_count = chunk.metadata.get("sentence_count", 5)

            # Build messages for context-aware generation
            messages = [
                {"role": "system", "content": self._prompt_config.system_prompt},
                {
                    "role": "user",
                    "content": self._prompt_config.multi_group_template1.replace(
                        "{{Content_Full}}", full_text
                    ),
                },
                {"role": "assistant", "content": self._prompt_config.assistant_response},
                {
                    "role": "user",
                    "content": self._prompt_config.multi_group_template2.replace(
                        "{{QA_Count}}", str(max(3, sentence_count))
                    ).replace("{{Content_Chunk}}", chunk.content),
                },
            ]

            # Generate QA
            try:
                response = self._llm_client.chat_with_messages(messages)
                qa_object = self._extract_qa_object(response)

                results.append(
                    ChunkQA(
                        chunk_id=chunk.id,
                        summary=qa_object.get("Summary", ""),
                        qa_pairs=self._extract_qa_pairs(qa_object.get("PossibleQA", [])),
                    )
                )
            except Exception as e:
                self._logger.warning(f"Failed to generate QA for chunk {chunk.id}: {e}")
                results.append(
                    ChunkQA(chunk_id=chunk.id, summary="", qa_pairs=[])
                )

        return results

    def _extract_qa_object(self, response: str) -> Dict[str, Any]:
        """
        Extract QA object from LLM response.

        Handles various response formats including markdown code blocks.
        """
        # Try to find JSON in the response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            # Find the end of the code block
            lines = response.split("\n")
            # Skip first line (```json) and last line (```)
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block or (not line.startswith("```")):
                    json_lines.append(line)
            response = "\n".join(json_lines)

        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to find JSON object in response
        match = re.search(r'\{[^{}]*"Summary"[^{}]*"PossibleQA"[^{}]*\[.*?\]\s*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Return empty structure
        self._logger.warning(f"Could not parse QA response: {response[:200]}")
        return {"Summary": "", "PossibleQA": []}

    def _extract_qa_pairs(self, possible_qa: Any) -> List[QAPair]:
        """
        Extract QA pairs from LLM response with defensive handling.

        Handles various malformed formats from LLM responses.
        """
        if not isinstance(possible_qa, list):
            self._logger.warning(f"PossibleQA is not a list: {type(possible_qa)}")
            return []

        qa_pairs = []
        for item in possible_qa:
            if isinstance(item, dict):
                question = item.get("Question", "") or item.get("question", "")
                answer = item.get("Answer", "") or item.get("answer", "")
                if question or answer:
                    qa_pairs.append(QAPair(question=str(question), answer=str(answer)))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # Handle [question, answer] format
                qa_pairs.append(QAPair(question=str(item[0]), answer=str(item[1])))
            elif isinstance(item, str):
                # Handle single string (use as both Q and A)
                self._logger.debug(f"Skipping string item in QA list: {item[:50]}")
            else:
                self._logger.warning(f"Unexpected QA item type: {type(item)}")

        return qa_pairs

    def _chunk_qa_to_dict(self, chunk_qa: ChunkQA) -> Dict[str, Any]:
        """Convert ChunkQA to dictionary for serialization."""
        return {
            "chunk_id": chunk_qa.chunk_id,
            "summary": chunk_qa.summary,
            "qa_pairs": [
                {"question": qa.question, "answer": qa.answer}
                for qa in chunk_qa.qa_pairs
            ],
        }
