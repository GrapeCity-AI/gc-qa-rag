FROM python:3.11-slim

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install PDM
RUN pip install --no-cache-dir pdm

# Copy dependency file (skip lock to resolve for Python 3.11)
COPY ./pyproject.toml /code/

# Install project dependencies
RUN pdm install --prod --no-editable

# Enable PEP 582
ENV PYTHONPATH=/code/__pypackages__/3.11/lib
ENV PYTHONPATH=${PYTHONPATH}:/code

# Copy application code and configurations
COPY ./ragapp /code/ragapp
COPY ./.env ./.config.development.json ./.config.production.json /code/

EXPOSE 8000

# Run application (adjust this to your actual startup command)
CMD ["pdm", "run", "start"]