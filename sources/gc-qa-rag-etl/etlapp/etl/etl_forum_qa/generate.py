import json
import logging
from typing import Dict, Any
from pathlib import Path

from etlapp.common.context import EtlContext
from etlapp.common.file import (
    write_text_to_file,
    ensure_folder_exists,
)
from etlapp.common.format import extract_qa_object
from etlapp.common.hash import get_hash_folder
from etlapp.common.llm import chat_to_llm

# Configure logging
logger = logging.getLogger(__name__)


class ForumQAGenerator:
    """Class for generating QA pairs from forum content."""

    PROMPT_TEMPLATE = """## instruction
我在构建一个检索系统，需要提取下面文档中的知识点，文档主要是产品技术支持论坛的帖子，需要总结并提炼，然后针对不同的角度各生成一个相似的问题及其答案，问题需要在源文档中找到答案，生成多个，使用中文回答。

## output schema
始终以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。   

## 要处理的文档
{{Content}}
"""

    def __init__(self, context: EtlContext):
        """Initialize the generator with context.

        Args:
            context: ETL context containing configuration and paths
        """
        self.context = context
        self.root_path = Path(context.root)
        self.product = context.product
        self.index = context.index

    def _generate_qa(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate QA pairs from content.

        Args:
            content: Content to generate QA pairs from

        Returns:
            Dict containing generated QA pairs
        """
        try:
            main_content = json.dumps(content, ensure_ascii=False)
            prompt = self.PROMPT_TEMPLATE.replace("{{Content}}", main_content)
            response = chat_to_llm(prompt)
            qa_object = extract_qa_object(response)
            return {"Groups": [qa_object]}
        except Exception as e:
            logger.error(f"Error generating QA pairs: {e}")
            return {"Groups": [{"Summary": "", "PossibleQA": []}]}

    def _get_output_path(self) -> Path:
        """Get the output path for generated QA pairs.

        Returns:
            Path to output file
        """
        folder_path = (
            self.root_path / f"etl_forum_qa/.temp/outputs_generate_qa/{self.product}"
        )
        ensure_folder_exists(str(folder_path))

        actual_folder = folder_path / get_hash_folder(str(self.index))
        ensure_folder_exists(str(actual_folder))

        return actual_folder / f"{self.index}.json"

    def generate(self) -> None:
        """Generate QA pairs and save to file."""
        try:
            content = self.context.thread_dict[self.index]["content"]
            if not content:
                logger.warning(f"No content found for index {self.index}")
                return

            result = self._generate_qa(content)
            result.update(
                {
                    "Product": content["product"],
                    "Url": content["url"],
                    "Title": content["title"],
                    "Category": content["forumName"] + "-" + content["threadTag"],
                }
            )

            output_path = self._get_output_path()
            write_text_to_file(str(output_path), json.dumps(result, ensure_ascii=False))
            logger.info(f"Successfully generated QA pairs for index {self.index}")
        except Exception as e:
            logger.error(f"Error processing index {self.index}: {e}")


def start_generate_forum_qa(context: EtlContext) -> None:
    """Start the forum QA generation process.

    Args:
        context: ETL context containing configuration and paths
    """
    generator = ForumQAGenerator(context)
    generator.generate()
