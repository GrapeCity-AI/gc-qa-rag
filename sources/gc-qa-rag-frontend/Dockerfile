# 第一阶段：构建应用
FROM node:20-slim as builder

# 设置工作目录
WORKDIR /app

# 安装pnpm
RUN npm install -g pnpm

# 复制package.json和pnpm-lock.yaml
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建应用
RUN pnpm run build

# 第二阶段：部署到Nginx
FROM nginx:alpine

# Copy the custom Nginx configuration file to the default location in the container
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Copy the local dist directory to the /usr/share/nginx/html directory in the container
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx. The default CMD is already set to start Nginx, so no need to specify it here