FROM python:3.13-slim

WORKDIR /code

# Copy files
COPY ./pyproject.toml ./pdm.lock ./.env /code/

# Intall pdm
RUN pip install --no-cache-dir pdm && \
    pdm --pep582 >> ~/.bashrc

# Install packages
RUN pdm install --prod

# Copy codes and configurations
COPY ./ragapp /code/ragapp
COPY ./.config.development.json ./.config.production.json /code/

EXPOSE 8000

# Run application
CMD ["pdm","start"]