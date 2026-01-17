"""
Configuration Schemas - Data classes for configuration.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_knowledge_service.abstractions.models.tasks import PublishStrategy
from ai_knowledge_service.abstractions.observability.logging import LogLevel


@dataclass
class ValidatorConfig:
    """Configuration for a validator."""

    type: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self.config.get(key, default)


@dataclass
class SourceConfigSchema:
    """Configuration for a data source."""

    connector_type: str
    connection: Dict[str, Any] = field(default_factory=dict)
    fetch_options: Dict[str, Any] = field(default_factory=dict)

    def get_connection(self, key: str, default: Any = None) -> Any:
        """Get a connection parameter."""
        return self.connection.get(key, default)

    def get_fetch_option(self, key: str, default: Any = None) -> Any:
        """Get a fetch option."""
        return self.fetch_options.get(key, default)


@dataclass
class IngestionConfig:
    """Configuration for ingestion."""

    source: SourceConfigSchema
    validators: List[ValidatorConfig] = field(default_factory=list)
    dedup_strategy: str = "version"  # "skip", "replace", "version"
    batch_size: int = 100

    def get_enabled_validators(self) -> List[ValidatorConfig]:
        """Get only enabled validators."""
        return [v for v in self.validators if v.enabled]


@dataclass
class StepConfigSchema:
    """Configuration for a processing step."""

    step_type: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self.config.get(key, default)


@dataclass
class IndexingConfig:
    """Configuration for indexing."""

    pipeline: List[StepConfigSchema] = field(default_factory=list)

    def get_enabled_steps(self) -> List[StepConfigSchema]:
        """Get only enabled steps."""
        return [s for s in self.pipeline if s.enabled]

    def get_step(self, step_type: str) -> Optional[StepConfigSchema]:
        """Get a step by type."""
        for step in self.pipeline:
            if step.step_type == step_type:
                return step
        return None


@dataclass
class TargetConfig:
    """Configuration for a publishing target."""

    environment_id: str
    alias_pattern: str = "{kb_id}_prod"
    strategy: PublishStrategy = PublishStrategy.BLUE_GREEN
    include_raw_files: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishingConfig:
    """Configuration for publishing."""

    targets: List[TargetConfig] = field(default_factory=list)

    def get_target(self, environment_id: str) -> Optional[TargetConfig]:
        """Get a target by environment ID."""
        for target in self.targets:
            if target.environment_id == environment_id:
                return target
        return None


@dataclass
class MetricsConfig:
    """Configuration for metrics."""

    enabled: bool = True
    type: str = "prometheus"  # "prometheus", "statsd", etc.
    endpoint: str = "/metrics"
    prefix: str = "ai_knowledge_service"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TracingConfig:
    """Configuration for tracing."""

    enabled: bool = True
    type: str = "opentelemetry"  # "opentelemetry", "jaeger", etc.
    endpoint: str = ""
    sample_rate: float = 1.0  # 1.0 = 100%
    service_name: str = "ai-knowledge-service"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: LogLevel = LogLevel.INFO
    format: str = "json"  # "json", "text"
    output: str = "stdout"  # "stdout", "file", etc.
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObservabilityConfig:
    """Configuration for observability."""

    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


@dataclass
class KnowledgeBaseConfig:
    """
    Complete configuration for a knowledge base.

    This is the top-level configuration that can be loaded from YAML.
    """

    id: str
    name: str
    description: str = ""

    ingestion: Optional[IngestionConfig] = None
    indexing: Optional[IndexingConfig] = None
    publishing: Optional[PublishingConfig] = None
    observability: Optional[ObservabilityConfig] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Knowledge base ID cannot be empty")
        if not self.name:
            raise ValueError("Knowledge base name cannot be empty")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeBaseConfig":
        """
        Create a config from a dictionary.

        Args:
            data: Configuration dictionary (e.g., loaded from YAML).

        Returns:
            KnowledgeBaseConfig: The configuration object.
        """
        kb_data = data.get("knowledge_base", data)

        # Parse ingestion config
        ingestion = None
        if "ingestion" in data:
            ing_data = data["ingestion"]
            source = SourceConfigSchema(
                connector_type=ing_data.get("source", {}).get("connector_type", ""),
                connection=ing_data.get("source", {}).get("connection", {}),
                fetch_options=ing_data.get("source", {}).get("fetch_options", {}),
            )
            validators = [
                ValidatorConfig(**v) for v in ing_data.get("validators", [])
            ]
            ingestion = IngestionConfig(
                source=source,
                validators=validators,
                dedup_strategy=ing_data.get("dedup_strategy", "version"),
                batch_size=ing_data.get("batch_size", 100),
            )

        # Parse indexing config
        indexing = None
        if "indexing" in data:
            idx_data = data["indexing"]
            steps = [
                StepConfigSchema(**s) for s in idx_data.get("pipeline", [])
            ]
            indexing = IndexingConfig(pipeline=steps)

        # Parse publishing config
        publishing = None
        if "publishing" in data:
            pub_data = data["publishing"]
            targets = []
            for t in pub_data.get("targets", []):
                strategy = t.get("strategy", "blue_green")
                if isinstance(strategy, str):
                    strategy = PublishStrategy(strategy)
                targets.append(TargetConfig(
                    environment_id=t.get("environment_id", ""),
                    alias_pattern=t.get("alias_pattern", "{kb_id}_prod"),
                    strategy=strategy,
                    include_raw_files=t.get("include_raw_files", False),
                ))
            publishing = PublishingConfig(targets=targets)

        # Parse observability config
        observability = None
        if "observability" in data:
            obs_data = data["observability"]
            metrics = MetricsConfig(**obs_data.get("metrics", {})) if "metrics" in obs_data else MetricsConfig()
            tracing = TracingConfig(**obs_data.get("tracing", {})) if "tracing" in obs_data else TracingConfig()

            log_data = obs_data.get("logging", {})
            if "level" in log_data and isinstance(log_data["level"], str):
                log_data["level"] = LogLevel(log_data["level"])
            logging_config = LoggingConfig(**log_data) if log_data else LoggingConfig()

            observability = ObservabilityConfig(
                metrics=metrics,
                tracing=tracing,
                logging=logging_config,
            )

        return cls(
            id=kb_data.get("id", ""),
            name=kb_data.get("name", ""),
            description=kb_data.get("description", ""),
            ingestion=ingestion,
            indexing=indexing,
            publishing=publishing,
            observability=observability,
            metadata=kb_data.get("metadata", {}),
        )
