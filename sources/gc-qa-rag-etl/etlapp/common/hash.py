import hashlib


def get_hash_str(text: str) -> str:
    """
    Generate SHA-256 hash of a text string.

    Args:
        text: Text to hash

    Returns:
        str: Hexadecimal hash string
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_hash_folder(file_name: str, folder_count: int = 100) -> str:
    """
    Generate a folder name based on file name hash.

    Args:
        file_name: Name of the file
        folder_count: Number of folders to distribute files into

    Returns:
        str: Folder name (0 to folder_count-1)
    """
    hash_int = int(hashlib.sha256(file_name.encode("utf-8")).hexdigest(), 16)
    return str(hash_int % folder_count)
