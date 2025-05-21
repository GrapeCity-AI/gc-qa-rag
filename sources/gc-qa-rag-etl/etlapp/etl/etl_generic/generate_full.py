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

    def _generate_answer(self, qa_pair: QAPair, doc: Document) -> str:
        try:
            prompt = self.PROMPT_TEMPLATE.format(
                question=f"Q：{qa_pair.question}\r\n",
                content=doc.content_text,
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
            doc_content = read_text_from_file(str(doc_path))
            return Document.from_text(doc_content)
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

    def _save_answer(
        self, answer: str, output_path: Path, chunk_index: int, qa_index: int
    ) -> None:
        try:
            write_text_to_file(str(output_path), answer)
        except Exception as e:
            logger.error(f"Error saving answer: {e}")

    def generate(self) -> None:
        qa_folder, full_folder, text_folder = self._get_file_paths()
        self._ensure_directories_exist(qa_folder, full_folder, text_folder)
        qa_path = qa_folder / f"{self.file_index}.json"
        doc_path = text_folder / f"{self.file_index}.txt"
        if not qa_path.exists() or not doc_path.exists():
            return
        doc = self._load_document(doc_path)
        if not doc:
            return
        chunks = self._load_qa_data(qa_path)
        if not chunks:
            return
        full_folder_path = full_folder / str(self.file_index)
        clear_folder(str(full_folder_path))
        logger.info(f"generate_full----{self.file_index}")
        for chunk_index, chunk in enumerate(chunks):
            for qa_index, qa_pair in enumerate(chunk.possible_qa):
                logger.info(
                    f"--{self.file_index}_{chunk_index}_{qa_index}_{qa_pair.question}"
                )
                answer = self._generate_answer(qa_pair, doc)
                output_path = (
                    full_folder_path / f"{self.file_index}_{chunk_index}_{qa_index}.md"
                )
                self._save_answer(answer, output_path, chunk_index, qa_index)


def start_generate_full_generic(context: EtlContext) -> None:
    generator = FullGenericGenerator(context)
    generator.generate()
