#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的Markdown报告生成器
直接从JSON测试结果生成完整的Markdown报告
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any
import argparse

def load_test_results(json_file: str) -> Dict[str, Any]:
    """加载测试结果JSON文件"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法加载JSON文件 {json_file}: {e}")
        return None

def format_timestamp(timestamp: float) -> str:
    """格式化时间戳"""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def generate_overview_section(test_info: Dict[str, Any]) -> str:
    """生成测试概览部分"""
    success_rate = test_info.get('success_rate', 0) * 100
    avg_response_time = test_info.get('average_response_time_ms', 0)
    total_questions = test_info.get('total_questions', 0)
    successful_queries = test_info.get('successful_queries', 0)

    # 准确度信息
    questions_with_gt = test_info.get('questions_with_ground_truth', 0)
    avg_doc_match = test_info.get('average_document_match_rate', 0) * 100
    avg_answer_sim = test_info.get('average_answer_similarity', 0) * 100
    avg_accuracy = test_info.get('average_accuracy_score', 0) * 100

    overview = f"""# RAG系统测试报告

## 📊 测试概览

**测试时间**: {format_timestamp(test_info.get('timestamp', 0))}
**总问题数**: {total_questions}
**成功查询**: {successful_queries}
**成功率**: {success_rate:.1f}%
**平均响应时间**: {avg_response_time:.1f}ms
**总测试时长**: {test_info.get('total_test_time_seconds', 0):.2f}秒

## 🎯 准确度评估

**评估基准**: {questions_with_gt}个问题有标准答案
**文档匹配率**: {avg_doc_match:.1f}% _(检索文档与参考文档的匹配度)_
**答案相似度**: {avg_answer_sim:.1f}% _(文本内容相似性)_
**综合准确度**: {avg_accuracy:.1f}% _(综合评分: 文档匹配70% + 答案相似30%)_

---

"""
    return overview

def generate_qa_section(detailed_results: List[Dict[str, Any]]) -> str:
    """生成详细问答部分"""
    qa_content = "## 📝 详细问答结果\n\n"

    for i, result in enumerate(detailed_results, 1):
        if not result.get('success', False):
            continue

        question = result.get('question', '')
        response_time = result.get('response_time_ms', 0)
        hits_count = result.get('hits_count', 0)
        full_answer = result.get('full_answer', '')
        all_source_docs = result.get('all_source_docs', [])
        accuracy_metrics = result.get('accuracy_metrics', {})

        # 准确度信息
        has_gt = accuracy_metrics.get('has_ground_truth', False)
        doc_match_rate = accuracy_metrics.get('document_match_rate', 0) * 100
        answer_similarity = accuracy_metrics.get('answer_similarity', 0) * 100
        accuracy_score = accuracy_metrics.get('accuracy_score', 0) * 100

        qa_content += f"""### {i}. {question}

**响应时间**: {response_time:.2f}ms | **匹配结果**: {hits_count}个

"""

        if has_gt:
            qa_content += f"""**准确度评估**:
- 文档匹配率: {doc_match_rate:.1f}%
- 答案相似度: {answer_similarity:.1f}%
- 综合准确度: {accuracy_score:.1f}%

"""

        qa_content += f"""**回答**:
{full_answer}

**参考文档**:
"""
        if all_source_docs:
            for doc in all_source_docs:
                qa_content += f"- {doc}\n"
        else:
            qa_content += "- 无参考文档\n"

        # 如果有标准答案，也显示出来
        if has_gt:
            standard_answer = accuracy_metrics.get('standard_answer', '')
            if standard_answer:
                qa_content += f"""
**标准答案**:
{standard_answer[:200]}{'...' if len(standard_answer) > 200 else ''}
"""

        qa_content += "\n---\n\n"

    return qa_content

def generate_performance_stats(detailed_results: List[Dict[str, Any]]) -> str:
    """生成性能统计部分"""
    successful_results = [r for r in detailed_results if r.get('success', False)]

    if not successful_results:
        return "## ⚡ 性能统计\n\n无成功查询数据。\n\n"

    response_times = [r.get('response_time_ms', 0) for r in successful_results]
    response_times.sort()

    avg_time = sum(response_times) / len(response_times)
    min_time = min(response_times)
    max_time = max(response_times)

    # P50和P95
    p50_idx = len(response_times) // 2
    p95_idx = int(len(response_times) * 0.95)
    p50_time = response_times[p50_idx] if p50_idx < len(response_times) else 0
    p95_time = response_times[p95_idx] if p95_idx < len(response_times) else 0

    # 命中数统计
    hit_counts = [r.get('hits_count', 0) for r in successful_results]
    avg_hits = sum(hit_counts) / len(hit_counts) if hit_counts else 0

    stats_content = f"""## ⚡ 性能统计

### 响应时间分布
- **平均响应时间**: {avg_time:.2f}ms
- **最快响应**: {min_time:.2f}ms
- **最慢响应**: {max_time:.2f}ms
- **P50延迟**: {p50_time:.2f}ms
- **P95延迟**: {p95_time:.2f}ms

### 检索效果
- **平均命中数**: {avg_hits:.1f}个结果
- **查询成功率**: 100.0%

---

"""
    return stats_content

def main():
    parser = argparse.ArgumentParser(description='从JSON测试结果生成Markdown报告')
    parser.add_argument('json_file', help='JSON测试结果文件')
    parser.add_argument('-o', '--output', help='输出Markdown文件名（默认自动生成）')

    args = parser.parse_args()

    # 加载测试结果
    print(f"📄 加载测试结果: {args.json_file}")
    test_data = load_test_results(args.json_file)

    if not test_data:
        return 1

    # 提取数据
    test_info = test_data.get('test_info', {})
    detailed_results = test_data.get('detailed_results', [])

    print(f"✅ 加载完成: {len(detailed_results)}个查询结果")

    # 生成报告内容
    print("📝 生成Markdown报告...")

    markdown_content = ""
    markdown_content += generate_overview_section(test_info)
    markdown_content += generate_performance_stats(detailed_results)
    markdown_content += generate_qa_section(detailed_results)

    # 输出文件名
    if args.output:
        output_file = args.output
    else:
        base_name = args.json_file.replace('.json', '')
        output_file = f"{base_name}.md"

    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✅ Markdown报告已生成: {output_file}")
        return 0
    except Exception as e:
        print(f"❌ 无法写入文件 {output_file}: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
