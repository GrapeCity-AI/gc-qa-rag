import json
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path
from etlapp.common.context import EtlContext
from etlapp.common.file import (
    read_text_from_file,
    write_text_to_file,
    ensure_folder_exists,
    clear_folder,
)
from etlapp.common.llm import chat_to_llm

logger = logging.getLogger(__name__)


@dataclass
class QAPair:
    question: str
    answer: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QAPair":
        return cls(question=data.get("Question", ""))


@dataclass
class Chunk:
    possible_qa: List[QAPair]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        return cls(
            possible_qa=[QAPair.from_dict(qa) for qa in data.get("PossibleQA", [])]
        )


class Document:
    def __init__(self, content_text: str):
        self.content_text = content_text

    @classmethod
    def from_text(cls, text: str) -> "Document":
        return cls(content_text=text)


class FullGenericGenerator:
    PROMPT_TEMPLATE = """基于以下<用户问题>，参考<相关文档>，生成一个最符合用户问题的总结性答案，输出为 markdown 格式的文本。\n## 用户问题\n{question}\n\n## 相关文档\n{content}\n"""

    def __init__(self, context: EtlContext):
        self.context = context
        self.root_path = Path(context.root)
        self.product = context.product
        self.file_index = context.index

    def _generate_answer(self, qa_pair: QAPair, doc_content: str) -> str:
        try:
            prompt = self.PROMPT_TEMPLATE.format(
                question=f"Q：{qa_pair.question}\r\n",
                content=doc_content,
            )
            return chat_to_llm(prompt)
        except Exception as e:
            logger.error(f"Exception occurred while generating answer: {e}")
            return ""

    def _get_file_paths(self) -> tuple[Path, Path, Path]:
        qa_folder = (
            self.root_path / f"etl_generic/.temp/outputs_generate_qa/{self.product}"
        )
        full_folder = (
            self.root_path
            / f"etl_generic/.temp/outputs_generate_qa_full/{self.product}"
        )
        text_folder = self.root_path / f"das/.temp/generic_output/{self.product}"
        return qa_folder, full_folder, text_folder

    def _ensure_directories_exist(self, *paths: Path) -> None:
        for path in paths:
            ensure_folder_exists(str(path))

    def _load_document(self, doc_path: Path) -> Optional[Document]:
        try:
            doc_text = read_text_from_file(str(doc_path))
            return json.loads(doc_text)["content"]
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            return None

    def _load_qa_data(self, qa_path: Path) -> Optional[List[Chunk]]:
        try:
            content = read_text_from_file(str(qa_path))
            data = json.loads(content)
            return [Chunk.from_dict(chunk) for chunk in data.get("Groups", [])]
        except Exception as e:
            logger.error(f"Error loading QA data: {e}")
            return None

    def _save_answer(self, answer: str, output_path: Path) -> None:
        try:
            write_text_to_file(str(output_path), answer)
        except Exception as e:
            logger.error(f"Error saving answer: {e}")

    def generate(self) -> None:
        print(f"🚀 [FULL-GEN] Starting full answer generation for: {self.file_index}")

        qa_folder, full_folder, text_folder = self._get_file_paths()
        self._ensure_directories_exist(qa_folder, full_folder, text_folder)

        qa_path = qa_folder / f"{self.file_index}.json"
        doc_path = text_folder / f"{self.file_index}.json"

        print(f"📂 [FULL-GEN] QA folder: {qa_folder}")
        print(f"📂 [FULL-GEN] Full folder: {full_folder}")
        print(f"📂 [FULL-GEN] Text folder: {text_folder}")
        print(f"📄 [FULL-GEN] QA path: {qa_path}")
        print(f"📄 [FULL-GEN] Doc path: {doc_path}")

        if not qa_path.exists():
            print(f"❌ [FULL-GEN] QA file not found: {qa_path}")
            return
        if not doc_path.exists():
            print(f"❌ [FULL-GEN] Document file not found: {doc_path}")
            return

        print("✅ [FULL-GEN] Both QA and document files exist")

        doc_content = self._load_document(doc_path)
        if not doc_content:
            print("❌ [FULL-GEN] Failed to load document content")
            return

        print(f"📄 [FULL-GEN] Document loaded, length: {len(doc_content)} characters")

        chunks = self._load_qa_data(qa_path)
        if not chunks:
            print("❌ [FULL-GEN] No QA chunks loaded! This is the main problem!")
            print("🔍 [FULL-GEN] Check if QA generation step produced valid output")
            return

        print(f"🎯 [FULL-GEN] Loaded {len(chunks)} QA chunks")
        total_qa_pairs = sum(len(chunk.possible_qa) for chunk in chunks)
        print(f"📊 [FULL-GEN] Total QA pairs to process: {total_qa_pairs}")

        if total_qa_pairs == 0:
            print("⚠️ [FULL-GEN] No QA pairs found in chunks!")
            return

        full_folder_path = full_folder / str(self.file_index)
        clear_folder(str(full_folder_path))
        logger.info(f"generate_full----{self.file_index}")

        processed_count = 0
        for chunk_index, chunk in enumerate(chunks):
            print(f"📦 [FULL-GEN] Processing chunk {chunk_index + 1}/{len(chunks)}")
            print(f"🔢 [FULL-GEN] Chunk has {len(chunk.possible_qa)} QA pairs")

            for qa_index, qa_pair in enumerate(chunk.possible_qa):
                print(f"❓ [FULL-GEN] Processing QA {qa_index + 1}: {qa_pair.question[:100]}...")
                logger.info(
                    f"--{self.file_index}_{chunk_index}_{qa_index}_{qa_pair.question}"
                )

                answer = self._generate_answer(qa_pair, doc_content)

                if answer:
                    print(f"✅ [FULL-GEN] Generated answer, length: {len(answer)} characters")
                else:
                    print("⚠️ [FULL-GEN] Generated empty answer")

                output_path = (
                    full_folder_path / f"{self.file_index}_{chunk_index}_{qa_index}.md"
                )
                self._save_answer(answer, output_path)
                processed_count += 1

        print("🏁 [FULL-GEN] Full answer generation completed!")
        print(f"📊 [FULL-GEN] Processed {processed_count} QA pairs")
        print(f"💾 [FULL-GEN] Saved to: {full_folder_path}")


def start_generate_full_generic(context: EtlContext) -> None:
    generator = FullGenericGenerator(context)
    generator.generate()
