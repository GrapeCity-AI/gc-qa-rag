# Build stage for frontend
FROM node:latest AS frontend-builder
WORKDIR /app
# Install pnpm
RUN npm install -g pnpm

# Copy frontend files
COPY etlapp-web/package.json etlapp-web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY etlapp-web/ ./
RUN pnpm build

# Final stage
FROM python:3.13
WORKDIR /app

# Install PDM
RUN pip install pdm

# Copy pdm files
COPY pyproject.toml pdm.lock ./

# Install dependencies
RUN pdm install --prod --no-editable

# Copy project files
COPY readme.md ./
COPY .config.*.json ./
COPY etlapp/ ./etlapp/
COPY etlapp_api/ ./etlapp_api/

# Copy frontend build files from builder stage
COPY --from=frontend-builder /app/dist ./etlapp-web/dist

# Expose the port
EXPOSE 8001

# Set environment variable
ENV GC_QA_RAG_ENV=development

# Run the application
CMD ["pdm", "run", "uvicorn", "etlapp_api.server:app", "--host", "0.0.0.0", "--port", "8001"]