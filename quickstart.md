# GC-QA-RAG 项目快速开始

本项目包含三个主要子模块：ETL（知识库构建及其配套前端）、Server（后端服务）、Frontend（主前端界面）。以下为各模块的快速编译与运行指南。

## 1. 环境准备

-   Python（Python 虚拟环境，版本均为 3.13）
-   Node.js（建议 16+，用于前端）
-   PDM（Python 包管理工具）
-   pnpm（前端包管理工具，推荐 8+）
-   Docker（可选，支持容器化部署）
-   MySQL、Qdrant（后端依赖服务）

## 2. 各模块编译与运行

### 2.1 ETL（知识库构建及配套前端）

目录：`sources/gc-qa-rag-etl`

#### 2.1.1 ETL 主程序

**安装依赖**

```bash
cd sources/gc-qa-rag-etl
pdm install
```

**运行**

```bash
pnpm run server
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

生产模式：

```bash
pdm run start
```

服务默认运行在 `http://0.0.0.0:8000`

**Docker 方式**

```bash
docker build -t rag-server .
docker run -p 8000:8000 rag-server
```

### 2.3 Frontend（主前端界面）

目录：`sources/gc-qa-rag-frontend`

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

**Docker 方式**

```bash
docker build -t rag-frontend .
```

## 3. 其他说明

-   各模块均支持 Docker 部署，建议生产环境使用容器化。
-   配置文件请根据实际环境修改。
-   详细功能和 API 说明请参考各模块 README。
