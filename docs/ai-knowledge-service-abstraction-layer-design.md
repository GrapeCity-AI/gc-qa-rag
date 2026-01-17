# AI 知识服务 - 抽象层设计文档

> 本文档定义 AI 知识服务的抽象层架构，提供与具体实现完全解耦的接口定义。

---

## 一、设计目标

### 1.1 核心原则

- **抽象与实现分离**：抽象层仅定义接口，不包含任何具体实现
- **依赖注入**：通过 DI 容器管理组件依赖
- **任务驱动**：所有管道都是 Job 模式，由任务队列驱动
- **可观测性**：内置 Metrics/Tracing/Logging 支持
- **最终一致性**：跨存储操作采用最终一致性模型
- **容错设计**：错误跳过继续，不中断整体流程

### 1.2 不在范围内

- 多租户支持
- 分布式事务

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Abstraction Layer                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐ │
│  │  Source  │───▶│Ingestion │───▶│Raw Files │───▶│ Indexing │───▶│Indexes │ │
│  │Connector │    │ Executor │    │ Storage  │    │ Executor │    │Storage │ │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────┬───┘ │
│                                                                       │     │
│                                       ┌───────────────────────────────┘     │
│                                       ▼                                     │
│                                 ┌──────────┐    ┌──────────┐                │
│                                 │Publishing│───▶│  Target  │                │
│                                 │ Executor │    │   Env    │                │
│                                 └──────────┘    └──────────┘                │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │   Task   │    │ Version  │    │    DI    │    │  Event   │               │
│  │  Queue   │    │ Manager  │    │Container │    │   Bus    │               │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Observability                                 │   │
│  │    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │   │
│  │    │ Metrics │    │ Tracing │    │ Logging │    │ Health  │          │   │
│  │    └─────────┘    └─────────┘    └─────────┘    └─────────┘          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、核心领域模型

### 3.1 知识库与版本

```python
@dataclass
class KnowledgeBase:
    """知识库 - 顶层组织单元"""
    id: str
    name: str
    description: str
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class KnowledgeBaseVersion:
    """知识库版本 - 某个时间点的快照"""
    id: str
    knowledge_base_id: str
    version_tag: str              # e.g., "v1.0", "20260117"
    status: VersionStatus         # DRAFT, BUILDING, READY, PUBLISHED, ARCHIVED
    parent_version_id: str | None # 用于增量构建的基线版本
    created_at: datetime
    published_at: datetime | None

class VersionStatus(Enum):
    DRAFT = "draft"           # 草稿，可编辑
    BUILDING = "building"     # 构建中
    READY = "ready"           # 构建完成，待发布
    PUBLISHED = "published"   # 已发布到生产
    ARCHIVED = "archived"     # 已归档

@dataclass
class FileVersion:
    """文件版本 - 单个文件的版本"""
    id: str
    raw_file_id: str
    knowledge_base_version_id: str
    content_hash: str             # 内容指纹，用于判断是否变更
    index_status: IndexStatus     # PENDING, INDEXED, FAILED
    indexed_at: datetime | None
```

### 3.2 原始文件

```python
@dataclass
class RawFile:
    """原始文件记录"""
    id: str
    knowledge_base_id: str
    source_type: str              # "sitemap", "forum_api", "file_upload"
    source_uri: str               # 原始来源标识
    original_name: str
    content_hash: str
    storage_path: str             # 物理存储路径
    mime_type: str
    size_bytes: int
    metadata: Dict[str, Any]      # 来源特定的元数据
    lifecycle_status: LifecycleStatus
    created_at: datetime

class LifecycleStatus(Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"           # 逻辑删除，物理保留
```

### 3.3 索引记录

```python
@dataclass
class IndexRecord:
    """索引记录 - 写入索引存储的单元"""
    id: str
    file_version_id: str          # 溯源到文件版本
    index_type: str               # "vector", "structured", "fulltext"
    content: Dict[str, Any]       # 索引内容（向量、文本等）
    payload: Dict[str, Any]       # 附加数据（问题、答案、元数据）
    created_at: datetime
```

---

## 四、任务模型

### 4.1 任务基类

```python
class TaskType(Enum):
    INGESTION = "ingestion"
    INDEXING = "indexing"
    PUBLISHING = "publishing"

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskBase(ABC):
    """任务基类"""
    id: str
    task_type: TaskType
    knowledge_base_id: str
    knowledge_base_version_id: str
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: Dict[str, Any]

@dataclass
class TaskResultBase(ABC):
    """任务结果基类"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    total_items: int
    succeeded_count: int
    failed_count: int
    skipped_count: int
    errors: List[ProcessingError]
    started_at: datetime
    completed_at: datetime
    duration_seconds: float

@dataclass
class ProcessingError:
    """处理错误记录"""
    item_id: str
    item_name: str
    step: str
    error_type: str
    error_message: str
    stacktrace: str | None = None
    timestamp: datetime
    recoverable: bool = True
```

### 4.2 采集任务

```python
@dataclass
class IngestionTask(TaskBase):
    """采集任务"""
    source_config: SourceConfig
    incremental: bool = False
    since: datetime | None = None
    validators: List[str]
    dedup_strategy: str = "version"

@dataclass
class IngestionTaskResult(TaskResultBase):
    """采集任务结果"""
    ingested_file_ids: List[str]
    new_files_count: int = 0
    updated_files_count: int = 0
    unchanged_files_count: int = 0
```

### 4.3 索引任务

```python
class BuildType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"

@dataclass
class IndexingTask(TaskBase):
    """索引构建任务"""
    build_type: BuildType
    file_version_ids: List[str]   # 空=全量
    pipeline_config: List[StepConfig]

@dataclass
class IndexingTaskResult(TaskResultBase):
    """索引构建任务结果"""
    index_records_count: int = 0
    collections_affected: List[str]
    step_stats: Dict[str, StepStats]

@dataclass
class StepStats:
    """步骤执行统计"""
    step_type: str
    input_count: int
    output_count: int
    duration_seconds: float
    errors_count: int
```

### 4.4 发布任务

```python
class PublishStrategy(Enum):
    REPLACE = "replace"
    BLUE_GREEN = "blue_green"

@dataclass
class PublishingTask(TaskBase):
    """发布任务"""
    target_environment_id: str
    include_raw_files: bool = False
    alias_name: str | None = None
    publish_strategy: PublishStrategy = PublishStrategy.BLUE_GREEN

@dataclass
class PublishingTaskResult(TaskResultBase):
    """发布任务结果"""
    target_collection: str = ""
    alias_applied: str | None = None
    previous_collection: str | None = None
    index_records_published: int = 0
    raw_files_published: int = 0
```

---

## 五、管道接口

### 5.1 数据源连接器

```python
class ISourceConnector(Protocol):
    """数据源连接器接口"""

    @property
    def source_type(self) -> str:
        """返回数据源类型标识"""
        ...

    def configure(self, config: SourceConfig) -> None:
        """配置连接器"""
        ...

    def validate_connection(self) -> ConnectionResult:
        """验证连接可用性"""
        ...

    def fetch(self) -> Iterator[SourceRecord]:
        """拉取数据"""
        ...

    def fetch_incremental(self, since: datetime) -> Iterator[SourceRecord]:
        """增量拉取"""
        ...

@dataclass
class SourceConfig:
    connector_type: str
    connection_params: Dict[str, Any]
    fetch_options: Dict[str, Any]

@dataclass
class SourceRecord:
    source_uri: str
    content: bytes | str
    content_type: str
    metadata: Dict[str, Any]
    fetched_at: datetime
```

### 5.2 任务执行器

```python
class ITaskExecutor(Protocol, Generic[TTask, TResult]):
    """任务执行器通用接口"""

    @property
    def task_type(self) -> TaskType:
        ...

    def validate(self, task: TTask) -> List[str]:
        """校验任务参数，返回错误列表"""
        ...

    def execute(self, task: TTask) -> TResult:
        """执行任务"""
        ...

    def cancel(self, task_id: str) -> bool:
        """取消任务"""
        ...

class IIngestionExecutor(ITaskExecutor[IngestionTask, IngestionTaskResult], Protocol):
    pass

class IIndexingExecutor(ITaskExecutor[IndexingTask, IndexingTaskResult], Protocol):
    pass

class IPublishingExecutor(ITaskExecutor[PublishingTask, PublishingTaskResult], Protocol):
    pass
```

### 5.3 处理步骤

```python
class IProcessingStep(Protocol):
    """处理步骤接口"""

    @property
    def step_type(self) -> str:
        ...

    def configure(self, config: Dict[str, Any]) -> None:
        ...

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext
    ) -> ProcessingContext:
        ...

class IContentParser(IProcessingStep):
    """内容解析器"""
    pass

class IChunker(IProcessingStep):
    """分片器"""
    pass

class IEnricher(IProcessingStep):
    """增强器（支持多个串联）"""

    @property
    def enrichment_type(self) -> str:
        ...

class IEmbedder(IProcessingStep):
    """嵌入器"""
    pass

class IIndexBuilder(IProcessingStep):
    """索引构建器"""
    pass

@dataclass
class ProcessingContext:
    """处理上下文"""
    raw_file: RawFile
    file_version: FileVersion
    parsed_document: ParsedDocument | None = None
    chunks: List[Chunk] | None = None
    enrichments: Dict[str, Any] = field(default_factory=dict)
    embeddings: List[Embedding] | None = None
    index_records: List[IndexRecord] | None = None
    errors: List[ProcessingError] = field(default_factory=list)
    should_skip: bool = False
    skip_reason: str | None = None
```

### 5.4 发布相关

```python
class ITargetEnvironment(Protocol):
    """目标环境接口"""

    @property
    def environment_id(self) -> str:
        ...

    def validate_connection(self) -> ConnectionResult:
        ...

    def get_capabilities(self) -> EnvironmentCapabilities:
        ...

class IIndexExporter(Protocol):
    """索引导出器"""

    def export(
        self,
        collection: str,
        output_path: str,
        options: ExportOptions
    ) -> ExportResult:
        ...

class IIndexImporter(Protocol):
    """索引导入器"""

    def import_index(
        self,
        source_path: str,
        target_collection: str,
        options: ImportOptions
    ) -> ImportResult:
        ...
```

---

## 六、存储接口

### 6.1 原始文件存储

```python
class IRawFileStorage(Protocol):
    """原始文件存储接口（组合接口）"""

    def save(self, record: SourceRecord, knowledge_base_id: str) -> RawFile:
        ...

    def get(self, file_id: str) -> RawFile:
        ...

    def get_content(self, file_id: str) -> bytes:
        ...

    def list(
        self,
        knowledge_base_id: str,
        status: LifecycleStatus | None = None,
        since: datetime | None = None
    ) -> Iterator[RawFile]:
        ...

    def update_status(self, file_id: str, status: LifecycleStatus) -> None:
        ...

    def exists_by_hash(self, knowledge_base_id: str, content_hash: str) -> str | None:
        ...

class IRawFileMetadataStore(Protocol):
    """原始文件元数据存储（数据库）"""

    def save(self, raw_file: RawFile) -> None
    def get(self, file_id: str) -> RawFile | None
    def query(self, criteria: QueryCriteria) -> List[RawFile]
    def update(self, raw_file: RawFile) -> None

class IRawFileContentStore(Protocol):
    """原始文件内容存储（文件系统）"""

    def write(self, file_id: str, content: bytes) -> str
    def read(self, storage_path: str) -> bytes
    def delete(self, storage_path: str) -> None
    def exists(self, storage_path: str) -> bool
```

### 6.2 索引存储

```python
class IIndexStorage(Protocol):
    """索引存储接口"""

    def create_collection(
        self,
        name: str,
        schema: IndexSchema,
        knowledge_base_version_id: str
    ) -> None:
        ...

    def write(
        self,
        collection: str,
        records: List[IndexRecord]
    ) -> WriteResult:
        ...

    def delete_by_file_version(
        self,
        collection: str,
        file_version_id: str
    ) -> int:
        ...

    def get_collection_info(self, collection: str) -> CollectionInfo:
        ...

    def delete_collection(self, collection: str) -> None:
        ...

    def update_alias(self, alias: str, collection: str) -> None:
        ...

@dataclass
class IndexSchema:
    index_type: str
    fields: List[FieldDefinition]
    vector_config: VectorConfig | None

@dataclass
class VectorConfig:
    dimensions: int
    distance_metric: str
    sparse_enabled: bool
```

---

## 七、基础设施接口

### 7.1 任务队列

```python
class ITaskQueue(Protocol):
    """任务队列接口"""

    def enqueue(
        self,
        task: TaskBase,
        delay: timedelta | None = None
    ) -> str:
        ...

    def dequeue(self, task_type: TaskType) -> TaskBase | None:
        ...

    def complete(self, task_id: str, result: TaskResultBase) -> None:
        ...

    def fail(
        self,
        task_id: str,
        error: str,
        result: TaskResultBase | None = None
    ) -> None:
        ...

    def get_task(self, task_id: str) -> TaskBase | None:
        ...

    def get_result(self, task_id: str) -> TaskResultBase | None:
        ...

    def list_tasks(
        self,
        task_type: TaskType | None = None,
        status: TaskStatus | None = None,
        knowledge_base_id: str | None = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TaskBase]:
        ...

    def cancel(self, task_id: str) -> bool:
        ...
```

### 7.2 任务调度器

```python
class ITaskScheduler(Protocol):
    """任务调度器接口"""

    def register_executor(
        self,
        task_type: TaskType,
        executor: ITaskExecutor
    ) -> None:
        ...

    def start(self, worker_count: int = 1) -> None:
        ...

    def stop(self, graceful: bool = True) -> None:
        ...

    def get_status(self) -> SchedulerStatus:
        ...

@dataclass
class SchedulerStatus:
    is_running: bool
    worker_count: int
    active_tasks: int
    pending_tasks: Dict[TaskType, int]
```

### 7.3 版本管理器

```python
class IVersionManager(Protocol):
    """版本管理器接口"""

    # 知识库版本
    def create_version(
        self,
        knowledge_base_id: str,
        version_tag: str,
        parent_version_id: str | None = None
    ) -> KnowledgeBaseVersion:
        ...

    def get_version(self, version_id: str) -> KnowledgeBaseVersion:
        ...

    def get_latest_version(
        self,
        knowledge_base_id: str,
        status: VersionStatus | None = None
    ) -> KnowledgeBaseVersion | None:
        ...

    def update_version_status(
        self,
        version_id: str,
        status: VersionStatus
    ) -> None:
        ...

    # 文件版本
    def create_file_version(
        self,
        raw_file_id: str,
        knowledge_base_version_id: str,
        content_hash: str
    ) -> FileVersion:
        ...

    def get_file_versions(
        self,
        knowledge_base_version_id: str,
        index_status: IndexStatus | None = None
    ) -> List[FileVersion]:
        ...

    def get_changed_files(
        self,
        knowledge_base_version_id: str,
        base_version_id: str
    ) -> List[FileVersion]:
        ...

    def update_file_index_status(
        self,
        file_version_id: str,
        status: IndexStatus
    ) -> None:
        ...
```

### 7.4 事件总线

```python
class IEventBus(Protocol):
    """事件总线接口"""

    def publish(self, event: DomainEvent) -> None:
        ...

    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None]
    ) -> None:
        ...

@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]

# 具体事件
class FileIngestedEvent(DomainEvent): ...
class BuildTaskCompletedEvent(DomainEvent): ...
class VersionPublishedEvent(DomainEvent): ...
```

### 7.5 依赖注入容器

```python
class Lifetime(Enum):
    TRANSIENT = "transient"
    SCOPED = "scoped"
    SINGLETON = "singleton"

class IServiceContainer(Protocol):
    """依赖注入容器接口"""

    def register(
        self,
        interface: Type[T],
        implementation: Type[T] | Callable[..., T],
        lifetime: Lifetime = Lifetime.TRANSIENT
    ) -> None:
        ...

    def register_instance(
        self,
        interface: Type[T],
        instance: T
    ) -> None:
        ...

    def resolve(self, interface: Type[T]) -> T:
        ...

    def create_scope(self) -> IServiceScope:
        ...

class IServiceScope(Protocol):
    def resolve(self, interface: Type[T]) -> T
    def __enter__(self) -> IServiceScope
    def __exit__(self, *args) -> None
```

---

## 八、可观测性接口

### 8.1 Metrics

```python
class IMetricsCollector(Protocol):
    """指标收集器接口"""

    def counter(
        self,
        name: str,
        value: int = 1,
        tags: Dict[str, str] | None = None
    ) -> None:
        ...

    def gauge(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] | None = None
    ) -> None:
        ...

    def histogram(
        self,
        name: str,
        value: float,
        tags: Dict[str, str] | None = None
    ) -> None:
        ...

    def timer(
        self,
        name: str,
        tags: Dict[str, str] | None = None
    ) -> ITimer:
        ...

class ITimer(Protocol):
    def __enter__(self) -> ITimer
    def __exit__(self, *args) -> None

    @property
    def elapsed_seconds(self) -> float: ...

class MetricNames:
    # 任务
    TASK_ENQUEUED = "task.enqueued"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_DURATION = "task.duration_seconds"

    # 采集
    INGESTION_FILES_TOTAL = "ingestion.files.total"
    INGESTION_FILES_NEW = "ingestion.files.new"
    INGESTION_BYTES_TOTAL = "ingestion.bytes.total"

    # 索引
    INDEXING_RECORDS_TOTAL = "indexing.records.total"
    INDEXING_STEP_DURATION = "indexing.step.duration_seconds"
    INDEXING_STEP_ERRORS = "indexing.step.errors"

    # 发布
    PUBLISHING_RECORDS_TOTAL = "publishing.records.total"
    PUBLISHING_DURATION = "publishing.duration_seconds"
```

### 8.2 Tracing

```python
class ITracer(Protocol):
    """分布式追踪接口"""

    def start_span(
        self,
        name: str,
        parent: ISpan | None = None,
        tags: Dict[str, str] | None = None
    ) -> ISpan:
        ...

    def get_current_span(self) -> ISpan | None:
        ...

    def inject_context(self, carrier: Dict[str, str]) -> None:
        ...

    def extract_context(self, carrier: Dict[str, str]) -> ISpan | None:
        ...

class ISpan(Protocol):
    @property
    def trace_id(self) -> str: ...

    @property
    def span_id(self) -> str: ...

    def set_tag(self, key: str, value: str) -> None: ...
    def log(self, message: str, **kwargs) -> None: ...
    def set_error(self, error: Exception) -> None: ...
    def finish(self) -> None: ...

    def __enter__(self) -> ISpan: ...
    def __exit__(self, *args) -> None: ...

class SpanNames:
    TASK_EXECUTE = "task.execute"
    INGESTION_FETCH = "ingestion.fetch"
    INGESTION_VALIDATE = "ingestion.validate"
    INDEXING_PARSE = "indexing.parse"
    INDEXING_CHUNK = "indexing.chunk"
    INDEXING_ENRICH = "indexing.enrich"
    INDEXING_EMBED = "indexing.embed"
    PUBLISHING_EXPORT = "publishing.export"
    PUBLISHING_IMPORT = "publishing.import"
```

### 8.3 Logging

```python
class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class ILogger(Protocol):
    """结构化日志接口"""

    def log(
        self,
        level: LogLevel,
        message: str,
        **context
    ) -> None:
        ...

    def debug(self, message: str, **context) -> None: ...
    def info(self, message: str, **context) -> None: ...
    def warning(self, message: str, **context) -> None: ...
    def error(self, message: str, error: Exception | None = None, **context) -> None: ...

    def with_context(self, **context) -> ILogger:
        ...

class ILoggerFactory(Protocol):
    def get_logger(self, name: str) -> ILogger:
        ...
```

### 8.4 Health Check

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    message: str | None = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime

class IHealthCheck(Protocol):
    @property
    def component_name(self) -> str: ...

    def check(self) -> HealthCheckResult: ...

class IHealthChecker(Protocol):
    def register(self, check: IHealthCheck) -> None: ...
    def check_all(self) -> List[HealthCheckResult]: ...
    def get_overall_status(self) -> HealthStatus: ...
```

### 8.5 可观测性上下文

```python
@dataclass
class ObservabilityContext:
    """可观测性上下文"""
    trace_id: str
    span_id: str
    task_id: str
    task_type: TaskType
    knowledge_base_id: str
    knowledge_base_version_id: str
    extra: Dict[str, str] = field(default_factory=dict)

    def to_tags(self) -> Dict[str, str]:
        return {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "kb_id": self.knowledge_base_id,
            "kb_version_id": self.knowledge_base_version_id,
            **self.extra
        }
```

---

## 九、模块组织结构

```
ai_knowledge_service/
├── abstractions/                    # 抽象层（纯接口定义）
│   ├── __init__.py
│   │
│   ├── models/                      # 领域模型
│   │   ├── __init__.py
│   │   ├── knowledge_base.py
│   │   ├── raw_file.py
│   │   ├── index.py
│   │   └── tasks.py
│   │
│   ├── execution/                   # 任务执行
│   │   ├── __init__.py
│   │   ├── executor.py
│   │   ├── queue.py
│   │   └── scheduler.py
│   │
│   ├── pipelines/                   # 管道接口
│   │   ├── __init__.py
│   │   ├── source.py
│   │   ├── steps.py
│   │   └── publishing.py
│   │
│   ├── storage/                     # 存储接口
│   │   ├── __init__.py
│   │   ├── raw_file_storage.py
│   │   └── index_storage.py
│   │
│   ├── observability/               # 可观测性
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── tracing.py
│   │   ├── logging.py
│   │   ├── health.py
│   │   └── context.py
│   │
│   ├── infrastructure/              # 基础设施接口
│   │   ├── __init__.py
│   │   ├── version_manager.py
│   │   ├── event_bus.py
│   │   └── container.py
│   │
│   └── config/                      # 配置模型
│       ├── __init__.py
│       └── schemas.py
│
├── core/                            # 核心实现（管道编排）
│   └── ...
│
└── implementations/                 # 具体实现
    └── ...
```

---

## 十、配置示例

```yaml
knowledge_base:
  id: "kb-forguncy-docs"
  name: "Forguncy 文档知识库"

ingestion:
  source:
    connector_type: "sitemap"
    connection:
      url: "https://example.com/docs/sitemap.xml"
  validators:
    - type: "size_limit"
      max_bytes: 10485760
  dedup_strategy: "version"

indexing:
  pipeline:
    - step_type: "html_parser"
      config:
        selector: "article.main-content"

    - step_type: "sentence_chunker"
      config:
        group_size: 10
        min_group_size: 5

    - step_type: "qa_enricher"
      config:
        strategy: "memory_focus"

    - step_type: "summary_enricher"
      config:
        max_length: 200

    - step_type: "dashscope_embedder"
      config:
        model: "text-embedding-v4"
        dimensions: 1024

    - step_type: "vector_index_builder"

publishing:
  targets:
    - environment_id: "prod-cn"
      alias_pattern: "{kb_id}_prod"
      strategy: "blue_green"

observability:
  metrics:
    enabled: true
    type: "prometheus"
  tracing:
    enabled: true
    type: "opentelemetry"
  logging:
    level: "info"
    format: "json"
```

---

## 十一、文档版本

| 版本 | 日期 | 说明 |
|-----|------|------|
| 1.0 | 2026-01-17 | 初稿，完整抽象层设计 |
