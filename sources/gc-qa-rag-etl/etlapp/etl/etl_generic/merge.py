import json
import logging
from typing import List, Dict, Any
from pathlib import Path
from etlapp.common.context import EtlContext
from etlapp.common.file import (
    read_text_from_file,
    write_text_to_file,
    ensure_folder_exists,
    get_file_names_in_directory,
)

logger = logging.getLogger(__name__)


class QAObject:
    def __init__(self, summary: str = "", possible_qa: List[Dict[str, Any]] = None):
        self.summary = summary
        self.possible_qa = possible_qa or []

    @classmethod
    def from_json(cls, text: str) -> "QAObject":
        try:
            data = json.loads(text)
            return cls(
                summary=data.get("Summary", ""), possible_qa=data.get("PossibleQA", [])
            )
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON, returning empty QAObject")
            return cls()


class QARoot:
    def __init__(self, groups: List[Dict[str, Any]] = None):
        self.groups = groups or [{"Summary": "", "PossibleQA": []}]

    @classmethod
    def from_json(cls, text: str) -> "QARoot":
        try:
            data = json.loads(text)
            return cls(groups=data.get("Groups", [{"Summary": "", "PossibleQA": []}]))
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON, returning empty QARoot")
            return cls()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Product": self.product,
            "Url": self.url,
            "Title": self.title,
            "Category": self.category,
            "Groups": self.groups,
        }


def merge_qa_sub(
    text: str, sub_file_list: List[str], doc_object: Dict[str, Any]
) -> QARoot:
    root = QARoot.from_json(text)

    # Set document metadata
    root.product = doc_object["product"]
    root.url = doc_object["url"]
    root.title = doc_object["title"]
    root.category = doc_object["category"]

    for sub_file in sub_file_list:
        filename = Path(sub_file).stem
        _, group_index, qa_index = filename.split("_")
        group_index = int(group_index)
        qa_index = int(qa_index)
        sub_text = read_text_from_file(sub_file)
        sub_qa = QAObject.from_json(sub_text)
        if group_index < len(root.groups) and qa_index < len(
            root.groups[group_index]["PossibleQA"]
        ):
            root.groups[group_index]["PossibleQA"][qa_index]["Sub"] = sub_qa.__dict__
    return root


def get_folder_paths(context: EtlContext) -> Dict[str, Path]:
    root_path = Path(context.root)
    product = context.product
    return {
        "doc": root_path / f"das/.temp/generic_output/{product}",
        "qa": root_path / f"etl_generic/.temp/outputs_generate_qa/{product}",
        "sub": root_path / f"etl_generic/.temp/outputs_generate_qa_sub/{product}",
        "merge": root_path / f"etl_generic/.temp/outputs_merge_qa/{product}",
    }


def start_merge_generic(context: EtlContext) -> None:
    paths = get_folder_paths(context)
    for path in paths.values():
        ensure_folder_exists(str(path))

    file_path = paths["qa"] / f"{context.index}.json"
    if not file_path.exists():
        return

    sub_folder = paths["sub"] / str(context.index)
    sub_file_list = (
        get_file_names_in_directory(str(sub_folder)) if sub_folder.exists() else []
    )

    # Read document metadata
    doc_file_path = paths["doc"] / f"{context.index}.json"
    doc_object = json.loads(read_text_from_file(str(doc_file_path)))

    logger.info(f"Starting merge for generic document {context.index}")
    content = read_text_from_file(str(file_path))
    merged_object = merge_qa_sub(content, sub_file_list, doc_object)
    output_path = paths["merge"] / file_path.name
    write_text_to_file(
        str(output_path), json.dumps(merged_object.to_dict(), ensure_ascii=False)
    )
    logger.info(f"Successfully merged generic document {context.index}")
