# gc-qa-rag-etl

### 概述

用于构建知识库索引的 ETL 程序。

### 系统架构

系统包含三个主要组件：

-   **DAS（数据采集系统）**：处理数据收集和预处理
-   **ETL（提取、转换、加载）**：管理数据处理和转换
-   **VED（向量嵌入发布）**：实现向量嵌入的发布

### 安装

1. 使用 PDM 安装依赖：

```bash
pdm install
```

### 开发

#### 环境要求

-   Python 3.13
-   PDM
-   Docker（可选）

#### 开发工具（推荐）

-   IDE：Visual Studio Code
-   Python 扩展：Pylance、Ruff

### 许可证

本项目采用 MIT 许可证
