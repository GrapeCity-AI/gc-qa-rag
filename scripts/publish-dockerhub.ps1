# GC-QA-RAG Docker Hub 发布脚本 (PowerShell版本)
# 使用方法: .\scripts\publish-dockerhub.ps1 [version]

param(
    [string]$Version = "latest"
)

# 配置变量
$DockerHubUsername = "your-dockerhub-username"  # 请替换为你的Docker Hub用户名
$ProjectName = "gc-qa-rag"

Write-Host "🚀 开始发布 GC-QA-RAG 镜像到 Docker Hub" -ForegroundColor Green
Write-Host "版本: $Version" -ForegroundColor Yellow
Write-Host "Docker Hub 用户名: $DockerHubUsername" -ForegroundColor Yellow

# 构建并推送 server 镜像
Write-Host "📦 构建 server 镜像..." -ForegroundColor Cyan
Set-Location "sources\gc-qa-rag-server"
docker build -t "$DockerHubUsername/$ProjectName-server`:$Version" .
docker build -t "$DockerHubUsername/$ProjectName-server`:latest" .
Write-Host "✅ server 镜像构建完成" -ForegroundColor Green

Write-Host "📤 推送 server 镜像到 Docker Hub..." -ForegroundColor Cyan
docker push "$DockerHubUsername/$ProjectName-server`:$Version"
docker push "$DockerHubUsername/$ProjectName-server`:latest"
Write-Host "✅ server 镜像推送完成" -ForegroundColor Green

# 构建并推送 etl 镜像
Write-Host "📦 构建 ETL 镜像..." -ForegroundColor Cyan
Set-Location "..\gc-qa-rag-etl"
docker build -t "$DockerHubUsername/$ProjectName-etl`:$Version" .
docker build -t "$DockerHubUsername/$ProjectName-etl`:latest" .
Write-Host "✅ ETL 镜像构建完成" -ForegroundColor Green

Write-Host "📤 推送 ETL 镜像到 Docker Hub..." -ForegroundColor Cyan
docker push "$DockerHubUsername/$ProjectName-etl`:$Version"
docker push "$DockerHubUsername/$ProjectName-etl`:latest"
Write-Host "✅ ETL 镜像推送完成" -ForegroundColor Green

# 构建并推送 frontend 镜像
Write-Host "📦 构建 frontend 镜像..." -ForegroundColor Cyan
Set-Location "..\gc-qa-rag-frontend"
docker build -t "$DockerHubUsername/$ProjectName-frontend`:$Version" .
docker build -t "$DockerHubUsername/$ProjectName-frontend`:latest" .
Write-Host "✅ frontend 镜像构建完成" -ForegroundColor Green

Write-Host "📤 推送 frontend 镜像到 Docker Hub..." -ForegroundColor Cyan
docker push "$DockerHubUsername/$ProjectName-frontend`:$Version"
docker push "$DockerHubUsername/$ProjectName-frontend`:latest"
Write-Host "✅ frontend 镜像推送完成" -ForegroundColor Green

# 回到项目根目录
Set-Location "..\.."

Write-Host "🎉 所有镜像发布完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 发布的镜像列表：" -ForegroundColor Yellow
Write-Host "  - $DockerHubUsername/$ProjectName-server`:$Version"
Write-Host "  - $DockerHubUsername/$ProjectName-server`:latest"
Write-Host "  - $DockerHubUsername/$ProjectName-etl`:$Version"
Write-Host "  - $DockerHubUsername/$ProjectName-etl`:latest"
Write-Host "  - $DockerHubUsername/$ProjectName-frontend`:$Version"
Write-Host "  - $DockerHubUsername/$ProjectName-frontend`:latest"
Write-Host ""
Write-Host "🔗 访问地址: https://hub.docker.com/r/$DockerHubUsername" -ForegroundColor Blue
