#!/usr/bin/env python3
"""
标准答案解析器 - 解析qa-list.md文件，提取问题、标准答案和参考文档
"""

import re
from typing import Dict, List, Tuple

def parse_qa_list(qa_file_path: str = "qa-list.md") -> Dict[str, Dict]:
    """解析QA列表文件，提取标准答案和参考文档"""
    try:
        with open(qa_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 未找到文件: {qa_file_path}")
        return {}

    # 按问题分割内容
    qa_sections = re.split(r'### Q\d+:', content)[1:]  # 去掉第一个空段

    ground_truth = {}

    for i, section in enumerate(qa_sections, 1):
        lines = section.strip().split('\n')
        if not lines:
            continue

        # 提取问题
        question_line = lines[0].strip()
        if not question_line:
            continue

        # 提取标准答案（**A:** 后面的内容，直到代码块或参考文档）
        answer_lines = []
        ref_docs = []

        in_answer = False
        in_code = False

        for line in lines[1:]:
            line = line.strip()

            # 跳过空行和分隔符
            if not line or line == '---':
                continue

            # 检测答案开始
            if line.startswith('**A:**'):
                in_answer = True
                answer_text = line.replace('**A:**', '').strip()
                if answer_text:
                    answer_lines.append(answer_text)
                continue

            # 检测代码块
            if line.startswith('```'):
                in_code = not in_code
                continue

            # 检测参考文档
            if line.startswith('**参考文档:**'):
                ref_docs_text = line.replace('**参考文档:**', '').strip()
                # 提取文档名（去掉反引号和标点）
                docs = re.findall(r'`([^`]+)`', ref_docs_text)
                if not docs:  # 如果没有反引号，直接分割
                    docs = [doc.strip(' .,`') for doc in ref_docs_text.split(',')]
                ref_docs.extend([doc.strip() for doc in docs if doc.strip()])
                break

            # 收集答案内容（不在代码块中）
            if in_answer and not in_code and not line.startswith('```'):
                answer_lines.append(line)

        # 组装结果
        if question_line and answer_lines:
            question = question_line
            answer = ' '.join(answer_lines)

            ground_truth[question] = {
                'question': question,
                'standard_answer': answer,
                'reference_docs': ref_docs,
                'question_id': f'Q{i}'
            }

    print(f"✅ 解析完成，共 {len(ground_truth)} 个问题的标准答案")
    return ground_truth

def get_question_ground_truth(question: str, ground_truth: Dict) -> Dict:
    """根据问题文本获取对应的标准答案信息"""
    # 直接匹配
    if question in ground_truth:
        return ground_truth[question]

    # 模糊匹配（去掉标点符号和空格后比较）
    question_normalized = re.sub(r'[^\w]', '', question)

    for gt_question, gt_data in ground_truth.items():
        gt_normalized = re.sub(r'[^\w]', '', gt_question)
        if question_normalized == gt_normalized:
            return gt_data

    # 部分匹配（找到包含关键词最多的问题）
    best_match = None
    max_match_score = 0

    question_words = set(re.findall(r'\w+', question))

    for gt_question, gt_data in ground_truth.items():
        gt_words = set(re.findall(r'\w+', gt_question))
        match_score = len(question_words & gt_words)

        if match_score > max_match_score and match_score >= 3:  # 至少匹配3个词
            max_match_score = match_score
            best_match = gt_data

    return best_match or {}

if __name__ == "__main__":
    # 测试解析功能
    ground_truth = parse_qa_list()

    if ground_truth:
        print(f"\n📋 解析结果示例:")
        first_key = next(iter(ground_truth))
        first_qa = ground_truth[first_key]
        print(f"问题: {first_qa['question'][:60]}...")
        print(f"答案: {first_qa['standard_answer'][:100]}...")
        print(f"参考文档: {first_qa['reference_docs']}")
