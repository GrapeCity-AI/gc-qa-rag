#!/usr/bin/env python3
"""
对比脚本B - 比较PostgreSQL+pgvector vs MySQL+Qdrant在电子表格技术文档问答上的性能

专门针对SpreadJS技术问题的benchmark分析

用法：
python compare_benchmark.py result_pgvector.json result_qdrant.json
"""

import json
import sys
from typing import Dict, List
import statistics

def load_result_file(filename: str) -> Dict:
    """加载结果文件"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到文件: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"❌ 文件格式错误: {filename}")
        return None

def extract_metrics(result_data: Dict) -> Dict:
    """提取关键指标"""
    if not result_data or "error" in result_data:
        return None

    test_info = result_data.get("test_info", {})
    detailed_results = result_data.get("detailed_results", [])

    # 提取响应时间
    successful_results = [r for r in detailed_results if r["success"]]
    response_times = [r["response_time_ms"] for r in successful_results]

    # 提取答案数量
    hits_counts = [r["hits_count"] for r in successful_results]

    return {
        "total_questions": test_info.get("total_questions", 0),
        "successful_queries": test_info.get("successful_queries", 0),
        "success_rate": test_info.get("success_rate", 0),
        "avg_response_time": test_info.get("average_response_time_ms", 0),
        "response_times": response_times,
        "avg_hits_count": statistics.mean(hits_counts) if hits_counts else 0,
        "p50_response_time": statistics.median(response_times) if response_times else 0,
        "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 5 else 0,  # 95%
        "min_response_time": min(response_times) if response_times else 0,
        "max_response_time": max(response_times) if response_times else 0,
        # 准确度指标
        "questions_with_ground_truth": test_info.get("questions_with_ground_truth", 0),
        "avg_document_match_rate": test_info.get("average_document_match_rate", 0),
        "avg_answer_similarity": test_info.get("average_answer_similarity", 0),
        "avg_accuracy_score": test_info.get("average_accuracy_score", 0),
    }

def generate_benchmark_report(pgvector_data: Dict, qdrant_data: Dict) -> Dict:
    """生成benchmark对比报告"""
    pg_metrics = extract_metrics(pgvector_data)
    qd_metrics = extract_metrics(qdrant_data)

    if not pg_metrics or not qd_metrics:
        return {"error": "无法提取指标数据"}

    # 计算性能差异
    def calc_diff_percent(pg_val, qd_val):
        if qd_val == 0:
            return 0
        return round(((pg_val - qd_val) / qd_val) * 100, 1)

    def determine_winner(pg_val, qd_val, lower_is_better=True):
        if lower_is_better:
            return "pgvector" if pg_val < qd_val else "qdrant"
        else:
            return "pgvector" if pg_val > qd_val else "qdrant"

    benchmark = {
        "test_overview": {
            "pgvector": {
                "total_questions": pg_metrics["total_questions"],
                "successful_queries": pg_metrics["successful_queries"],
                "success_rate": f"{pg_metrics['success_rate']:.1%}"
            },
            "qdrant": {
                "total_questions": qd_metrics["total_questions"],
                "successful_queries": qd_metrics["successful_queries"],
                "success_rate": f"{qd_metrics['success_rate']:.1%}"
            }
        },

        "performance_comparison": {
            "average_response_time": {
                "pgvector_ms": pg_metrics["avg_response_time"],
                "qdrant_ms": qd_metrics["avg_response_time"],
                "difference_percent": calc_diff_percent(pg_metrics["avg_response_time"], qd_metrics["avg_response_time"]),
                "winner": determine_winner(pg_metrics["avg_response_time"], qd_metrics["avg_response_time"])
            },

            "p95_response_time": {
                "pgvector_ms": pg_metrics["p95_response_time"],
                "qdrant_ms": qd_metrics["p95_response_time"],
                "difference_percent": calc_diff_percent(pg_metrics["p95_response_time"], qd_metrics["p95_response_time"]),
                "winner": determine_winner(pg_metrics["p95_response_time"], qd_metrics["p95_response_time"])
            },

            "average_hits_count": {
                "pgvector": round(pg_metrics["avg_hits_count"], 1),
                "qdrant": round(qd_metrics["avg_hits_count"], 1),
                "difference_percent": calc_diff_percent(pg_metrics["avg_hits_count"], qd_metrics["avg_hits_count"], ),
                "winner": determine_winner(pg_metrics["avg_hits_count"], qd_metrics["avg_hits_count"], lower_is_better=False)
            }
        },

        "accuracy_comparison": {
            "document_match_rate": {
                "pgvector": round(pg_metrics["avg_document_match_rate"], 3),
                "qdrant": round(qd_metrics["avg_document_match_rate"], 3),
                "difference_percent": calc_diff_percent(pg_metrics["avg_document_match_rate"], qd_metrics["avg_document_match_rate"]),
                "winner": determine_winner(pg_metrics["avg_document_match_rate"], qd_metrics["avg_document_match_rate"], lower_is_better=False)
            },

            "answer_similarity": {
                "pgvector": round(pg_metrics["avg_answer_similarity"], 3),
                "qdrant": round(qd_metrics["avg_answer_similarity"], 3),
                "difference_percent": calc_diff_percent(pg_metrics["avg_answer_similarity"], qd_metrics["avg_answer_similarity"]),
                "winner": determine_winner(pg_metrics["avg_answer_similarity"], qd_metrics["avg_answer_similarity"], lower_is_better=False)
            },

            "overall_accuracy": {
                "pgvector": round(pg_metrics["avg_accuracy_score"], 3),
                "qdrant": round(qd_metrics["avg_accuracy_score"], 3),
                "difference_percent": calc_diff_percent(pg_metrics["avg_accuracy_score"], qd_metrics["avg_accuracy_score"]),
                "winner": determine_winner(pg_metrics["avg_accuracy_score"], qd_metrics["avg_accuracy_score"], lower_is_better=False)
            },

            "questions_evaluated": {
                "pgvector": pg_metrics["questions_with_ground_truth"],
                "qdrant": qd_metrics["questions_with_ground_truth"]
            }
        },

        "detailed_metrics": {
            "pgvector": pg_metrics,
            "qdrant": qd_metrics
        }
    }

    return benchmark

def print_benchmark_table(benchmark: Dict):
    """打印benchmark对比表格"""
    if "error" in benchmark:
        print(f"❌ {benchmark['error']}")
        return

    print("\n" + "="*80)
    print("🏆 PostgreSQL+pgvector vs MySQL+Qdrant Benchmark 报告")
    print("📊 电子表格技术文档问答性能对比")
    print("="*80)

    # 测试概览
    overview = benchmark["test_overview"]
    print(f"\n📊 测试概览")
    print(f"{'指标':<20} {'pgvector':<15} {'qdrant':<15}")
    print("-" * 50)
    print(f"{'总问题数':<20} {overview['pgvector']['total_questions']:<15} {overview['qdrant']['total_questions']:<15}")
    print(f"{'成功查询数':<20} {overview['pgvector']['successful_queries']:<15} {overview['qdrant']['successful_queries']:<15}")
    print(f"{'成功率':<20} {overview['pgvector']['success_rate']:<15} {overview['qdrant']['success_rate']:<15}")

    # 性能对比
    perf = benchmark["performance_comparison"]
    print(f"\n🚀 性能对比")
    print("-" * 70)

    # 平均响应时间
    avg_rt = perf["average_response_time"]
    print(f"平均响应时间:")
    print(f"  pgvector: {avg_rt['pgvector_ms']:.1f} ms")
    print(f"  qdrant:   {avg_rt['qdrant_ms']:.1f} ms")
    print(f"  差异:     {avg_rt['difference_percent']:+.1f}% (获胜者: {avg_rt['winner']})")

    # P95响应时间
    p95_rt = perf["p95_response_time"]
    print(f"\nP95响应时间:")
    print(f"  pgvector: {p95_rt['pgvector_ms']:.1f} ms")
    print(f"  qdrant:   {p95_rt['qdrant_ms']:.1f} ms")
    print(f"  差异:     {p95_rt['difference_percent']:+.1f}% (获胜者: {p95_rt['winner']})")

    # 平均结果数量
    hits = perf["average_hits_count"]
    print(f"\n平均结果数量:")
    print(f"  pgvector: {hits['pgvector']:.1f} 个")
    print(f"  qdrant:   {hits['qdrant']:.1f} 个")
    print(f"  差异:     {hits['difference_percent']:+.1f}% (获胜者: {hits['winner']})")

        # 准确度对比
    accuracy = benchmark.get("accuracy_comparison", {})
    if accuracy and accuracy.get("questions_evaluated", {}).get("pgvector", 0) > 0:
        print(f"\n🎯 准确度对比 (基于标准答案评估)")
        print("-" * 50)

        doc_match = accuracy["document_match_rate"]
        print(f"文档匹配率:")
        print(f"  pgvector: {doc_match['pgvector']:.1%}")
        print(f"  qdrant:   {doc_match['qdrant']:.1%}")
        print(f"  差异:     {doc_match['difference_percent']:+.1f}% (获胜者: {doc_match['winner']})")

        ans_sim = accuracy["answer_similarity"]
        print(f"\n答案相似度:")
        print(f"  pgvector: {ans_sim['pgvector']:.1%}")
        print(f"  qdrant:   {ans_sim['qdrant']:.1%}")
        print(f"  差异:     {ans_sim['difference_percent']:+.1f}% (获胜者: {ans_sim['winner']})")

        overall = accuracy["overall_accuracy"]
        print(f"\n综合准确度:")
        print(f"  pgvector: {overall['pgvector']:.1%}")
        print(f"  qdrant:   {overall['qdrant']:.1%}")
        print(f"  差异:     {overall['difference_percent']:+.1f}% (获胜者: {overall['winner']})")

        questions_eval = accuracy["questions_evaluated"]
        print(f"\n评估问题数: {questions_eval['pgvector']} vs {questions_eval['qdrant']}")

    # 总结
    print(f"\n🏆 Benchmark 总结")
    print("-" * 30)

    # 性能指标
    perf_winners = [avg_rt['winner'], p95_rt['winner'], hits['winner']]

    # 准确度指标
    accuracy_winners = []
    if accuracy and accuracy.get("questions_evaluated", {}).get("pgvector", 0) > 0:
        accuracy_winners = [
            accuracy["document_match_rate"]['winner'],
            accuracy["answer_similarity"]['winner'],
            accuracy["overall_accuracy"]['winner']
        ]

    all_winners = perf_winners + accuracy_winners
    pgvector_wins = all_winners.count('pgvector')
    qdrant_wins = all_winners.count('qdrant')

    print(f"性能维度: pgvector {perf_winners.count('pgvector')}/3, qdrant {perf_winners.count('qdrant')}/3")
    if accuracy_winners:
        print(f"准确度维度: pgvector {accuracy_winners.count('pgvector')}/3, qdrant {accuracy_winners.count('qdrant')}/3")

    if pgvector_wins > qdrant_wins:
        print("🥇 综合获胜者: PostgreSQL+pgvector")
    elif qdrant_wins > pgvector_wins:
        print("🥇 综合获胜者: MySQL+Qdrant")
    else:
        print("🤝 综合表现相当")

    print("="*80)

def save_benchmark_report(benchmark: Dict, filename: str):
    """保存benchmark报告"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(benchmark, f, indent=2, ensure_ascii=False)
    print(f"📁 详细报告已保存: {filename}")

def main():
    if len(sys.argv) != 3:
        print("用法: python compare_benchmark.py <pgvector结果文件> <qdrant结果文件>")
        print("示例: python compare_benchmark.py result_pgvector.json result_qdrant.json")
        print("说明: 对比两种架构在SpreadJS技术文档问答上的性能")
        sys.exit(1)

    pgvector_file = sys.argv[1]
    qdrant_file = sys.argv[2]

    # 加载数据
    print(f"📂 加载测试结果...")
    pgvector_data = load_result_file(pgvector_file)
    qdrant_data = load_result_file(qdrant_file)

    if not pgvector_data or not qdrant_data:
        sys.exit(1)

    # 生成benchmark报告
    benchmark = generate_benchmark_report(pgvector_data, qdrant_data)

    # 打印报告
    print_benchmark_table(benchmark)

    # 保存详细报告
    save_benchmark_report(benchmark, "benchmark_report.json")

if __name__ == "__main__":
    main()
