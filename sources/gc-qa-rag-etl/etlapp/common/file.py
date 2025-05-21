import os
import shutil
from pathlib import Path
from typing import List


def read_text_from_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Read text content from a file.

    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)

    Returns:
        str: Content of the file

    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file encoding is incorrect
    """
    with open(file_path, "r", encoding=encoding) as file:
        return file.read()


def write_text_to_file(file_path: str, content: str, encoding: str = "utf-8") -> None:
    """
    Write text content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write
        encoding: File encoding (default: utf-8)

    Raises:
        IOError: If file cannot be written
    """
    with open(file_path, "w", encoding=encoding) as file:
        file.write(content)


def ensure_folder_exists(folder_path: str) -> None:
    """
    Create a folder if it doesn't exist.

    Args:
        folder_path: Path to the folder to create
    """
    Path(folder_path).mkdir(parents=True, exist_ok=True)


def get_file_names_in_directory(directory: str) -> List[str]:
    """
    Get all file paths in a directory recursively.

    Args:
        directory: Directory to search

    Returns:
        List[str]: List of file paths
    """
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


def get_sub_folder_names_in_directory(directory: str) -> List[str]:
    """
    Get immediate subfolder names in a directory.

    Args:
        directory: Directory to search

    Returns:
        List[str]: List of subfolder names
    """
    try:
        return [
            item
            for item in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, item))
        ]
    except Exception as e:
        print(f"Error getting subfolders in {directory}: {e}")
        return []


def clear_folder(folder_path: str) -> None:
    """
    Remove all contents of a folder.

    Args:
        folder_path: Path to the folder to clear
    """
    ensure_folder_exists(folder_path)

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        except Exception as e:
            print(f"Failed to delete {item_path}: {e}")
