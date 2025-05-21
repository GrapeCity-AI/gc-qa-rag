import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from bs4 import BeautifulSoup
from etlapp.common.chunk import split_text_into_sentence_groups
from etlapp.common.context import EtlContext
from etlapp.common.file import (
    write_text_to_file,
    ensure_folder_exists,
)
from etlapp.common.format import extract_qa_object
from etlapp.common.hash import get_hash_folder
from etlapp.common.llm import chat_to_llm, chat_to_llm_with_messages

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PromptConfig:
    """Configuration for LLM prompts."""

    single_group_template: str = """## instruction
我在构建一个检索系统，需要提取下面文档中的知识点，文档主要是产品技术支持论坛的教程帖子，需要总结并提炼，然后针对不同的角度各生成一个相似的问题及其答案，问题需要在源文档中找到答案，问题不少于{{QA_Count}}个，使用中文回答。

## output schema
始终以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。  
 
## 要处理的文档
{{Content}}
"""

    multi_group_template1: str = """
请记住下面的技术文档，它将对你后续要做的任务有帮助。
{{Content_Full}}
"""

    multi_group_template2: str = """## instruction
我在构建一个知识检索系统，需要提取下面文档片段中的知识点，文档主要是产品技术支持论坛的教程帖子，需要先总结并提炼片段部分的概要，然后针对片段内不同的知识点各生成一个相关的问题及其答案，问题需要在源文档中找到答案，问题不少于{{QA_Count}}个，使用中文回答。

## 输出格式
始终直接以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。  

## 文档片段
{{Content_Chunk}}
"""

    assistant_response: str = "好的，我将在后续任务参考上述文档。请告诉我你的具体任务。"


class QAGenerator:
    """Class for generating QA pairs from forum tutorial content."""

    def __init__(self, prompt_config: Optional[PromptConfig] = None):
        self.prompt_config = prompt_config or PromptConfig()

    def get_html_main_content(self, content: str) -> str:
        """Extract main content from HTML."""
        soup = BeautifulSoup(content, "html.parser")
        element = soup
        if element:
            return element.get_text(separator="\n", strip=True)
        else:
            logger.error("HTML parsing error")
            return ""

    def _generate_single_qa(self, prompt: str) -> Dict[str, Any]:
        """Generate QA pairs from a single prompt."""
        try:
            response = chat_to_llm(prompt)
            return extract_qa_object(response)
        except Exception as e:
            logger.error(f"Error generating QA: {e}")
            return {"Summary": "", "PossibleQA": []}

    def _generate_multi_qa(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate QA pairs from multiple messages."""
        try:
            response = chat_to_llm_with_messages(messages)
            return extract_qa_object(response)
        except Exception as e:
            logger.error(f"Error generating QA: {e}")
            return {"Summary": "", "PossibleQA": []}

    def generate_by_single_group(
        self, main_content: str, group: List[str]
    ) -> Dict[str, Any]:
        """Generate QA pairs from a single group of sentences."""
        sentence_length = len(group)
        prompt = self.prompt_config.single_group_template.replace(
            "{{QA_Count}}", str(sentence_length)
        ).replace("{{Content}}", main_content)

        qa_object = self._generate_single_qa(prompt)
        return {"Groups": [qa_object]}

    def generate_by_groups(
        self, main_content: str, groups: List[List[str]]
    ) -> Dict[str, Any]:
        """Generate QA pairs from multiple groups of sentences."""
        objects = []

        for group in groups:
            sentence_length = len(group)
            sentence_text = "。".join(group)

            messages = [
                {"role": "system", "content": "你是一个乐于解答各种问题的助手。"},
                {
                    "role": "user",
                    "content": self.prompt_config.multi_group_template1.replace(
                        "{{Content_Full}}", main_content
                    ),
                },
                {"role": "assistant", "content": self.prompt_config.assistant_response},
                {
                    "role": "user",
                    "content": self.prompt_config.multi_group_template2.replace(
                        "{{QA_Count}}", str(sentence_length)
                    ).replace("{{Content_Chunk}}", sentence_text),
                },
            ]

            qa_object = self._generate_multi_qa(messages)
            objects.append(qa_object)

        return {"Groups": objects}

    def generate(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate QA pairs from forum tutorial content."""
        main_content = self.get_html_main_content(content["authorContent"])
        main_content = (
            f"论坛名称：{content['forumName']} 标题：{content['title']}\n"
            + main_content
        )

        groups = split_text_into_sentence_groups(main_content)

        if len(groups) > 1:
            return self.generate_by_groups(main_content, groups)
        else:
            return self.generate_by_single_group(main_content, groups[0])


def start_generate_forum_tutorial(context: EtlContext) -> None:
    """Start the forum tutorial generation process."""
    root_path = context.root
    product = context.product
    index = context.index
    thread_dict = context.thread_dict

    # Setup paths
    folder_path_r = os.path.join(
        root_path, f"etl_forum_tutorial/.temp/outputs_generate_qa/{product}"
    )

    ensure_folder_exists(folder_path_r)

    try:
        thread = thread_dict[index]
        content = thread["content"]
        if not content:
            return

        logger.info(f"Generating QA for forum tutorial {index}")

        generator = QAGenerator()
        result = generator.generate(content)

        result["Product"] = content["product"]
        result["Url"] = content["url"]
        result["Title"] = content["title"]
        result["Category"] = content["forumName"] + "-" + content["threadTag"]

        actual_folder = os.path.join(folder_path_r, get_hash_folder(str(index)))
        ensure_folder_exists(actual_folder)

        file_path_r = os.path.join(actual_folder, str(index) + ".json")
        write_text_to_file(file_path_r, json.dumps(result, ensure_ascii=False))

    except Exception as e:
        logger.error(f"Error in forum tutorial generation: {e}")
