import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
import logging
from typing import List, Dict
from datetime import datetime


class ResultAnalyzer:
    @staticmethod
    def generate_report(evaluation_results: List[Dict], output_path: str = None) -> str:
        """Generate evaluation report, supports multiple subjects"""
        logger = logging.getLogger(__name__)
        logger.info("Start generating evaluation report")
        try:
            # Support passing in single or multiple subject results
            if isinstance(evaluation_results, dict):
                evaluation_results = [evaluation_results]
            # Flatten multiple subjects
            flat_results = []
            for r in evaluation_results:
                if isinstance(r, list):
                    flat_results.extend(r)
                else:
                    flat_results.append(r)
            # Convert to DataFrame for analysis
            df = pd.DataFrame(
                [
                    {
                        "model": r["model"],
                        "options": json.dumps(r.get("options", {}), ensure_ascii=False),
                        "accuracy": r["metrics"]["accuracy"],
                        "correct": r["metrics"]["correct_answers"],
                        "total": r["metrics"]["total_questions"],
                        "subject": r.get("subject", "Unknown Subject"),
                    }
                    for r in flat_results
                ]
            )
            logger.info(f"Converted to DataFrame with {len(df)} records")
            # Generate visualization
            plt.rcParams["font.sans-serif"] = ["SimHei"]  # Show Chinese labels
            plt.rcParams["axes.unicode_minus"] = False  # Show minus sign correctly
            plt.figure(figsize=(12, 7))
            sns.barplot(data=df, x="subject", y="accuracy", hue="model")
            plt.title("Model Accuracy Comparison by Subject")
            plt.ylabel("Accuracy")
            plt.xlabel("Subject")
            plt.ylim(0, 1)
            plt.legend(title="Model")

            if output_path:
                # Append date to ensure uniqueness
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(output_path, date_str)
                os.makedirs(output_path, exist_ok=True)
                plt.savefig(f"{output_path}/accuracy_comparison.png")
                logger.info(
                    f"Saved visualization chart to: {output_path}/accuracy_comparison.png"
                )
                df.to_csv(
                    f"{output_path}/results_summary.csv",
                    index=False,
                    encoding="utf-8-sig",
                )
                logger.info(
                    f"Saved summary results to: {output_path}/results_summary.csv"
                )
                # Output detailed answer results for each model and subject
                for r in flat_results:
                    model_name = r["model"]
                    subject = r.get("subject", "Unknown Subject")
                    results = r.get("results", [])
                    if results:
                        detail_df = pd.DataFrame(results)
                        detail_df.to_csv(
                            f"{output_path}/results_detail_{model_name}_{subject}.csv",
                            index=False,
                            encoding="utf-8-sig",
                        )
                        logger.info(
                            f"Saved detailed results for model {model_name} subject {subject} to: {output_path}/results_detail_{model_name}_{subject}.csv"
                        )
            else:
                plt.show()
                logger.info("Visualization chart displayed")

            # Generate detailed report text
            report = "Model Evaluation Report\n\n"
            report += "Accuracy Comparison (by Subject):\n"
            report += df.to_string(index=False) + "\n\n"
            report += "Model Parameters (options):\n"
            for idx, row in df.iterrows():
                report += f"{row['model']} [{row['subject']}]: {row['options']}\n"
            report += "\n"
            logger.info("Report text generated")
            return report
        except Exception as e:
            logger.exception(
                f"Exception occurred while generating evaluation report: {e}"
            )
            raise
