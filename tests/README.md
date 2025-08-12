# RAG搜索质量测试工具

专注于SpreadJS技术文档的RAG搜索排名质量分析和准确度评估。

## 🎯 测试目标

基于30个SpreadJS技术问题，评估RAG系统的：
- **搜索排名质量**：前8个结果的相关性
- **文档匹配准确度**：检索到的文档与标准参考文档的匹配率
- **系统性能指标**：响应时间、成功率等

## 📁 文件说明

### 核心测试工具
- `test_search_ranking.py` - **主要测试脚本**，获取搜索排名前8的完整结果
- `generate_markdown_report.py` - 独立的Markdown报告生成器
- `compare_benchmark.py` - 对比分析脚本（用于A/B测试）
- `ground_truth_parser.py` - 标准答案解析器

### 测试数据
- `test_queries.json` - 30个SpreadJS技术问题
- `qa-list.md` - 问题的标准答案和参考文档
- `rag_data/` - 测试用的知识库文档（30个.md文件）

### 输出文件
- `ranking_results.json` - 搜索排名测试结果
- `search_ranking_report.md` - 详细的分析报告

## 🚀 使用方法

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 基础测试
```bash
# 单个问题测试
python test_search_ranking.py --test --question "如何创建相机视图"

# 完整测试（30个问题）
python test_search_ranking.py --output my_results.json
```

### 3. 生成报告
```bash
python generate_markdown_report.py ranking_results.json -o my_report.md
```

### 4. 对比分析（可选）
```bash
# 比较两次测试结果
python compare_benchmark.py results1.json results2.json
```

## 📊 测试指标

### 性能指标
- **响应时间**：平均、最大、最小响应时间
- **成功率**：成功查询的比例
- **结果数量**：平均返回的搜索结果数

### 准确度指标
- **文档匹配率**：检索到的文档中包含标准参考文档的比例
- **搜索质量**：前8个结果的相关性和排序合理性

## 🎯 典型测试场景

### 场景1：新系统测试
```bash
python test_search_ranking.py --output new_system_results.json
python generate_markdown_report.py new_system_results.json -o new_system_report.md
```

### 场景2：A/B对比测试
```bash
# 第一个版本
python test_search_ranking.py --output version_a.json

# 切换到第二个版本，运行相同测试
python test_search_ranking.py --output version_b.json

# 生成对比报告
python compare_benchmark.py version_a.json version_b.json
```

## 📈 结果解读

### 搜索排名数据结构
每个问题的测试结果包含：
- `top_8_results`: 前8个搜索结果的详细信息
- `accuracy_metrics`: 准确度评估指标
- `all_source_docs`: 所有参考文档列表
- `session_info`: 会话追踪信息

### 准确度评估
- `document_match_rate`: 文档匹配率（0-1）
- `matched_documents`: 匹配到的参考文档
- `missing_documents`: 遗漏的参考文档
- `extra_documents`: 额外检索到的文档

## 🔧 配置选项

### 环境设置
- RAG服务URL：`--url http://localhost:8000`
- 产品标识：默认为 `bbb`
- 问题文件：`--questions-file custom_queries.json`

### 输出控制
- JSON结果：`--output custom_name.json`
- Markdown报告：使用独立的生成器脚本

## 💡 最佳实践

1. **测试前准备**
   - 确保RAG服务运行正常
   - 确认测试数据已正确上传
   - 备份重要的测试结果

2. **结果分析**
   - 关注文档匹配率和排序质量
   - 分析响应时间分布
   - 识别系统性能瓶颈

3. **对比测试**
   - 使用相同的测试数据集
   - 在相同的环境条件下测试
   - 记录系统配置差异

## 📝 注意事项

- 测试脚本会生成唯一的session_id用于会话追踪
- 所有结果数据以JSON格式保存，便于后续分析
- Markdown报告包含详细的问答和排名信息
- 测试过程中会输出实时的调试信息

## 🎯 下一步优化方向

基于测试结果，可能的优化方向：
1. **改进答案选择策略**：考虑多个结果，智能选择最佳答案
2. **调整RRF融合权重**：优化dense/sparse向量平衡
3. **引入语义重排**：基于问题相关性重新排序检索结果