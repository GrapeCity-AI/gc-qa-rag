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
    print("🔍 [PARSE] Starting QA object extraction...")
    print(f"📄 [PARSE] Input text length: {len(text)} characters")
    print(f"🔍 [PARSE] Input preview: {text[:300]}...")

    extracted_content = extract_json_content(text)
    print(f"📋 [PARSE] JSON content extracted, length: {len(extracted_content)} characters")

    if extracted_content != text:
        print(f"✂️ [PARSE] Found JSON code block, extracted content: {extracted_content[:200]}...")
    else:
        print("📝 [PARSE] No JSON code block found, using original text")

    parsed_json: Dict[str, Union[str, List[Dict[str, str]]]] = {
        "Summary": "",
        "PossibleQA": [],
    }

    try:
        if extracted_content:
            print("🔧 [PARSE] Attempting JSON parsing...")
            parsed_json = json.loads(extracted_content)

            qa_count = len(parsed_json.get("PossibleQA", []))
            summary = parsed_json.get("Summary", "")

            print("✅ [PARSE] JSON parsing successful!")
            print(f"🎯 [PARSE] Found {qa_count} QA pairs")
            print(f"📊 [PARSE] Summary: {summary[:100]}..." if summary else "📊 [PARSE] No summary found")

            if qa_count == 0:
                print("⚠️ [PARSE] WARNING: No QA pairs found in parsed JSON!")
                print(f"🔍 [PARSE] Parsed structure: {list(parsed_json.keys())}")

    except json.JSONDecodeError as e:
        print(f"❌ [PARSE] JSON parsing failed: {str(e)}")
        print(f"🔍 [PARSE] Failed content: {extracted_content[:500]}...")
        try:
            print("🔧 [PARSE] Attempting manual extraction...")
            manual_result = extract_json_manually(text)
            if manual_result:
                parsed_json = manual_result
                qa_count = len(parsed_json.get("PossibleQA", []))
                print(f"✅ [PARSE] Manual extraction successful! Found {qa_count} QA pairs")
            else:
                print("❌ [PARSE] Manual extraction returned None")
        except Exception as e:
            print(f"❌ [PARSE] Manual extraction failed: {str(e)}")
            print("💀 [PARSE] Returning default empty object")

    final_qa_count = len(parsed_json.get("PossibleQA", []))
    print(f"🏁 [PARSE] Final result: {final_qa_count} QA pairs extracted")

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
