# Agentic 模式使用说明

## 概述

现在系统支持三种评估模式：

1. **无上下文模式** (`--no-flags`): 直接向模型提问，不提供任何检索信息
2. **预检索模式** (`--with_context`): 预先检索相关信息作为上下文提供给模型
3. **Agentic 模式** (`--agentic`): 让模型自主决定何时以及如何使用检索工具 ⭐️**新功能**

## Agentic 模式特点

在 Agentic 模式下：

-   模型获得`search_knowledge_base`工具的调用能力
-   模型可以自主决定搜索关键词和搜索时机
-   支持多轮搜索，模型可以根据初步搜索结果进行进一步探索
-   模型会自主判断何时停止搜索并给出最终答案

## 使用方法

### 命令行使用

```bash
# 使用agentic模式评估
python app/main.py --agentic --models "eric/claude-sonnet-4-20250514" --max_questions 10

# 比较不同模式的效果
python app/main.py --with_context --models "eric/claude-sonnet-4-20250514" --max_questions 10
python app/main.py --agentic --models "eric/claude-sonnet-4-20250514" --max_questions 10
```

### 程序化使用

```python
from app.eval import EvaluationEngine
from app.llm import OpenAIImplementation
from app.query import KnowledgeBaseClient
from app.question import QuestionBank

# 初始化组件
question_bank = QuestionBank(".data/questions_full.xlsx")
kb_client = KnowledgeBaseClient()
engine = EvaluationEngine(question_bank, kb_client)

# 创建模型
model = OpenAIImplementation(
    model_name="claude-sonnet-4-20250514",
    api_key="your_api_key",
    api_base="your_api_base"
)

# 运行agentic模式评估
result = engine.evaluate_model_by_subject(
    llm=model,
    subject="活字格认证工程师-科目一",
    agentic_mode=True,  # 启用agentic模式
    parallel_count=1,
    max_questions=10
)
```

## 工作流程

1. **问题分析**: 模型首先分析题目，理解需要什么信息
2. **自主搜索**: 模型决定搜索关键词，调用`search_knowledge_base`工具
3. **结果评估**: 模型评估搜索结果，决定是否需要进一步搜索
4. **迭代搜索**: 如需要，模型会使用不同关键词进行多轮搜索
5. **答案生成**: 综合所有信息，生成最终答案

## 搜索工具说明

### search_knowledge_base 函数

-   **参数**:

    -   `query` (必需): 搜索关键词或查询字符串

-   **返回**: JSON 格式的搜索结果，包含相关文档片段和评分

### 示例搜索过程

```
用户问题: "活字格中如何实现数据验证?"

模型可能的搜索序列:
1. search_knowledge_base(keyword="活字格 数据验证", product="forguncy")
2. search_knowledge_base(keyword="表单验证 规则", product="forguncy")
3. search_knowledge_base(keyword="输入控件 验证", product="forguncy")

最终基于搜索结果生成答案。
```

## 配置选项

-   `max_iterations`: 最大搜索轮次 (默认: 10)
-   `parallel_count`: 并行处理线程数
-   `max_questions`: 每个科目最大题目数

## 性能比较

建议使用相同的题目集合比较三种模式的效果：

| 模式     | 优点                 | 缺点               |
| -------- | -------------------- | ------------------ |
| 无上下文 | 速度快，成本低       | 准确率可能较低     |
| 预检索   | 信息全面，一次性提供 | 可能包含无关信息   |
| Agentic  | 精确搜索，多轮探索   | 耗时较长，成本较高 |

## 日志监控

启用 DEBUG 级别日志可以观察模型的搜索过程：

```python
logging.basicConfig(level=logging.DEBUG)
```

这将显示：

-   每次 function call 的参数
-   搜索结果的数量
-   迭代轮次信息

## 故障排除

1. **模型不调用搜索工具**: 检查模型是否支持 function calling
2. **搜索结果为空**: 检查知识库服务是否正常运行
3. **无限循环**: 调整`max_iterations`参数
4. **API 错误**: 检查 API 密钥和模型名称配置

## 示例脚本

运行 `agentic_example.py` 查看完整的使用示例。
