# GC QA RAG Server

A Retrieval-Augmented Generation (RAG) server for question answering, built with FastAPI and integrated with multiple AI services.

## Features

-   **Semantic Search**: Hybrid search capabilities combining semantic and keyword-based search
-   **Chat Interface**: Streaming chat responses with context-aware answers
-   **Research Mode**: In-depth research capabilities for complex queries
-   **Thinking Mode**: Advanced reasoning and analysis of search results
-   **Feedback System**: User feedback collection and rating system
-   **Search History**: Track and retrieve search history
-   **Rate Limiting**: Built-in rate limiting for API endpoints

## Tech Stack

-   **Backend**: FastAPI
-   **Vector Database**: Qdrant
-   **AI Services**:
    -   DashScope
    -   OpenAI
-   **Database**: MySQL
-   **Environment Management**: PDM (Python Development Master)

## Prerequisites

-   Python 3.11
-   PDM
-   MySQL
-   Qdrant

## Installation

1. Install dependencies using PDM:

```bash
pdm install
```

2. Configure environment:
    - Update `.config.development.json` for development
    - Update `.config.production.json` for production

## Running the Server

### Development Mode

```bash
pdm run dev
```

### Production Mode

```bash
pdm run start
```

The server will start on `http://0.0.0.0:8000`

## API Endpoints

### Search

-   **POST** `/search/`
    -   Search for information using keywords
    -   Supports different search modes

### Chat

-   **POST** `/chat_streaming/`
    -   Streaming chat interface
    -   Context-aware responses

### Research

-   **POST** `/reasearch_streaming/`
    -   In-depth research mode
    -   Detailed analysis of topics

### Thinking

-   **POST** `/think_streaming/`
    -   Advanced reasoning mode
    -   Deep analysis of search results

### Feedback

-   **POST** `/feedback/`
    -   Submit feedback on answers
    -   Rate and comment on responses

## Docker Support

The project includes a Dockerfile for containerized deployment:

```bash
docker build -t rag-server .
docker run -p 8000:8000 rag-server
```

## Docker Export Images

```cmd
docker save -o ./rag_images.tar rag-frontend:latest rag-server:latest qdrant/qdrant:latest mysql:latest
```

## Configuration

The application uses JSON configuration files:

-   `.config.development.json` for development
-   `.config.production.json` for production

Key configuration options include:

-   Database settings
-   AI service API keys
-   Vector database settings

## License

This project is licensed under the MIT License
