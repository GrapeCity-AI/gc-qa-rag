import logging
import json
import concurrent.futures
import re
from typing import List, Dict, Tuple

from app.llm import LLMInterface
from app.query import KnowledgeBaseClient
from app.question import Question, QuestionBank


class EvaluationEngine:
    def __init__(self, question_bank: QuestionBank, kb_client: KnowledgeBaseClient):
        self.question_bank = question_bank
        self.kb_client = kb_client
        self.logger = logging.getLogger(__name__)

    def _score_answer(self, question: Question, answer: str) -> Tuple[float, str]:
        """Scoring logic: Prefer to extract content within <答案></答案> tags for comparison. If the answer matches exactly, score 1, otherwise 0."""
        # Try to extract content within <答案>...</答案> tags (take only the last match)
        matches = re.findall(r"<答案>(.*?)</答案>", answer)
        answer_to_check = matches[-1].strip() if matches else answer.strip()
        if answer_to_check == question.correct_answer.strip():
            return 1.0, "Correct answer"
        else:
            return 0.0, f"Incorrect answer. Standard answer: {question.correct_answer}"

    def _calculate_metrics(self, results: List[Dict]) -> Dict:
        """Calculate evaluation metrics"""
        total = len(results)
        correct = sum(1 for r in results if r["score"] == 1.0)
        accuracy = correct / total if total > 0 else 0

        return {
            "total_questions": total,
            "correct_answers": correct,
            "accuracy": accuracy,
            # More metrics can be added
        }

    def evaluate_model_by_subject(
        self,
        llm: LLMInterface,
        subject: str,
        parallel_count: int = 1,
        max_questions: int = 100,
        with_context: bool = False,
        agentic_mode: bool = False,
    ) -> Dict:
        """Evaluate the model for a specific subject"""
        mode_str = (
            "agentic"
            if agentic_mode
            else ("with_context" if with_context else "no_context")
        )
        self.logger.info(
            f"Start evaluating model: {llm.model_display_name}, subject: {subject}, mode: {mode_str}"
        )
        results = []
        try:
            questions = self.question_bank.get_questions_by_subject(subject)[
                :max_questions
            ]

            self.logger.info(f"Subject [{subject}] fetched {len(questions)} questions")

            def process_question(idx_question):
                idx, question = idx_question
                context = {}
                answer = ""

                if agentic_mode:
                    # Use agentic mode - let the model decide when and how to search
                    self.logger.debug(
                        f"[{llm.model_display_name}] Question {idx} (agentic): {question.content}"
                    )
                    answer = llm.generate_answer_agentic(question, self.kb_client)
                    context = "agentic_mode"  # Mark that agentic mode was used
                elif with_context:
                    # Traditional mode with pre-search
                    context = self.kb_client.search(
                        question.content
                        + json.dumps(question.options, ensure_ascii=False),
                        question.product,
                    )
                    self.logger.debug(
                        f"[{llm.model_display_name}] Question {idx}: {question.content}"
                    )
                    answer = llm.generate_answer(question, context)
                else:
                    # No context mode
                    self.logger.debug(
                        f"[{llm.model_display_name}] Question {idx}: {question.content}"
                    )
                    answer = llm.generate_answer(question, context)

                score, feedback = self._score_answer(question, answer)

                self.logger.info(
                    f"[{llm.model_display_name}] Question {idx},  score: {score}"
                )
                result = {
                    "question_id": question.id,
                    "question": question.content,
                    "correct_answer": question.correct_answer,
                    "model_answer": answer,
                    "score": score,
                    "feedback": feedback,
                    "context_used": context,
                    "subject": subject,
                    "evaluation_mode": mode_str,
                }
                self.logger.debug(
                    f"[{llm.model_display_name}] Question {idx} score: {score}, feedback: {feedback}"
                )

                return result

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=parallel_count
            ) as executor:
                results = list(executor.map(process_question, enumerate(questions, 1)))

            metrics = self._calculate_metrics(results)
            self.logger.info(
                f"Model {llm.model_display_name} evaluation completed, subject [{subject}], mode: {mode_str}, accuracy: {metrics['accuracy']:.2%}"
            )
            return {
                "model": str(llm.model_display_name),
                "options": llm.options,
                "results": results,
                "metrics": metrics,
                "subject": subject,
                "evaluation_mode": mode_str,
            }
        except Exception as e:
            self.logger.exception(
                f"Exception occurred while evaluating model {llm.model_display_name}, subject [{subject}]: {e}"
            )
            raise

    def evaluate_model_all_subjects(
        self,
        llm: LLMInterface,
        parallel_count: int = 1,
        max_questions: int = 100,
        agentic_mode: bool = False,
    ) -> List[Dict]:
        """Batch evaluation for all subjects, return evaluation results for each subject"""
        subjects = self.question_bank.get_subjects()
        all_results = []
        for subject in subjects:
            result = self.evaluate_model_by_subject(
                llm, subject, parallel_count, max_questions, agentic_mode=agentic_mode
            )
            all_results.append(result)
        return all_results
