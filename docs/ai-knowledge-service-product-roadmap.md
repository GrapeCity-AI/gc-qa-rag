# AI 知识服务 ETL - 产品路线图

> 本文档定义 AI 知识服务 ETL 层的产品路线图，从基础框架到生产化部署的全阶段规划。

---

## 一、ETL 服务架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ETL 服务架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         用户层 (User Layer)                          │   │
│   │  ┌───────────────────────────────┐  ┌───────────────────────────┐   │   │
│   │  │         管理控制台 (Admin)      │  │        CLI 工具            │   │   │
│   │  └───────────────────────────────┘  └───────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         API 层 (API Layer)                           │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│   │  │ 知识库 API  │  │  版本 API   │  │  任务 API   │  │ WebSocket  │  │   │
│   │  │ /kb        │  │ /versions   │  │ /tasks      │  │  /ws       │  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                       服务层 (Service Layer)                         │   │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │   │
│   │  │    Ingestion    │  │    Indexing     │  │    Publishing       │  │   │
│   │  │   (数据采集)     │  │   (索引构建)     │  │    (发布部署)        │  │   │
│   │  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                       抽象层 (Abstraction Layer)                     │   │
│   │                           接口定义、领域模型                          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     基础设施层 (Infrastructure)                       │   │
│   │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │   │
│   │  │ Qdrant │ │ SQLite │ │ Redis  │ │  LLM   │ │Embedding│ │  FS    │ │   │
│   │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、阶段规划

### Phase 1: 基础框架

**目标**: 让抽象层可运行，建立开发基础

**状态**: ✅ 完成

| 任务 | 说明 | 状态 |
|------|------|------|
| 抽象层设计文档 | 完整的接口设计文档 | ✅ 完成 |
| 抽象层代码 | 所有接口定义 | ✅ 完成 |
| DI 容器实现 | 简单依赖注入容器 | ✅ 完成 |
| 内存队列实现 | 开发用任务队列 | ✅ 完成 |
| 日志实现 | 控制台日志输出 | ✅ 完成 |
| 文件存储实现 | 文件系统 + SQLite | ✅ 完成 |
| 版本管理器实现 | SQLite 版本管理 | ✅ 完成 |
| 单元测试 | 全组件测试覆盖 (154 tests) | ✅ 完成 |

**产出物**:
```
implementations/
├── infrastructure/
│   ├── simple_container.py          # DI 容器
│   ├── memory_queue.py              # 内存任务队列
│   ├── memory_event_bus.py          # 内存事件总线
│   └── sqlite_version_manager.py    # 版本管理器
├── observability/
│   ├── console_logger.py            # 控制台日志
│   ├── noop_metrics.py              # 空操作 metrics
│   └── noop_tracer.py               # 空操作 tracer
└── storage/
    ├── filesystem_content_store.py  # 文件内容存储
    ├── sqlite_metadata_store.py     # SQLite 元数据
    └── composite_raw_file_storage.py # 组合存储

tests/
├── conftest.py                      # 测试配置和 fixtures
├── test_simple_container.py         # DI 容器测试 (24 tests)
├── test_memory_event_bus.py         # 事件总线测试 (15 tests)
├── test_memory_queue.py             # 任务队列测试 (29 tests)
├── test_console_logger.py           # 日志测试 (23 tests)
├── test_storage.py                  # 存储测试 (26 tests)
└── test_version_manager.py          # 版本管理测试 (37 tests)
```

---

### Phase 2: 核心管道

**目标**: ETL 管道可端到端运行

**状态**: ⏳ 待开始

| 任务 | 说明 |
|------|------|
| 任务调度器 | 线程池调度器，支持并发执行 |
| Ingestion 执行器 | 数据采集管道执行器 |
| Indexing 执行器 | 索引构建管道执行器 |
| Publishing 执行器 | 发布管道执行器 |
| Source Connectors | Sitemap、Forum API、文件系统连接器 |
| 处理步骤 | Parser、Chunker、Enricher、Embedder |
| Qdrant 存储 | 向量索引存储实现 |

**产出物**:
```
core/
├── scheduler/
│   └── thread_scheduler.py          # 线程池调度器
└── executors/
    ├── base_executor.py             # 基类
    ├── ingestion_executor.py        # 采集执行器
    ├── indexing_executor.py         # 索引执行器
    └── publishing_executor.py       # 发布执行器

implementations/
├── connectors/
│   ├── sitemap_connector.py         # Sitemap 连接器
│   ├── forum_api_connector.py       # 论坛 API 连接器
│   └── filesystem_connector.py      # 文件系统连接器
├── steps/
│   ├── parsers/
│   │   ├── html_parser.py           # HTML 解析器
│   │   └── markdown_parser.py       # Markdown 解析器
│   ├── chunkers/
│   │   └── sentence_chunker.py      # 句子分片器
│   ├── enrichers/
│   │   ├── qa_enricher.py           # QA 生成
│   │   └── summary_enricher.py      # 摘要生成
│   └── embedders/
│       └── dashscope_embedder.py    # DashScope 嵌入
└── storage/
    └── qdrant_index_storage.py      # Qdrant 存储
```

---

### Phase 3: 管理 API

**目标**: 通过 API 管理知识库和任务

**状态**: ⏳ 待开始

**API 端点设计**:

```
/api/

# 知识库管理
GET    /knowledge-bases                    # 列出知识库
POST   /knowledge-bases                    # 创建知识库
GET    /knowledge-bases/{id}               # 获取详情
PUT    /knowledge-bases/{id}               # 更新知识库
DELETE /knowledge-bases/{id}               # 删除知识库

# 版本管理
GET    /knowledge-bases/{id}/versions      # 列出版本
POST   /knowledge-bases/{id}/versions      # 创建版本
GET    /versions/{id}                      # 版本详情
PUT    /versions/{id}                      # 更新版本
DELETE /versions/{id}                      # 删除版本

# 构建与发布
POST   /versions/{id}/build                # 触发构建
POST   /versions/{id}/publish              # 触发发布
GET    /versions/{id}/files                # 文件列表

# 任务管理
GET    /tasks                              # 任务列表
GET    /tasks/{id}                         # 任务详情
GET    /tasks/{id}/logs                    # 任务日志
POST   /tasks/{id}/cancel                  # 取消任务
POST   /tasks/{id}/retry                   # 重试任务

# 数据源
GET    /connectors                         # 可用连接器类型
POST   /connectors/test                    # 测试连接

# 环境管理
GET    /environments                       # 目标环境列表
POST   /environments                       # 添加环境
DELETE /environments/{id}                  # 删除环境

# 系统
GET    /health                             # 健康检查
GET    /metrics                            # 指标数据
GET    /config                             # 系统配置
```

**产出物**:
```
api/
├── __init__.py
├── main.py                              # FastAPI 应用入口
├── dependencies.py                      # 依赖注入配置
├── routers/
│   ├── knowledge_bases.py               # 知识库路由
│   ├── versions.py                      # 版本路由
│   ├── tasks.py                         # 任务路由
│   ├── connectors.py                    # 连接器路由
│   ├── environments.py                  # 环境路由
│   └── system.py                        # 系统路由
├── schemas/
│   ├── knowledge_base.py                # 请求/响应模型
│   ├── version.py
│   ├── task.py
│   └── common.py
└── middleware/
    ├── error_handler.py                 # 错误处理
    └── logging.py                       # 请求日志
```

---

### Phase 4: 管理控制台 (Admin UI)

**目标**: 可视化管理知识库构建流程

**状态**: ⏳ 待开始

**功能模块**:

```
管理控制台
├── 仪表盘 (Dashboard)
│   ├── 知识库总览卡片
│   ├── 任务状态统计
│   ├── 最近活动时间线
│   └── 系统健康状态
│
├── 知识库管理 (Knowledge Bases)
│   ├── 知识库列表
│   │   ├── 搜索/筛选
│   │   ├── 状态标签
│   │   └── 快捷操作
│   ├── 创建知识库向导
│   │   ├── 基本信息
│   │   ├── 数据源配置
│   │   ├── 处理管道配置
│   │   └── 发布目标配置
│   ├── 知识库详情
│   │   ├── 概览信息
│   │   ├── 版本历史
│   │   ├── 文件浏览器
│   │   └── 配置编辑
│   └── 版本管理
│       ├── 版本对比
│       ├── 构建触发
│       └── 发布管理
│
├── 任务中心 (Tasks)
│   ├── 任务列表
│   │   ├── 状态筛选
│   │   ├── 类型筛选
│   │   └── 时间范围
│   ├── 任务详情
│   │   ├── 执行进度
│   │   ├── 步骤统计
│   │   ├── 错误列表
│   │   └── 实时日志
│   └── 任务调度
│       ├── 定时任务配置
│       └── 手动触发
│
├── 数据源管理 (Sources)
│   ├── 连接器类型列表
│   ├── 连接测试工具
│   └── 采集历史记录
│
├── 发布管理 (Publishing)
│   ├── 目标环境配置
│   ├── 发布历史
│   ├── 别名管理
│   └── 回滚操作
│
└── 系统设置 (Settings)
    ├── 处理步骤配置
    │   ├── 分片参数
    │   ├── QA 生成参数
    │   └── 嵌入参数
    ├── LLM 配置
    │   ├── API 密钥
    │   ├── 模型选择
    │   └── 速率限制
    ├── 存储配置
    │   ├── 文件存储路径
    │   └── 数据库连接
    └── 系统信息
        ├── 版本信息
        └── 许可证
```

**技术选型**:
- 框架: React 18
- UI 库: Ant Design 5.x
- 状态管理: React Query
- 路由: React Router
- 构建: Vite
- 语言: TypeScript

**产出物**:
```
admin-ui/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── api/                             # API 客户端
│   │   ├── client.ts
│   │   ├── knowledge-bases.ts
│   │   ├── tasks.ts
│   │   └── ...
│   ├── components/                      # 通用组件
│   │   ├── Layout/
│   │   ├── DataTable/
│   │   ├── StatusBadge/
│   │   └── ...
│   ├── pages/                           # 页面组件
│   │   ├── Dashboard/
│   │   ├── KnowledgeBases/
│   │   ├── Tasks/
│   │   ├── Settings/
│   │   └── ...
│   ├── hooks/                           # 自定义 Hooks
│   ├── stores/                          # 状态管理
│   └── utils/                           # 工具函数
├── package.json
└── vite.config.ts
```

---

### Phase 5: 生产化

**目标**: 生产环境就绪

**状态**: ⏳ 待开始

| 任务 | 说明 | 优先级 |
|------|------|--------|
| Redis 队列 | 替换内存队列，支持分布式 | 高 |
| Prometheus Metrics | 生产级监控指标 | 高 |
| OpenTelemetry | 分布式追踪集成 | 中 |
| 结构化日志 | JSON 格式日志输出 | 高 |
| 配置管理 | 多环境配置支持 | 高 |
| Docker 镜像 | 容器化部署 | 高 |
| Docker Compose | 本地/测试环境编排 | 高 |
| Kubernetes | 生产集群部署 | 中 |
| Helm Charts | K8s 包管理 | 中 |
| CI/CD | GitHub Actions 流水线 | 高 |
| 健康检查 | 就绪/存活探针 | 高 |
| 优雅关闭 | 信号处理、连接排空 | 高 |
| 限流 | API 速率限制 | 中 |
| 认证 | API Key / JWT | 高 |
| 授权 | RBAC 权限控制 | 中 |
| 审计日志 | 操作记录 | 中 |
| 备份恢复 | 数据备份策略 | 中 |

**产出物**:
```
deploy/
├── docker/
│   ├── Dockerfile.etl
│   └── Dockerfile.admin
├── docker-compose/
│   ├── docker-compose.dev.yml
│   ├── docker-compose.staging.yml
│   └── docker-compose.prod.yml
├── kubernetes/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment-etl.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── helm/
│   └── ai-knowledge-etl/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
└── .github/
    └── workflows/
        ├── ci.yml
        ├── build.yml
        └── deploy.yml

implementations/
├── infrastructure/
│   └── redis_queue.py                   # Redis 任务队列
└── observability/
    ├── prometheus_metrics.py            # Prometheus 指标
    ├── opentelemetry_tracer.py          # OTel 追踪
    └── structured_logger.py             # 结构化日志
```

---

### Phase 6: 高级特性

**目标**: 增强功能和扩展能力

**状态**: ⏳ 长期规划

| 特性 | 说明 | 复杂度 |
|------|------|--------|
| 多租户 | 租户隔离、配额管理 | 高 |
| Webhook | 事件通知集成 (构建完成、发布等) | 低 |
| 插件系统 | 自定义处理步骤、连接器 | 高 |
| Python SDK | 编程式 ETL 接口 | 中 |
| CLI 工具 | 命令行管理工具 | 中 |
| 定时调度 | Cron 式任务调度 | 中 |
| 增量同步 | 实时/准实时数据同步 | 高 |
| 数据血缘 | 文件处理追踪 | 中 |
| 质量检测 | 索引质量评估 | 中 |

---

## 三、时间线总览

```
Phase 1: 基础框架        ████████████████████████  ✅ 完成
Phase 2: 核心管道        ████░░░░░░░░░░░░░░░░░░░░  当前阶段
Phase 3: 管理 API        ░░░░████░░░░░░░░░░░░░░░░
Phase 4: 管理控制台       ░░░░░░░░████░░░░░░░░░░░░
Phase 5: 生产化          ░░░░░░░░░░░░████████████  (持续进行)
Phase 6: 高级特性        ░░░░░░░░░░░░░░░░░░░░░░░░  (长期规划)
```

---

## 四、与现有系统的关系

### 代码迁移映射

```
现有系统                              新架构
────────────────────────────────────────────────────────────────

gc-qa-rag-etl/                    →   ETL 服务
├── etlapp/das/
│   ├── das_doc.py                →   SitemapConnector
│   ├── das_forum.py              →   ForumApiConnector
│   └── das_generic.py            →   FilesystemConnector
├── etlapp/etl/
│   ├── etl_doc/generate.py       →   QAEnricher
│   ├── etl_doc/generate_sub.py   →   SynonymEnricher
│   └── etl_doc/generate_full.py  →   FullAnswerEnricher
├── etlapp/common/
│   ├── chunk.py                  →   SentenceChunker
│   ├── embedding.py              →   DashScopeEmbedder
│   └── vector.py                 →   QdrantIndexStorage
└── etlapp/ved/                   →   PublishingExecutor
```

### 迁移策略

1. **并行运行**: 新旧系统并行运行，逐步切换流量
2. **适配器模式**: 通过适配器将现有代码接入新抽象层
3. **渐进式迁移**: 按模块逐步迁移，降低风险
4. **数据兼容**: 保持索引格式兼容，支持无缝切换

---

## 五、文档版本

| 版本 | 日期 | 说明 |
|-----|------|------|
| 1.0 | 2026-01-17 | 初稿 |
| 1.1 | 2026-01-17 | 聚焦 ETL 层，移除 RAG 查询服务相关内容 |
| 1.2 | 2026-01-17 | Phase 1 完成，新增测试套件 (154 tests) |
