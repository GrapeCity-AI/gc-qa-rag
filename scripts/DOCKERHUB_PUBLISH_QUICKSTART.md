# 🚀 Docker Hub 发布快速开始指南

本指南将帮助你在 5 分钟内完成 GC-QA-RAG 项目到 Docker Hub 的发布。

## 📋 前置检查清单

-   [ ] 已注册 Docker Hub 账户
-   [ ] 已安装 Docker Desktop
-   [ ] 已登录 Docker Hub (`docker login`)
-   [ ] 已获取 GitHub 仓库的写入权限

## ⚡ 5 分钟快速发布

### 1. 配置 GitHub Secrets（仅首次需要）

在 GitHub 仓库设置中添加以下 Secrets：

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 添加以下 Secrets：
    - `DOCKERHUB_LOGIN_USERNAME`: 你的 Docker Hub 登录用户名
    - `DOCKERHUB_USERNAME`: 你的 Docker Hub 用户名
    - `DOCKERHUB_TOKEN`: 你的 Docker Hub 访问令牌

### 2. 发布方式选择

#### 🎯 方式一：GitHub Actions 自动发布（推荐）

```bash
# 1. 创建版本标签
git tag v1.0.0

# 2. 推送标签到 GitHub
git push origin v1.0.0
```

推送标签后，GitHub Actions 会自动：

-   构建所有 Docker 镜像
-   推送到 Docker Hub
-   创建 GitHub Release

#### 🎯 方式二：手动发布

**Windows 用户：**

```powershell
# 1. 修改脚本中的用户名
# 编辑 scripts/publish-dockerhub.ps1，将 your-dockerhub-username 替换为你的用户名

# 2. 执行发布脚本
.\scripts\publish-dockerhub.ps1 v1.0.0
```

**Linux/Mac 用户：**

```bash
# 1. 修改脚本中的用户名
# 编辑 scripts/publish-dockerhub.sh，将 your-dockerhub-username 替换为你的用户名

# 2. 添加执行权限
chmod +x scripts/publish-dockerhub.sh

# 3. 执行发布脚本
./scripts/publish-dockerhub.sh v1.0.0
```

## ✅ 验证发布结果

### 1. 检查 Docker Hub 仓库

访问：`https://hub.docker.com/r/你的用户名`

你应该能看到以下镜像：

-   `gc-qa-rag-server:latest`
-   `gc-qa-rag-server:v1.0.0`
-   `gc-qa-rag-etl:latest`
-   `gc-qa-rag-etl:v1.0.0`
-   `gc-qa-rag-frontend:latest`
-   `gc-qa-rag-frontend:v1.0.0`

### 2. 测试镜像拉取

```bash
docker pull 你的用户名/gc-qa-rag-server:latest
docker pull 你的用户名/gc-qa-rag-etl:latest
docker pull 你的用户名/gc-qa-rag-frontend:latest
```

## 🔗 使用发布的镜像

### 1. 更新 docker-compose 文件

编辑 `sources/gc-qa-rag-server/deploy/docker-compose.dockerhub.yml`：

```yaml
server:
    image: 你的用户名/gc-qa-rag-server:latest
frontend:
    image: 你的用户名/gc-qa-rag-frontend:latest
```

编辑 `sources/gc-qa-rag-etl/docker-compose.dockerhub.yml`：

```yaml
rag-etl:
    image: 你的用户名/gc-qa-rag-etl:latest
```

### 2. 一键部署

```bash
# 部署主服务
cd sources/gc-qa-rag-server/deploy
docker compose -f docker-compose.dockerhub.yml up -d

# 部署 ETL 管理后台
cd ../../gc-qa-rag-etl
docker compose -f docker-compose.dockerhub.yml up -d
```

## 📝 版本管理最佳实践

### 1. 语义化版本号

-   `v1.0.0`: 主版本.次版本.修订版本
-   `v1.1.0`: 新功能发布
-   `v1.0.1`: Bug 修复

### 2. 发布流程

```bash
# 1. 更新代码并提交
git add .
git commit -m "feat: 新功能"
git push origin main

# 2. 创建版本标签
git tag v1.1.0
git push origin v1.1.0

# 3. GitHub Actions 自动发布
# 等待几分钟，镜像会自动发布到 Docker Hub
```

## 🆘 常见问题

### Q: 推送失败，提示权限不足

A: 检查 Docker Hub 登录状态和用户名是否正确

### Q: GitHub Actions 失败

A: 检查 GitHub Secrets 是否配置正确

### Q: 如何删除已发布的镜像

A: 在 Docker Hub 网页界面删除，或使用 Docker Hub API

### Q: 如何更新 latest 标签

A: 重新发布相同版本或新版本即可

## 📚 详细文档

-   [完整发布指南](./docs/zh/4-发布指南/Docker-Hub发布指南.md)
-   [Docker Hub 官方文档](https://docs.docker.com/docker-hub/)
-   [GitHub Actions 文档](https://docs.github.com/en/actions)

## 🎉 恭喜！

你已经成功将 GC-QA-RAG 发布到 Docker Hub！现在其他用户可以通过以下方式快速部署你的项目：

```bash
# 克隆项目
git clone https://github.com/GrapeCity-AI/gc-qa-rag.git
cd gc-qa-rag

# 配置 API 密钥
# 编辑配置文件...

# 使用你的镜像部署主服务
cd sources/gc-qa-rag-server/deploy
docker compose -f docker-compose.dockerhub.yml up -d

# 使用你的镜像部署 ETL 管理后台
cd ../../gc-qa-rag-etl
docker compose -f docker-compose.dockerhub.yml up -d
```
