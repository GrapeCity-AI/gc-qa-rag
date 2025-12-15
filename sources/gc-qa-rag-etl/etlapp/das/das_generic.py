import os
import json
import argparse
import logging
from typing import List, Tuple, Optional, Dict, Any
from etlapp.common.file import ensure_folder_exists, write_text_to_file
from etlapp.common.hash import get_hash_str
from etlapp.common.config import app_config

logger = logging.getLogger(__name__)

def get_markitdown_inst():
    try:
        from markitdown import MarkItDown
        return MarkItDown()
    except ImportError as e:
        logger.error(f"Failed to import MarkItDown: {e}")
        raise

def collect_files(input_dir: str) -> List[Tuple[str, str]]:
    """
    Traverse the directory and collect the absolute paths of all files.
    Returns [(absolute file path, path relative to input_dir)]
    """
    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, input_dir)
            file_list.append((abs_path, rel_path))
    return file_list


def convert_file_to_json(
    product: str, file_path: str, rel_path: str, markitdown_inst
) -> Tuple[Dict[str, Any], str]:
    """
    Use MarkItDown to convert the file and generate a JSON object.
    """
    try:
        result = markitdown_inst.convert(file_path)
        content = result.text_content
    except Exception as e:
        logger.error(f"MarkItDown conversion failed for {file_path}: {e}")
        content = f"[MarkItDown conversion failed: {e}]"
    return {
        "product": product,
        "url": os.path.abspath(file_path),
        "title": os.path.basename(file_path),
        "category": os.path.dirname(rel_path),
        "content": content,
    }, content

def process_files(
    product: str,
    files: List[Tuple[str, str]],
    markitdown_inst,
    output_dir: str,
) -> None:
    """
    Convert and save all files to JSON in the output directory.
    """
    for idx, (file_path, rel_path) in enumerate(files):
        doc_json, content = convert_file_to_json(
            product, file_path, rel_path, markitdown_inst
        )
        content_hash = get_hash_str(content)[:12]
        rel_path_underscored = rel_path.replace(os.sep, "_")
        output_file = os.path.join(
            output_dir, f"{rel_path_underscored}_{content_hash}.json"
        )
        try:
            write_text_to_file(output_file, json.dumps(doc_json, ensure_ascii=False))
            logger.info(f"[{idx + 1}/{len(files)}] Saved {output_file}")
        except Exception as e:
            logger.error(f"Failed to write {output_file}: {e}")

def das_generic_single_file(product: str, filename: str): 
    input_dir = os.path.join(app_config.root_path, f"das/.temp/generic_input/{product}")
    output_dir = os.path.join(app_config.root_path, f"das/.temp/generic_output/{product}")
    
    ensure_folder_exists(input_dir)
    ensure_folder_exists(output_dir)
    
    # Check if the specific file exists
    file_path = os.path.join(input_dir, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {filename} not found in {input_dir}")
    
    # Process only the specific file
    rel_path = filename  # Since it's directly in the input_dir
    files = [(file_path, rel_path)]
    
    logger.info(f"MarkItDown instance is getting")
    markitdown_inst = get_markitdown_inst()
    logger.info(f"MarkItDown instance created")
    
    process_files(product, files, markitdown_inst, output_dir)

def das_generic_main(
    product: str,
    input_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> None:
    """
    Main entry for generic DAS processing.
    """
    if input_dir is None:
        input_dir = os.path.join(
            app_config.root_path, f"das/.temp/generic_input/{product}"
        )
    if output_dir is None:
        output_dir = os.path.join(
            app_config.root_path, f"das/.temp/generic_output/{product}"
        )

    ensure_folder_exists(input_dir)
    ensure_folder_exists(output_dir)

    logger.info(f"MarkItDown instance is getting")
    markitdown_inst = None
    try:
        markitdown_inst = get_markitdown_inst()
        logger.info(f"MarkItDown instance created")
    except:
        markitdown_inst = None
        logger.info(f"MarkItDown instance created failed")
        return

    files = collect_files(input_dir)
    logger.info(f"Found {len(files)} files in {input_dir}")
    process_files(product, files, markitdown_inst, output_dir)
    logger.info(f"Collected {len(files)} files, output to {output_dir}")


def cli():
    parser = argparse.ArgumentParser(
        description="Batch collect all documents in the directory as JSON, convert content to plain text with MarkItDown, and output to das/.temp/generic_output/{product}/"
    )
    parser.add_argument("--product", type=str, required=True, help="Product name")
    parser.add_argument(
        "--input_dir",
        type=str,
        required=False,
        help="Input directory (default: root_path/das/.temp/generic_input/{product}/)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=False,
        help="Output directory (default: root_path/das/.temp/generic_output/{product}/)",
    )
    args = parser.parse_args()
    das_generic_main(args.product, args.input_dir, args.output_dir)


if __name__ == "__main__":
    cli()
