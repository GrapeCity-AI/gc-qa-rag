#!/bin/bash

# GC-QA-RAG Docker Hub 发布脚本
# 使用方法: ./scripts/publish-dockerhub.sh [version]

set -e

# 配置变量
DOCKERHUB_USERNAME="your-dockerhub-username"  # 请替换为你的Docker Hub用户名
VERSION=${1:-latest}
PROJECT_NAME="gc-qa-rag"

echo "🚀 开始发布 GC-QA-RAG 镜像到 Docker Hub"
echo "版本: $VERSION"
echo "Docker Hub 用户名: $DOCKERHUB_USERNAME"

# 构建并推送 server 镜像
echo "📦 构建 server 镜像..."
cd sources/gc-qa-rag-server
docker build -t $DOCKERHUB_USERNAME/$PROJECT_NAME-server:$VERSION .
docker build -t $DOCKERHUB_USERNAME/$PROJECT_NAME-server:latest .
echo "✅ server 镜像构建完成"

echo "📤 推送 server 镜像到 Docker Hub..."
docker push $DOCKERHUB_USERNAME/$PROJECT_NAME-server:$VERSION
docker push $DOCKERHUB_USERNAME/$PROJECT_NAME-server:latest
echo "✅ server 镜像推送完成"

# 构建并推送 etl 镜像
echo "📦 构建 ETL 镜像..."
cd ../gc-qa-rag-etl
docker build -t $DOCKERHUB_USERNAME/$PROJECT_NAME-etl:$VERSION .
docker build -t $DOCKERHUB_USERNAME/$PROJECT_NAME-etl:latest .
echo "✅ ETL 镜像构建完成"

echo "📤 推送 ETL 镜像到 Docker Hub..."
docker push $DOCKERHUB_USERNAME/$PROJECT_NAME-etl:$VERSION
docker push $DOCKERHUB_USERNAME/$PROJECT_NAME-etl:latest
echo "✅ ETL 镜像推送完成"

# 构建并推送 frontend 镜像
echo "📦 构建 frontend 镜像..."
cd ../gc-qa-rag-frontend
docker build -t $DOCKERHUB_USERNAME/$PROJECT_NAME-frontend:$VERSION .
docker build -t $DOCKERHUB_USERNAME/$PROJECT_NAME-frontend:latest .
echo "✅ frontend 镜像构建完成"

echo "📤 推送 frontend 镜像到 Docker Hub..."
docker push $DOCKERHUB_USERNAME/$PROJECT_NAME-frontend:$VERSION
docker push $DOCKERHUB_USERNAME/$PROJECT_NAME-frontend:latest
echo "✅ frontend 镜像推送完成"

# 回到项目根目录
cd ../../

echo "🎉 所有镜像发布完成！"
echo ""
echo "📋 发布的镜像列表："
echo "  - $DOCKERHUB_USERNAME/$PROJECT_NAME-server:$VERSION"
echo "  - $DOCKERHUB_USERNAME/$PROJECT_NAME-server:latest"
echo "  - $DOCKERHUB_USERNAME/$PROJECT_NAME-etl:$VERSION"
echo "  - $DOCKERHUB_USERNAME/$PROJECT_NAME-etl:latest"
echo "  - $DOCKERHUB_USERNAME/$PROJECT_NAME-frontend:$VERSION"
echo "  - $DOCKERHUB_USERNAME/$PROJECT_NAME-frontend:latest"
echo ""
echo "🔗 访问地址: https://hub.docker.com/r/$DOCKERHUB_USERNAME"
