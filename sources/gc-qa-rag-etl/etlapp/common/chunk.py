from typing import List


def split_text_into_sentence_groups(
    text: str,
    group_size: int = 10,
    min_group_size: int = 5,
    sentence_delimiter: str = "。",
) -> List[List[str]]:
    """
    Split text into groups of sentences based on the specified delimiter.

    Args:
        text: The input text to be split
        group_size: Maximum number of sentences per group
        min_group_size: Minimum number of sentences required for a new group
        sentence_delimiter: Character used to split sentences (default: Chinese period)

    Returns:
        List of sentence groups, where each group is a list of sentences
    """
    if not text:
        return []

    sentences = text.split(sentence_delimiter)

    # Remove empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return []

    groups = []
    current_group = []

    for sentence in sentences:
        current_group.append(sentence)

        if len(current_group) >= group_size:
            groups.append(current_group)
            current_group = []

    # Handle remaining sentences
    if current_group:
        if len(current_group) < min_group_size and groups:
            # Merge with last group if too small
            groups[-1].extend(current_group)
        else:
            groups.append(current_group)

    return groups
