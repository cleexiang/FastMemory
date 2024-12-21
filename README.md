# AI Memory Service

A FastAPI-based service that provides long-term memory capabilities for AI chatbots using vector databases.

## Features

- Vector-based memory storage and retrieval
- Support for multiple vector database backends (OpenSearch, Pinecone)
- Fact extraction and memory management using LLMs
- RESTful API interface
- Configurable logging and monitoring

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:

````env
OPENROUTER_API_KEY=your_key
LANGFUSE_PUBLIC_KEY=your_key
LANGFUSE_SECRET_KEY=your_key
LANGFUSE_HOST=your_host
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=your_index

3. Run the server:

```bash
python main.py
````

## API Documentation

After starting the server, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
