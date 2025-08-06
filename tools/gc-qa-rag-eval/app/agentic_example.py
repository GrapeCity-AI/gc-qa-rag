#!/usr/bin/env python3
"""
Agentic模式使用示例

本示例展示如何使用新实现的agentic模式来评估模型。
在agentic模式下，大模型会自主决定何时以及如何使用检索工具来获取信息，
而不是预先提供所有上下文。
"""

import logging
from app.eval import EvaluationEngine
from app.llm import OpenAIImplementation
from app.query import KnowledgeBaseClient
from app.question import QuestionBank


def main():
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # 初始化组件
    question_bank = QuestionBank(".data/questions_full.xlsx")
    kb_client = KnowledgeBaseClient()
    engine = EvaluationEngine(question_bank, kb_client)
    
    # 创建模型实例 - 这里使用你的API配置
    model = OpenAIImplementation(
        model_name="claude-sonnet-4-20250514",
        api_key="cr_5e7e3d5bfb17cf15d55b7c7b96cb8e10825c4cd923ee53373105506461d2f215",
        api_base="https://claude.edricli.com/openai/claude/v1",
    )
    
    # 选择一个科目进行测试
    subjects = question_bank.get_subjects()
    test_subject = "活字格认证工程师-科目一"
    
    # 测试题数
    max_questions = 10

    print(f"开始使用agentic模式测试科目: {test_subject}")
    print("=" * 50)
    
    # 运行agentic模式评估
    result = engine.evaluate_model_by_subject(
        llm=model,
        subject=test_subject,
        parallel_count=1,  # 单线程方便观察过程
        max_questions=max_questions,   # 只测试10道题
        agentic_mode=True  # 启用agentic模式
    )
    
    # 打印结果
    print(f"\n评估完成!")
    print(f"模型: {result['model']}")
    print(f"科目: {result['subject']}")
    print(f"模式: {result['evaluation_mode']}")
    print(f"准确率: {result['metrics']['accuracy']:.2%}")
    print(f"正确题数: {result['metrics']['correct_answers']}/{result['metrics']['total_questions']}")
    
    # 显示详细结果
    print("\n详细结果:")
    print("-" * 50)
    for i, question_result in enumerate(result['results'][:max_questions], 1):
        print(f"题目 {i}:")
        print(f"  问题: {question_result['question'][:100]}...")
        print(f"  正确答案: {question_result['correct_answer']}")
        print(f"  模型答案: {question_result['model_answer'][:200]}...")
        print(f"  得分: {question_result['score']}")
        print(f"  反馈: {question_result['feedback']}")
        print()


if __name__ == "__main__":
    main() 