import json
import logging
from typing import Dict, Any, Callable
from pathlib import Path

from etlapp.common.context import EtlContext
from etlapp.common.embedding_qa import embedding_qa_json
from etlapp.common.file import (
    read_text_from_file,
    write_text_to_file,
    ensure_folder_exists,
)

logger = logging.getLogger(__name__)


def process_embedding_file(
    input_file: Path,
    output_file: Path,
    category_parser: Callable[[Dict[str, Any]], str],
) -> None:
    try:
        logger.info(f"Processing embedding file: {input_file}")
        content = read_text_from_file(str(input_file))
        processed_data = embedding_qa_json(content, category_parser)
        write_text_to_file(
            str(output_file), json.dumps(processed_data, ensure_ascii=False)
        )
        logger.info(f"Successfully processed and saved embedding file: {output_file}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {input_file}: {e}")
    except Exception as e:
        logger.error(f"Error processing file {input_file}: {e}", exc_info=True)


def empty_prefix(obj: Any) -> str:
    return "[" + obj["Category"] + "/" + obj["Title"] + "]"


def start_embedding_generic(context: EtlContext) -> None:
    root_path = Path(context.root)
    product = context.product
    file_index = context.index
    input_dir = root_path / f"etl_generic/.temp/outputs_merge_qa/{product}"
    output_dir = root_path / f"etl_generic/.temp/outputs_embedding/{product}"
    ensure_folder_exists(str(input_dir))
    ensure_folder_exists(str(output_dir))
    input_file = input_dir / f"{file_index}.json"
    if not input_file.exists():
        logger.warning(f"Input file does not exist: {input_file}")
        return
    logger.info(f"Starting embedding process for generic file {file_index}")
    output_file = output_dir / input_file.name
    process_embedding_file(input_file, output_file, empty_prefix)
