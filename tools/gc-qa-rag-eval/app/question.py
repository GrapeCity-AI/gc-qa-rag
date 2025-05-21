import pandas as pd
from enum import Enum
from typing import List, Dict


class QuestionType(Enum):
    SINGLE_CHOICE = "单选题"
    MULTIPLE_CHOICE = "多选题"
    TRUE_FALSE = "判断题"


class Question:
    def __init__(self, data: Dict):
        self.id = data["ID"]
        self.type = QuestionType(data["题型"])
        self.content = data["题干"]
        self.correct_answer = data["正确答案"]

        # Extract the content before the second comma as the subject title
        subject_raw = data.get("关联考试信息", "")
        subject_parts = subject_raw.split("，")
        if len(subject_parts) >= 2:
            self.subject = subject_parts[0].strip() + "-" + subject_parts[1].strip()
        else:
            self.subject = subject_raw.strip()

        # Set product based on the prefix of subject
        if self.subject.startswith("活字格"):
            self.product = "forguncy"
        elif self.subject.startswith("Wyn"):
            self.product = "wyn"
        elif self.subject.startswith("SpreadJS"):
            self.product = "spreadjs"
        else:
            self.product = "unknown"

        self.options = {
            k: v for k, v in data.items() if k.startswith("选项") and pd.notna(v)
        }

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "subject": self.subject,
            "product": self.product,
        }


class QuestionBank:
    def __init__(self, excel_path: str):
        self.questions = self._load_questions(excel_path)

    def _load_questions(self, path: str) -> List[Question]:
        df = pd.read_excel(path)
        return [Question(row) for _, row in df.iterrows()]

    def get_subjects(self) -> List[str]:
        """Return all subject names (deduplicated)"""
        return list(sorted(set(q.subject for q in self.questions)))

    def get_questions(self) -> List[Question]:
        # Filter out questions whose content contains <img tag
        return [q for q in self.questions if "<img" not in q.content]

    def get_questions_by_subject(self, subject: str) -> List[Question]:
        """Get questions for the specified subject"""
        return [q for q in self.get_questions() if q.subject == subject]
