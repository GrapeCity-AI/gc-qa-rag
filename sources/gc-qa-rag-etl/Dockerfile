# Build stage for frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy frontend files
COPY etlapp-web/package.json etlapp-web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy the rest of the frontend source code and build it
COPY etlapp-web/ ./
RUN pnpm build

# Final stage
FROM python:3.11-slim
WORKDIR /app

# Install PDM
RUN pip install pdm

# Copy pdm file (skip lock to resolve for Python 3.11)
COPY pyproject.toml ./

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

ENV GC_QA_RAG_ENV=production

# Set Python path for PDM virtual environment
ENV PYTHONPATH=/app/.venv/lib/python3.11/site-packages

# Run the application
CMD ["pdm", "run", "uvicorn", "etlapp_api.server:app", "--host", "0.0.0.0", "--port", "8001"]