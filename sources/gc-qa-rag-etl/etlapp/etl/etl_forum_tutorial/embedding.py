import os
import json
import logging
from typing import Dict, Any, Callable
from etlapp.common.context import EtlContext
from etlapp.common.embedding_qa import embedding_qa_json
from etlapp.common.file import (
    read_text_from_file,
    write_text_to_file,
    ensure_folder_exists,
)
from etlapp.common.hash import get_hash_folder

# Configure logging
logger = logging.getLogger(__name__)


def format_category(category_data: Dict[str, Any]) -> str:
    """Format category data into a string representation.

    Args:
        category_data: Dictionary containing category information

    Returns:
        Formatted category string
    """
    return f"[{category_data['Category']}]"


def process_qa_file(
    input_file_path: str,
    output_file_path: str,
    category_formatter: Callable[[Dict[str, Any]], str],
) -> None:
    """Process a single QA file by reading, embedding, and writing the results.

    Args:
        input_file_path: Path to the input JSON file
        output_file_path: Path where the output should be written
        category_formatter: Function to format category data
    """
    if not os.path.exists(input_file_path):
        return

    logger.info(f"Processing file: {os.path.basename(input_file_path)}")

    try:
        qa_data = read_text_from_file(input_file_path)
        embedded_data = embedding_qa_json(qa_data, category_formatter)
        write_text_to_file(
            output_file_path, json.dumps(embedded_data, ensure_ascii=False)
        )
    except Exception as e:
        logger.error(f"Error processing file {input_file_path}: {str(e)}")
        raise


def start_embedding_forum_tutorial(context: EtlContext) -> None:
    """Start the embedding process for forum tutorial data.

    Args:
        context: ETL context containing configuration and paths
    """
    root_path = context.root
    product = context.product
    file_index = context.index

    # Define input and output paths
    input_base_path = os.path.join(
        root_path, f"etl_forum_tutorial/.temp/outputs_generate_qa/{product}"
    )
    output_base_path = os.path.join(
        root_path, f"etl_forum_tutorial/.temp/outputs_embedding/{product}"
    )

    # Ensure directories exist
    ensure_folder_exists(input_base_path)
    ensure_folder_exists(output_base_path)

    # Construct file paths
    input_folder = os.path.join(input_base_path, get_hash_folder(str(file_index)))
    input_file = os.path.join(input_folder, f"{file_index}.json")

    output_folder = os.path.join(output_base_path, get_hash_folder(str(file_index)))
    ensure_folder_exists(output_folder)
    output_file = os.path.join(output_folder, f"{file_index}.json")

    # Process the file
    process_qa_file(input_file, output_file, format_category)
