import argparse
import logging
from app.analyze import ResultAnalyzer
from app.eval import EvaluationEngine
from app.llm import DashScopeImplementation, OpenRouterImplementation
from app.query import KnowledgeBaseClient
from app.question import QuestionBank


def parse_args():
    parser = argparse.ArgumentParser(description="Multi-subject intelligent evaluation")
    parser.add_argument(
        "--subjects",
        type=str,
        default=None,
        help="Specify subjects (comma separated), e.g.: Math,Science",
    )
    parser.add_argument(
        "--parallel", type=int, default=1, help="Number of parallel threads"
    )
    parser.add_argument(
        "--models",
        type=str,
        default="dashscope/qwen-plus",
        help="Model names (comma separated)",
    )
    parser.add_argument(
        "--max_questions",
        type=int,
        default=1000,
        help="Maximum number of questions per subject",
    )
    parser.add_argument(
        "--excel",
        type=str,
        default=".data/questions_full.xlsx",
        help="Question bank Excel path",
    )
    parser.add_argument(
        "--output", type=str, default=".reports/", help="Report output directory"
    )
    return parser.parse_args()


def get_models(model_names: str):
    # Can be extended to support more models and parameters
    name_list = [name.strip() for name in model_names.split(",")]
    models = []
    for name in name_list:
        if name == "dashscope/qwen-plus-thinking":
            models.append(
                DashScopeImplementation(
                    model_name="qwen-plus-2025-04-28",
                    options={"extra_body": {"enable_thinking": True}},
                )
            )
        elif name.startswith("dashscope/"):
            models.append(
                DashScopeImplementation(model_name=name.split("dashscope/")[1])
            )
        else:
            models.append(OpenRouterImplementation(model_name=name))

    return models


def main():
    args = parse_args()
    question_bank = QuestionBank(args.excel)
    kb_client = KnowledgeBaseClient()
    engine = EvaluationEngine(question_bank, kb_client)
    models = get_models(args.models)

    # Select subjects
    all_subjects = question_bank.get_subjects()
    subjects_str = args.subjects

    # subjects_str = "活字格认证工程师-科目一"

    if subjects_str:
        subjects = [s for s in subjects_str.split(",") if s in all_subjects]
        if not subjects:
            print(
                f"Specified subjects not found, all available subjects are: {all_subjects}"
            )
            return
    else:
        subjects = all_subjects

    all_results = []
    for model in models:
        for subject in subjects:
            result = engine.evaluate_model_by_subject(
                model,
                subject,
                parallel_count=args.parallel,
                max_questions=args.max_questions,
                with_context=True,
            )
            all_results.append(result)

    report = ResultAnalyzer.generate_report(all_results, output_path=args.output)
    print(report)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    main()
