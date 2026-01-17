"""
Embedders package - Embedding generation steps.
"""

from ai_knowledge_service.implementations.steps.embedders.dashscope_embedder import (
    DashScopeEmbedder,
    DashScopeConfig,
)

__all__ = ["DashScopeEmbedder", "DashScopeConfig"]
