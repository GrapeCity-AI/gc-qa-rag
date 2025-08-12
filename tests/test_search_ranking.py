#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG搜索排名测试脚本 - 专注于搜索结果收集
获取前8个排名结果，完整保存RAG检索数据
"""

import json
import time
import asyncio
import aiohttp
import argparse
from typing import List, Dict, Any
from datetime import datetime
import uuid
from ground_truth_parser import parse_qa_list, get_question_ground_truth

class SearchRankingTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ground_truth = parse_qa_list()
        self.session_id = str(uuid.uuid4())
        print(f"✅ 加载了 {len(self.ground_truth)} 个标准答案用于准确度评估")
        print(f"🔑 会话ID: {self.session_id}")

    def load_questions(self, questions_file: str = 'test_queries.json') -> List[str]:
        """加载问题列表"""
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('queries', [])
        except Exception as e:
            print(f"❌ 无法加载问题文件 {questions_file}: {e}")
            return []

    def extract_source_documents(self, hits: List[Dict]) -> List[str]:
        """从hits中提取源文档名称"""
        source_docs = []
        for hit in hits:
            payload = hit.get('payload', {})
            doc_name = (
                payload.get('title') or
                payload.get('source_doc') or
                payload.get('file_name') or
                payload.get('url', '').split('/')[-1]
            )
            if doc_name and doc_name not in source_docs:
                source_docs.append(doc_name)
        return source_docs

    def calculate_accuracy_metrics(self, question: str, hits: List[Dict]) -> Dict[str, Any]:
        """计算准确度指标"""
        gt_info = get_question_ground_truth(question, self.ground_truth)

        if not gt_info:
            return {"has_ground_truth": False}

        # 获取检索到的文档和参考文档
        retrieved_docs = self.extract_source_documents(hits)
        reference_docs = gt_info.get('reference_docs', [])

        # 文档匹配率计算
        if not reference_docs:
            doc_match_rate = 1.0
        else:
            matched_docs = set(retrieved_docs) & set(reference_docs)
            doc_match_rate = len(matched_docs) / len(reference_docs)

        return {
            "has_ground_truth": True,
            "reference_docs": reference_docs,
            "retrieved_docs": retrieved_docs,
            "document_match_rate": round(doc_match_rate, 3),
            "matched_documents": list(set(retrieved_docs) & set(reference_docs)),
            "missing_documents": list(set(reference_docs) - set(retrieved_docs)),
            "extra_documents": list(set(retrieved_docs) - set(reference_docs)),
            "standard_answer": gt_info.get('standard_answer', '')
        }

    async def search_single_question(self, question: str, session_index: int = 0) -> Dict[str, Any]:
        """搜索单个问题，获取排名前8的结果"""
        start_time = time.perf_counter()

        try:
            async with aiohttp.ClientSession() as session:
                # 模拟前端请求格式
                payload = {
                    "keyword": question,
                    "mode": "chat",
                    "product": "bbb",
                    "session_id": self.session_id,
                    "session_index": session_index
                }

                print(f"🔍 [DEBUG] 搜索请求: {question[:50]}...")

                async with session.post(
                    f"{self.base_url}/search/",
                    json=payload,
                    headers={
                        "accept": "*/*",
                        "content-type": "application/json"
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    end_time = time.perf_counter()
                    response_time = (end_time - start_time) * 1000

                    print(f"📡 [DEBUG] 响应状态: {response.status}, 时间: {response_time:.2f}ms")

                    if response.status == 200:
                        result = await response.json()

                        # 处理响应格式
                        if isinstance(result, list):
                            hits = result
                        elif isinstance(result, dict):
                            hits = result.get('hits', result.get('data', []))
                        else:
                            hits = []

                        # 取前8个结果
                        top_hits = hits[:8]
                        print(f"✅ [DEBUG] 获取 {len(top_hits)} 个搜索结果")

                        # 提取完整的搜索结果信息
                        search_results = []
                        for i, hit in enumerate(top_hits, 1):
                            payload_data = hit.get('payload', {})
                            search_results.append({
                                "rank": i,
                                "score": hit.get('score', 0),
                                "answer": payload_data.get('answer', ''),
                                "title": payload_data.get('title', ''),
                                "url": payload_data.get('url', ''),
                                "summary": payload_data.get('summary', ''),
                                "question": payload_data.get('question', ''),
                                "product": payload_data.get('product', ''),
                                "category": payload_data.get('category', ''),
                                "file_index": payload_data.get('file_index', ''),
                                "collection_category": payload_data.get('collection_category', '')
                            })

                        # 计算准确度指标
                        accuracy_metrics = self.calculate_accuracy_metrics(question, top_hits)

                        # 提取所有参考文档
                        all_source_docs = self.extract_source_documents(top_hits)

                        return {
                            "question": question,
                            "success": True,
                            "response_time_ms": round(response_time, 2),
                            "total_hits": len(hits),
                            "top_8_results": search_results,  # 完整的前8个结果
                            "all_source_docs": all_source_docs,
                            "accuracy_metrics": accuracy_metrics,
                            "session_info": {
                                "session_id": self.session_id,
                                "session_index": session_index
                            }
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ [DEBUG] HTTP错误 {response.status}: {error_text[:200]}...")

                        return {
                            "question": question,
                            "success": False,
                            "response_time_ms": round(response_time, 2),
                            "error": f"HTTP {response.status}: {error_text[:100]}",
                            "total_hits": 0,
                            "top_8_results": [],
                            "all_source_docs": [],
                            "accuracy_metrics": self.calculate_accuracy_metrics(question, []),
                            "session_info": {
                                "session_id": self.session_id,
                                "session_index": session_index
                            }
                        }

        except Exception as e:
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000
            print(f"❌ [DEBUG] 请求异常: {str(e)}")

            return {
                "question": question,
                "success": False,
                "response_time_ms": round(response_time, 2),
                "error": str(e),
                "total_hits": 0,
                "top_8_results": [],
                "all_source_docs": [],
                "accuracy_metrics": self.calculate_accuracy_metrics(question, []),
                "session_info": {
                    "session_id": self.session_id,
                    "session_index": session_index
                }
            }

    async def run_all_searches(self, questions_file: str = 'test_queries.json') -> Dict[str, Any]:
        """运行所有搜索"""
        questions = self.load_questions(questions_file)

        if not questions:
            return {"error": "没有加载到任何问题"}

        print(f"📋 开始搜索 {len(questions)} 个SpreadJS技术问题...")
        results = []

        for i, question in enumerate(questions):
            print(f"  {i+1}/{len(questions)}: {question[:80]}...")
            result = await self.search_single_question(question, session_index=i)
            results.append(result)

            # 简短的进度反馈
            if result['success']:
                top_result = result['top_8_results'][0] if result['top_8_results'] else {}
                preview = top_result.get('answer', '')[:100] + ("..." if len(top_result.get('answer', '')) > 100 else "")
                print(f"    ✅ {result['response_time_ms']:.0f}ms, {result['total_hits']}个结果 - {preview}")
            else:
                print(f"    ❌ {result.get('error', 'Unknown error')}")

        # 计算统计信息
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]

        if successful_results:
            response_times = [r['response_time_ms'] for r in successful_results]
            total_hits = [r['total_hits'] for r in successful_results]
            avg_response_time = sum(response_times) / len(response_times)
            avg_hits = sum(total_hits) / len(total_hits)
        else:
            avg_response_time = avg_hits = 0

        # 准确度统计
        accuracy_results = [r for r in successful_results if r.get("accuracy_metrics", {}).get("has_ground_truth", False)]
        if accuracy_results:
            avg_doc_match_rate = sum([r["accuracy_metrics"]["document_match_rate"] for r in accuracy_results]) / len(accuracy_results)
        else:
            avg_doc_match_rate = 0.0

        print(f"\n✅ 搜索完成！成功: {len(successful_results)}/{len(questions)}")
        print(f"📊 平均响应时间: {avg_response_time:.1f}ms")
        print(f"📊 平均搜索结果: {avg_hits:.1f}个")
        print(f"🎯 准确度统计 ({len(accuracy_results)}个问题有标准答案):")
        print(f"   文档匹配率: {avg_doc_match_rate:.1%}")

        return {
            "test_info": {
                "timestamp": time.time(),
                "test_type": "search_ranking",
                "session_id": self.session_id,
                "total_questions": len(questions),
                "successful_queries": len(successful_results),
                "failed_queries": len(failed_results),
                "success_rate": len(successful_results) / len(questions) if questions else 0,
                "average_response_time_ms": avg_response_time,
                "average_hits_count": avg_hits,
                "questions_with_ground_truth": len(accuracy_results),
                "average_document_match_rate": avg_doc_match_rate
            },
            "detailed_results": results
        }

def main():
    parser = argparse.ArgumentParser(description='RAG搜索排名测试脚本')
    parser.add_argument('--output', help='输出结果文件名(JSON格式)', default='search_ranking_results.json')
    parser.add_argument('--url', default='http://localhost:8000', help='RAG服务URL')
    parser.add_argument('--test', action='store_true', help='仅测试单个查询')
    parser.add_argument('--question', help='测试单个问题的内容')
    parser.add_argument('--questions-file', default='test_queries.json', help='问题文件路径')

    args = parser.parse_args()

    async def run_test():
        tester = SearchRankingTester(args.url)

        if args.test:
            # 测试单个问题
            question = args.question if args.question else "如何创建相机视图"
            print(f"🧪 [TEST] 测试单个搜索: {question}...")
            result = await tester.search_single_question(question)

            print(f"\n📊 搜索结果:")
            print(f"   成功: {result['success']}")
            print(f"   响应时间: {result['response_time_ms']:.2f}ms")
            print(f"   总结果数: {result['total_hits']}")
            print(f"   前8结果: {len(result['top_8_results'])}个")
            if result['top_8_results']:
                print(f"   第1名答案: {result['top_8_results'][0]['answer'][:100]}...")
            return

        # 运行完整搜索测试
        results = await tester.run_all_searches(args.questions_file)

        if "error" in results:
            print(f"❌ 测试失败: {results['error']}")
            return

        # 保存JSON结果
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"📁 搜索结果已保存到: {args.output}")
        print("💡 使用Markdown生成器创建详细报告:")
        print(f"   python generate_markdown_report.py {args.output}")

    # 运行测试
    asyncio.run(run_test())

if __name__ == "__main__":
    main()
