import json
import re
from typing import Dict, List, Optional, Union


def extract_qa_object(text: str) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """
    Extract QA object from text, attempting both JSON and manual extraction methods.

    Args:
        text: Input text containing QA information

    Returns:
        Dictionary containing Summary and PossibleQA list
    """
    extracted_content = extract_json_content(text)
    parsed_json: Dict[str, Union[str, List[Dict[str, str]]]] = {
        "Summary": "",
        "PossibleQA": [],
    }

    try:
        if extracted_content:
            parsed_json = json.loads(extracted_content)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {str(e)}")
        try:
            print("Attempting manual extraction...")
            parsed_json = extract_json_manually(text)
            print("Manual extraction successful")
        except Exception as e:
            print(f"Manual extraction failed: {str(e)}")
            print("Returning default empty object")

    return parsed_json


def extract_json_content(text: str) -> str:
    """
    Extract JSON content from text enclosed in ```json blocks.

    Args:
        text: Input text containing JSON

    Returns:
        Extracted JSON content or original text if no JSON block found
    """
    JSON_PATTERN = r"```json(.*?)```"
    match = re.search(JSON_PATTERN, text, re.DOTALL)
    return match.group(1) if match else text


def extract_json_manually(
    text: str,
) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
    """
    Manually extract QA information from text using regex patterns.

    Args:
        text: Input text containing QA information

    Returns:
        Dictionary containing Summary and PossibleQA list, or None if extraction fails
    """
    # Define regex patterns
    SUMMARY_PATTERN = r'"Summary":\s*"([^"]*)"'
    QUESTION_PATTERN = r'"Question":\s*"([^"]*)"'
    ANSWER_PATTERN = r'"Answer":\s*"([^"]*)"'

    # Extract content using patterns
    summary_match = re.search(SUMMARY_PATTERN, text)
    questions = re.findall(QUESTION_PATTERN, text)
    answers = re.findall(ANSWER_PATTERN, text)

    # Validate and construct result
    if not (summary_match and questions and answers and len(questions) == len(answers)):
        return None

    result = {
        "Summary": summary_match.group(1),
        "PossibleQA": [
            {"Question": q, "Answer": a} for q, a in zip(questions, answers)
        ],
    }

    return result


def extract_markdown_content(text: str) -> str:
    """
    Extract markdown content from text enclosed in ```markdown blocks.

    Args:
        text: Input text containing markdown

    Returns:
        Extracted markdown content or original text if no markdown block found
    """
    MARKDOWN_PATTERN = r"```markdown\s*(.*?)\s*```"
    matches = re.findall(MARKDOWN_PATTERN, text, re.DOTALL)
    return "\n".join(matches).strip() if matches else text.strip()
