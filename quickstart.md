# GC-QA-RAG 项目快速开始

## 概述

GC-QA-RAG 项目采用模块化、分布式架构设计，将整体系统拆分为 ETL（知识库构建）、Server（后端服务）和 Frontend（主前端界面）三个独立子模块。ETL 和 Server 均为独立的 Web 应用，分别负责知识库数据处理与后端 API 服务，前后端完全分离，便于独立开发、测试和部署。各模块通过标准 API 进行通信，极大提升了系统的可扩展性和维护性。此外，项目对 Docker 支持良好，所有模块均可通过容器化方式一键部署，极大简化了生产环境的集成与运维流程，适合多种实际应用场景。

以下为各模块的快速编译与运行指南。

## 1. 环境准备

-   Python（Python 虚拟环境，版本均为 3.13）
-   Node.js（建议 16+，用于前端）
-   PDM（Python 包管理工具）
-   pnpm（前端包管理工具，推荐 8+）
-   Docker（可选，支持容器化部署）
-   MySQL、Qdrant（后端依赖服务）

## 2. 各模块编译与运行

### 2.1 ETL（知识库构建及配套前端）

ETL（Extract-Transform-Load）模块是 GC-QA-RAG 项目的核心组成部分，主要负责知识库的构建与管理。该模块实现了数据的抽取、转换和加载流程，支持多源数据的高效处理与入库。ETL 模块不仅包含 CLI 主程序，还配套了可视化前端（etlapp-web），方便用户对知识库构建流程进行管理和监控。主程序基于 Python 开发，配套前端基于 Node.js 与 pnpm 构建，二者协同工作，极大提升了知识库构建的自动化与易用性。

#### 2.1.1 ETL 主程序

**安装依赖**

```bash
cd sources/gc-qa-rag-etl
pdm install
```

**运行**

```bash
pdm run dev
```

服务默认运行在 `http://0.0.0.0:8001`

#### 2.1.2 etlapp-web（ETL 配套前端）

目录：`sources/gc-qa-rag-etl/etlapp-web`

**安装依赖**

```bash
cd sources/gc-qa-rag-etl/etlapp-web
pnpm install
```

**启动开发环境**

```bash
pnpm run dev
```

### 2.2 Server（后端服务）

Server 模块是 GC-QA-RAG 项目的后端核心，负责为前端和 ETL 模块提供 API 支持。该模块基于 Python 开发，依赖 MySQL 作为关系型数据库，Qdrant 作为向量数据库，并可集成多种 AI 服务。Server 支持灵活的开发与生产环境配置，具备良好的可扩展性和高性能，适合大规模知识库问答场景。通过 Docker 可实现一键部署，便于生产环境集成。

目录：`sources/gc-qa-rag-server`

**安装依赖**

```bash
cd sources/gc-qa-rag-server
pdm install
```

**配置环境**

-   修改 `.config.development.json` 或 `.config.production.json`，配置数据库、Qdrant、AI 服务等参数。

**启动服务**

开发模式：

```bash
pdm run dev
```

服务默认运行在 `http://0.0.0.0:8000`

### 2.3 Frontend（主前端界面）

Frontend 模块为 GC-QA-RAG 项目的主用户界面，基于现代前端技术栈（如 Vue/React、Node.js 和 pnpm）开发，提供直观易用的知识库问答与管理体验。该模块支持本地开发和生产环境构建，亦可通过 Docker 部署，方便快速上线。前端与后端 API 紧密集成，支持多种交互场景，满足不同用户需求。

**安装依赖**

```bash
cd sources/gc-qa-rag-frontend
pnpm install
```

**启动开发环境**

```bash
pnpm run dev
```

**构建生产包**

```bash
pnpm run build
```

## 3. 其他说明

-   各模块均支持 Docker 部署，建议生产环境使用容器化。
-   配置文件请根据实际环境修改。
