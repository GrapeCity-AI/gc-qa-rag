import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from etlapp.common.chunk import split_text_into_sentence_groups
from etlapp.common.context import EtlContext
from etlapp.common.file import (
    read_text_from_file,
    write_text_to_file,
    ensure_folder_exists,
)
from etlapp.common.format import extract_qa_object
from etlapp.common.llm import chat_to_llm, chat_to_llm_with_messages

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PromptConfig:
    single_group_template: str = """## instruction\n我在构建一个检索系统，需要提取下面文档中的知识点，文档为通用文本，需要总结并提炼，然后针对不同的角度各生成一个相似的问题及其答案，问题需要在源文档中找到答案，问题不少于{{QA_Count}}个，使用中文回答。\n\n## output schema\n始终以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。  \n\n## 要处理的文档\n{{Content}}\n"""
    multi_group_template1: str = (
        """请记住下面的文本内容，它将对你后续要做的任务有帮助。\n{{Content_Full}}\n"""
    )
    multi_group_template2: str = """## instruction\n我在构建一个知识检索系统，需要提取下面文本片段中的知识点，需要先总结并提炼片段部分的概要，然后针对片段内不同的知识点各生成一个相关的问题及其答案，问题需要在源文档中找到答案，问题不少于{{QA_Count}}个，使用中文回答。\n\n## 输出格式\n始终直接以如下JSON格式返回：{"Summary":"string","PossibleQA":[{"Question":"string","Answer":"string"}]}。  \n\n## 文本片段\n{{Content_Chunk}}\n"""
    assistant_response: str = "好的，我将在后续任务参考上述文本。请告诉我你的具体任务。"


class QAGenerator:
    def __init__(self, prompt_config: Optional[PromptConfig] = None):
        self.prompt_config = prompt_config or PromptConfig()

    def _generate_single_qa(self, prompt: str) -> Dict[str, Any]:
        try:
            print("🤖 [QA-GEN] Starting single QA generation...")
            print(f"📝 [QA-GEN] Prompt length: {len(prompt)} characters")
            print(f"🔍 [QA-GEN] Prompt preview: {prompt[:200]}...")

            response = chat_to_llm(prompt)

            print(f"✅ [QA-GEN] LLM response received, length: {len(response)} characters")
            print(f"📄 [QA-GEN] Response preview: {response[:300]}...")

            qa_result = extract_qa_object(response)
            qa_count = len(qa_result.get("PossibleQA", []))

            print(f"🎯 [QA-GEN] Extracted {qa_count} QA pairs")
            print(f"📊 [QA-GEN] Summary: {qa_result.get('Summary', 'N/A')[:100]}...")

            if qa_count == 0:
                print("⚠️ [QA-GEN] WARNING: No QA pairs generated!")
                print(f"🔍 [QA-GEN] Full LLM response: {response}")

            return qa_result
        except Exception as e:
            print(f"❌ [QA-GEN] ERROR in _generate_single_qa: {str(e)}")
            print(f"💣 [QA-GEN] Exception type: {type(e).__name__}")
            logger.error(f"Error generating QA: {e}")
            return {"Summary": "", "PossibleQA": []}

    def _generate_multi_qa(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        try:
            print("🤖 [QA-MULTI] Starting multi-turn QA generation...")
            print(f"💬 [QA-MULTI] Message count: {len(messages)}")
            for i, msg in enumerate(messages):
                content_preview = msg.get("content", "")[:150] + "..." if len(msg.get("content", "")) > 150 else msg.get("content", "")
                print(f"📝 [QA-MULTI] Message {i+1} ({msg.get('role', 'unknown')}): {content_preview}")

            response = chat_to_llm_with_messages(messages)

            print(f"✅ [QA-MULTI] LLM response received, length: {len(response)} characters")
            print(f"📄 [QA-MULTI] Response preview: {response[:300]}...")

            qa_result = extract_qa_object(response)
            qa_count = len(qa_result.get("PossibleQA", []))

            print(f"🎯 [QA-MULTI] Extracted {qa_count} QA pairs")
            print(f"📊 [QA-MULTI] Summary: {qa_result.get('Summary', 'N/A')[:100]}...")

            if qa_count == 0:
                print("⚠️ [QA-MULTI] WARNING: No QA pairs generated!")
                print(f"🔍 [QA-MULTI] Full LLM response: {response}")

            return qa_result
        except Exception as e:
            print(f"❌ [QA-MULTI] ERROR in _generate_multi_qa: {str(e)}")
            print(f"💣 [QA-MULTI] Exception type: {type(e).__name__}")
            logger.error(f"Error generating QA: {e}")
            return {"Summary": "", "PossibleQA": []}

    def generate_by_single_group(
        self, main_content: str, group: List[str]
    ) -> Dict[str, Any]:
        sentence_length = len(group)
        prompt = self.prompt_config.single_group_template.replace(
            "{{QA_Count}}", str(sentence_length)
        ).replace("{{Content}}", main_content)
        qa_object = self._generate_single_qa(prompt)
        return {"Groups": [qa_object]}

    def generate_by_groups(
        self, main_content: str, groups: List[List[str]]
    ) -> Dict[str, Any]:
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

    def generate(self, text: str) -> Dict[str, Any]:
        main_content = text
        groups = split_text_into_sentence_groups(main_content)
        if len(groups) > 1:
            return self.generate_by_groups(main_content, groups)
        else:
            return self.generate_by_single_group(main_content, groups[0])


def start_generate_generic(context: EtlContext) -> None:
    print(f"🚀 [ETL-GEN] Starting QA generation for file: {context.index}")
    print(f"📁 [ETL-GEN] Product: {context.product}")
    print(f"📂 [ETL-GEN] Root path: {context.root}")

    root_path = context.root
    product = context.product
    file_index = context.index
    folder_path = os.path.join(root_path, f"das/.temp/generic_output/{product}")
    folder_path_r = os.path.join(
        root_path, f"etl_generic/.temp/outputs_generate_qa/{product}"
    )

    print(f"📂 [ETL-GEN] Input folder: {folder_path}")
    print(f"📂 [ETL-GEN] Output folder: {folder_path_r}")

    ensure_folder_exists(folder_path)
    ensure_folder_exists(folder_path_r)

    try:
        file_path = os.path.join(folder_path, str(file_index) + ".json")
        print(f"📄 [ETL-GEN] Looking for input file: {file_path}")

        if not os.path.exists(file_path):
            print(f"❌ [ETL-GEN] Input file not found: {file_path}")
            return

        print("✅ [ETL-GEN] Input file found, reading content...")
        logger.info(f"generate---{file_index}")

        doc_obj = json.loads(read_text_from_file(file_path))
        content = doc_obj["content"]

        print(f"📄 [ETL-GEN] Document content loaded, length: {len(content)} characters")
        print(f"🔍 [ETL-GEN] Content preview: {content[:200]}...")

        generator = QAGenerator()
        print("🤖 [ETL-GEN] Starting QA generation process...")
        result = generator.generate(content)

        total_qa_count = sum(len(group.get("PossibleQA", [])) for group in result.get("Groups", []))
        print(f"🎯 [ETL-GEN] QA generation completed! Total QA pairs: {total_qa_count}")
        print(f"📊 [ETL-GEN] Groups generated: {len(result.get('Groups', []))}")

        filename_r = os.path.basename(file_path)
        file_path_r = os.path.join(folder_path_r, filename_r)

        print(f"💾 [ETL-GEN] Saving results to: {file_path_r}")
        write_text_to_file(file_path_r, json.dumps(result, ensure_ascii=False))

        print(f"✅ [ETL-GEN] QA generation completed successfully for {file_index}")
        print(f"🔍 [ETL-GEN] Result preview: {json.dumps(result, ensure_ascii=False)[:500]}...")

    except Exception as e:
        print(f"❌ [ETL-GEN] FATAL ERROR in start_generate_generic: {str(e)}")
        print(f"💣 [ETL-GEN] Exception type: {type(e).__name__}")
        print("🔍 [ETL-GEN] Full traceback will be in logs")
        logger.error(f"Error in generic document generation: {e}")
        raise
