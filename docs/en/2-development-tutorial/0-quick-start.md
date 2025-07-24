## 1. Module Overview

-   **gc-qa-rag-etl**  
    Used for knowledge base data collection, processing and vectorization (ETL process), supporting multiple data sources and embedding models. **Includes a Web management interface for convenient document upload and processing.**

-   **gc-qa-rag-server**  
    FastAPI-based backend service providing semantic retrieval, Q&A, reasoning and other APIs, integrating vector database (Qdrant) and relational database (MySQL).

-   **gc-qa-rag-frontend**  
    Frontend interface based on React + Ant Design, providing intelligent Q&A, search and other functions.

## 2. Environment Setup

### General Requirements

-   Recommended OS: Windows 10/11 or Linux
-   Recommended IDE: Visual Studio Code

### Dependencies

-   Python 3.13
-   Node.js 18+, pnpm
-   PDM (Python package management tool)
-   Docker (optional, recommended for production deployment)
-   MySQL 8+
-   Qdrant

## 3. Important Notice: Configuration Before Deployment ⚠️

**You must configure API keys before starting any deployment!**

The system relies on large language models and embedding models to provide services. Without correct API configuration, the deployed system will not work properly. Services need to be restarted if keys change.

### Get Required API Keys

You need to prepare the following API keys:

1. **Large Language Model API** (choose one):

    - Alibaba Cloud Bailian Platform: [https://bailian.console.aliyun.com/](https://bailian.console.aliyun.com/)
    - OpenAI API: [https://platform.openai.com/](https://platform.openai.com/)
    - Other OpenAI-compatible model services

2. **Embedding Model API**:
    - Recommend using Alibaba Cloud's text embedding model (code defaults to text-embedding-v4)

## 4. Deployment Steps

### 4.1 Simplest Way: Docker One-Click Deployment (Recommended for Beginners)

**Step 1: Configure API Keys**

Before deployment, please configure as follows:

```bash
# 1. Clone project
git clone https://github.com/GrapeCity-AI/gc-qa-rag.git
cd gc-qa-rag

# 2. Configure ETL module
# Edit sources/gc-qa-rag-etl/.config.production.json
# Fill in your API keys

# 3. Configure server
# Edit sources/gc-qa-rag-server/.config.production.json
# Fill in your API keys
```

**Step 2: One-Click Deployment**

```bash
# Enter deployment directory
cd sources/gc-qa-rag-server/deploy

# Start core services (MySQL, Qdrant, backend, frontend)
docker compose up -d --build

# Start ETL service
cd ../../gc-qa-rag-etl
docker build -t rag-etl:latest .
docker run -d --name rag-etl -p 8001:8001 -e GC_QA_RAG_ENV=production rag-etl:latest
```

**Step 3: Upload Data and Test**

1. Visit ETL management backend: http://localhost:8001
2. Upload your documents (PDF, Word, Markdown, etc.)
3. Wait for system to process documents and generate Q&A pairs
4. Publish data to knowledge base
5. Visit frontend interface: http://localhost:80
6. Start asking questions to test!

**Complete Usage Flow**:

```
Configure API Keys → Docker Deploy → Upload Documents → ETL Process → Publish Data → Frontend Test
```

### 4.2 Manual Deployment of Each Module

If you want to understand each module in depth or do development, you can choose manual deployment:

### 4.2.1 gc-qa-rag-etl

#### Install Dependencies

```bash
# Enter directory
cd sources/gc-qa-rag-etl

# Install dependencies
pdm install
```

#### Configure Environment (Required)

-   **Important**: Modify `.config.development.json` or `.config.production.json`, fill in API Keys and addresses for LLM, Embedding, Qdrant and other services.

#### Start ETL Management Service

```bash
# Start Web management interface
pdm run server

# Visit http://localhost:8001 for document upload and processing
```

#### Command Line ETL Process

```bash
# Convert generic documents to text files
pdm run das

# Generate QA pairs and build vectors
pdm run etl

# Publish vectors to knowledge base
pdm run ved
```

### 4.2.2 gc-qa-rag-server

#### Install Dependencies

```bash
cd sources/gc-qa-rag-server
pdm install
```

#### Configure Environment (Required)

-   **Important**: Modify `.config.development.json` or `.config.production.json`, configure database, Qdrant, LLM and other information.

#### Start Service

```bash
# Development mode
pdm run dev

# Production mode
pdm run start
```

-   Access URL: `http://localhost:8000`

#### Docker Deployment

```bash
docker build -t rag-server .
docker run -p 8000:8000 rag-server
```

### 4.2.3 gc-qa-rag-frontend

#### Install Dependencies

```bash
cd sources/gc-qa-rag-frontend
pnpm install
```

#### Local Development

```bash
pnpm run dev
```

#### Build Production Package

```bash
pnpm run build
```

#### Docker Deployment

```bash
docker build -t rag-frontend .
docker run -p 80:80 rag-frontend
```

## 5. Complete Operation Guide for Beginners

If you are a complete beginner, it's recommended to follow this order strictly:

### Phase 1: Preparation

1. ✅ Ensure Docker is installed
2. ✅ Get large language model API keys
3. ✅ Clone project locally

### Phase 2: Configure System

4. ✅ Configure ETL module API keys
5. ✅ Configure server API keys
6. ✅ Check configuration file format is correct

### Phase 3: Deploy Services

7. ✅ Execute Docker one-click deployment command
8. ✅ Verify all containers start normally
9. ✅ Check if services are accessible

### Phase 4: Add Data

10. ✅ Visit ETL management interface (http://localhost:8001)
11. ✅ Upload test documents
12. ✅ Wait for ETL processing to complete
13. ✅ Publish data to knowledge base

### Phase 5: Test Usage

14. ✅ Visit frontend interface (http://localhost:80)
15. ✅ Ask questions based on uploaded document content
16. ✅ Verify system answer quality
17. ✅ Start official usage!

## 6. Common Issues and Solutions

-   **Services unresponsive after deployment**: First check if API Keys are correctly configured, view Docker logs to troubleshoot errors.
-   **Frontend cannot get answers**: Confirm vector database has data, need to upload and process documents through ETL first.
-   **ETL processing fails**: Check if document format is supported, if API keys are valid.
-   **Port conflicts**: Ensure ports 8000 (backend), 80 (frontend), 8001 (ETL), 3306 (MySQL), 6333 (Qdrant) are not occupied.
-   **Dependency installation fails**: Check Python, Node.js, PDM, pnpm versions, recommend using officially recommended versions.
-   **Database connection fails**: Confirm MySQL/Qdrant configuration is correct, container network connectivity.
-   **DAS configuration questions**: DAS is data acquisition system (crawler), if you only want to upload local documents, you can leave it empty temporarily.

For detailed parameter descriptions or other issues, please check each module's `README.md` or see the [Docker Deployment Tutorial](./1-Docker-deployment.md) for detailed instructions.
