import json
from typing import Dict, List, Any, Callable
from etlapp.common.embedding import create_embedding


def _embed_questions(qa_list: List[Dict[str, Any]], prefix: str) -> None:
    """Embed questions from a list of QA objects."""
    questions = [
        prefix + item["Question"]
        for item in qa_list
        if "Question" in item and item["Question"]
    ]
    if not questions:
        return

    question_embeddings = create_embedding(questions).output["embeddings"]
    for embedding_item in question_embeddings:
        text_index = embedding_item["text_index"]
        qa_list[text_index]["QuestionEmbedding"] = embedding_item


def _embed_answers(qa_list: List[Dict[str, Any]], prefix: str) -> None:
    """Embed answers from a list of QA objects."""
    answers = [
        prefix + item["Answer"]
        for item in qa_list
        if "Answer" in item and item["Answer"]
    ]
    if not answers:
        return

    answer_embeddings = create_embedding(answers).output["embeddings"]
    for embedding_item in answer_embeddings:
        text_index = embedding_item["text_index"]
        qa_list[text_index]["AnswerEmbedding"] = embedding_item


def embedding_qa_object(qa_object: Dict[str, Any], prefix: str) -> Dict[str, Any]:
    """Embed questions and answers from a QA object."""
    if not qa_object.get("PossibleQA"):
        return qa_object

    qa_list = qa_object["PossibleQA"]
    _embed_questions(qa_list, prefix)
    _embed_answers(qa_list, prefix)

    return qa_object


def embedding_qa_json(
    text: str, parse_category_function: Callable[[Dict[str, Any]], str]
) -> Dict[str, Any]:
    """Process and embed QA data from JSON text."""
    try:
        root = json.loads(text)
    except json.JSONDecodeError:
        print("Failed to parse JSON, returning default empty object")
        return {"Groups": [{"Summary": "", "PossibleQA": []}]}

    prefix = parse_category_function(root)

    for group in root["Groups"]:
        embedding_qa_object(group, prefix)

        # Process sub-questions if they exist
        sub_questions = [
            item["Sub"]
            for item in group["PossibleQA"]
            if "Sub" in item and item["Sub"] is not None
        ]
        for sub_qa in sub_questions:
            embedding_qa_object(sub_qa, prefix)

    return root
