# GC-QA-RAG Project Quick Start

## Overview

The GC-QA-RAG project adopts a modular, distributed architecture design, splitting the overall system into three independent sub-modules: ETL (knowledge base construction), Server (backend services), and Frontend (main frontend interface). Both ETL and Server are independent web applications, responsible for knowledge base data processing and backend API services respectively. The frontend and backend are completely separated, facilitating independent development, testing, and deployment. Each module communicates through standard APIs, greatly improving system scalability and maintainability. Additionally, the project has excellent Docker support, and all modules can be deployed with one-click containerization, greatly simplifying production environment integration and operations processes, suitable for various practical application scenarios.

The following is a quick compilation and running guide for each module.

## 1. Environment Preparation

- Python (Python virtual environment, all versions 3.13)
- Node.js (recommended 16+, for frontend)
- PDM (Python package management tool)
- pnpm (frontend package management tool, recommended 8+)
- Docker (optional, supports containerized deployment)
- MySQL, Qdrant (backend dependency services)

## 2. Module Compilation and Running

### 2.1 ETL (Knowledge Base Construction and Supporting Frontend)

The ETL (Extract-Transform-Load) module is a core component of the GC-QA-RAG project, primarily responsible for knowledge base construction and management. This module implements data extraction, transformation, and loading processes, supporting efficient processing and storage of multi-source data. The ETL module includes not only the CLI main program but also a visual frontend (etlapp-web), facilitating user management and monitoring of the knowledge base construction process. The main program is developed based on Python, and the supporting frontend is built based on Node.js and pnpm. Working together, they greatly improve the automation and usability of knowledge base construction.

#### 2.1.1 ETL Main Program

**Install Dependencies**

```bash
cd sources/gc-qa-rag-etl
pdm install
```

**Run**

```bash
pdm run dev
```

Service runs by default on `http://0.0.0.0:8001`

#### 2.1.2 etlapp-web (ETL Supporting Frontend)

Directory: `sources/gc-qa-rag-etl/etlapp-web`

**Install Dependencies**

```bash
cd sources/gc-qa-rag-etl/etlapp-web
pnpm install
```

**Start Development Environment**

```bash
pnpm run dev
```

### 2.2 Server (Backend Services)

The Server module is the backend core of the GC-QA-RAG project, responsible for providing API support for the frontend and ETL modules. This module is developed based on Python, relies on MySQL as the relational database, Qdrant as the vector database, and can integrate various AI services. The Server supports flexible development and production environment configurations, has good scalability and high performance, suitable for large-scale knowledge base Q&A scenarios. One-click deployment can be achieved through Docker, facilitating production environment integration.

Directory: `sources/gc-qa-rag-server`

**Install Dependencies**

```bash
cd sources/gc-qa-rag-server
pdm install
```

**Configure Environment**

- Modify `.config.development.json` or `.config.production.json` to configure database, Qdrant, AI services, and other parameters.

**Start Service**

Development mode:

```bash
pdm run dev
```

Service runs by default on `http://0.0.0.0:8000`

### 2.3 Frontend (Main Frontend Interface)

The Frontend module is the main user interface of the GC-QA-RAG project, developed based on modern frontend technology stack (such as Vue/React, Node.js, and pnpm), providing an intuitive and easy-to-use knowledge base Q&A and management experience. This module supports local development and production environment building, and can also be deployed through Docker for quick online deployment. The frontend is tightly integrated with backend APIs, supporting various interaction scenarios to meet different user needs.

**Install Dependencies**

```bash
cd sources/gc-qa-rag-frontend
pnpm install
```

**Start Development Environment**

```bash
pnpm run dev
```

**Build Production Package**

```bash
pnpm run build
```

## 3. Additional Notes

- All modules support Docker deployment; containerization is recommended for production environments.
- Please modify configuration files according to your actual environment. 