# Docker 部署教程

本教程将指导您如何使用 Docker 部署 GC-QA-RAG 系统。提供两种部署方式：**一键部署**（推荐）和**单独部署**。

## 1. 环境准备

### 必需工具

-   Docker 20.0+
-   Docker Compose 2.0+

### 系统要求

-   推荐内存：8GB+
-   推荐存储：20GB+ 可用空间

## 2. 一键部署（推荐）

### 2.1 部署步骤

使用预配置的 `docker-compose.yml` 可以一键启动完整的 RAG 系统，包括：

-   MySQL 数据库
-   Qdrant 向量数据库
-   RAG 后端服务
-   RAG 前端界面

**注意**：以上仅包含 RAG 系统核心服务，ETL 数据处理模块需要单独部署。

```bash
# 进入部署目录
cd sources/gc-qa-rag-server/deploy

# 构建并启动所有服务
docker compose up -d
```

### 2.2 ETL 模块部署

ETL 模块负责数据采集、处理和向量化，是完整 RAG 系统的重要组成部分。需要在核心服务启动后单独部署：

```bash
# 进入 ETL 目录
cd sources/gc-qa-rag-etl

# 构建 Docker 镜像
docker build -t rag-etl:latest .

# 运行容器
docker run -d \
  --name rag-etl \
  -p 8001:8001 \
  -e GC_QA_RAG_ENV=production \
  rag-etl:latest
```

### 2.3 服务访问

部署完成后，可通过以下地址访问：

-   **前端界面**：http://localhost
-   **后端 API**：http://localhost:8000
-   **MySQL**：localhost:3306
-   **Qdrant**：http://localhost:6333

ETL 应用：

-   **ETL 管理界面**：http://localhost:8001

### 2.4 默认配置

| 服务       | 端口      | 用户名         | 密码     |
| ---------- | --------- | -------------- | -------- |
| MySQL      | 3306      | search_db_user | 12345678 |
| MySQL Root | 3306      | root           | 12345678 |
| Qdrant     | 6333/6334 | -              | -        |
| ETL        | 8001      | -              | -        |

### 2.5 停止服务

```bash
# 停止所有服务
docker compose down

# 停止 ETL 服务
docker stop rag-etl
docker rm rag-etl

# 停止服务并删除数据卷（谨慎操作）
docker compose down -v
```

## 3. 单独部署

如果需要更灵活的部署方式，可以单独构建和部署各个模块。

### 3.1 后端服务部署

```bash
# 进入服务端目录
cd sources/gc-qa-rag-server

# 构建 Docker 镜像
docker build -t rag-server:latest .

# 创建配置文件挂载点
mkdir -p config

# 运行容器
docker run -d \
  --name rag-server \
  -p 8000:8000 \
  -e GC_QA_RAG_ENV=production \
  rag-server:latest
```

### 3.2 前端界面部署

```bash
# 进入前端目录
cd sources/gc-qa-rag-frontend

# 先构建前端资源
pnpm install
pnpm run build

# 构建 Docker 镜像
docker build -t rag-frontend:latest .

# 运行容器
docker run -d \
  --name rag-frontend \
  -p 80:80 \
  rag-frontend:latest
```

### 3.3 数据库部署

#### MySQL 部署

```bash
docker run -d \
  --name rag-mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=12345678 \
  -e MYSQL_DATABASE=search_db \
  -e MYSQL_USER=search_db_user \
  -e MYSQL_PASSWORD=12345678 \
  -v rag-mysql-data:/var/lib/mysql \
  mysql:latest
```

#### Qdrant 部署

```bash
docker run -d \
  --name rag-qdrant \
  -p 6333:6333 \
  -p 6334:6334 \
  -e QDRANT__SERVICE__GRPC_PORT=6334 \
  -e QDRANT__SERVICE__HTTP_PORT=6333 \
  -v rag-qdrant-data:/qdrant/storage \
  --memory 8g \
  qdrant/qdrant:latest
```

## 4. 配置文件说明

### 4.1 ETL 配置

在 `sources/gc-qa-rag-etl/.config.production.json` 中配置：

```json
{
    "das": {
        "base_url_page": "",
        "base_url_thread": "",
        "token": ""
    },
    "llm": {
        "api_key": "",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": "qwen-plus"
    },
    "embedding": {
        "api_key": "your-dashscope-api-key"
    },
    "vector_db": {
        "host": "http://localhost:6333"
    },
    "root_path": "./.rag-cache",
    "log_path": "./"
}
```

### 4.2 服务端配置

在 `sources/gc-qa-rag-server/.config.production.json` 中配置：

```json
{
    "database": {
        "host": "rag_mysql_container",
        "port": 3306,
        "username": "search_db_user",
        "password": "12345678",
        "database": "search_db"
    },
    "qdrant": {
        "url": "http://rag_qdrant_container:6333"
    },
    "llm": {
        "provider": "openai",
        "api_key": "your-api-key",
        "base_url": "https://api.openai.com/v1"
    }
}
```

## 5. 生产环境优化

### 5.1 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
    server:
        deploy:
            resources:
                limits:
                    memory: 2G
                    cpus: "1.0"
                reservations:
                    memory: 1G
```

## 6. 常见问题

### 6.1 端口冲突

如果端口被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
    - "8080:8000" # 将后端服务映射到 8080 端口
```

### 6.2 内存不足

如果系统内存不足，可以调整 Qdrant 的内存限制：

```yaml
deploy:
    resources:
        limits:
            memory: 4G # 降低内存限制
```

### 6.3 数据持久化

确保数据卷正确挂载，避免容器重启后数据丢失：

```bash
# 查看数据卷
docker volume ls

# 备份数据卷
docker run --rm -v rag-mysql-data:/data -v $(pwd):/backup alpine tar czf /backup/mysql-backup.tar.gz -C /data .
```

### 6.4 网络连接问题

如果容器间无法通信，检查网络配置：

```bash
# 查看网络
docker network ls

# 检查容器网络
docker network inspect deploy_rag_network
```

## 7. 监控和维护

### 7.1 容器状态监控

```bash
# 查看所有服务状态
docker compose ps

# 查看服务日志
docker compose logs -f server

# 查看资源使用情况
docker stats
```

通过以上步骤，您就可以成功部署 GC-QA-RAG 系统了。推荐使用一键部署方式，简单快捷且配置完整。
