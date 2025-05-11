# Limitless OSINT Tool

A powerful Open Source Intelligence (OSINT) tool with RAG (Retrieval Augmented Generation) capabilities, inspired by the Limitless platform. This tool helps intelligence professionals analyze documents, extract insights, and query intelligence using natural language.

## Features

- **Document Processing**: Upload, extract, and process intelligence documents (.pdf, .csv, .txt, etc.)
- **Advanced NLP**: Apply preprocessing techniques like stopword removal, lemmatization, and NER
- **Vector Search**: Use semantic search to find relevant intelligence across documents
- **RAG Capabilities**: Query your intelligence database using natural language
- **Interactive Dashboard**: View key metrics and recent activity

## Architecture

The application follows a modular architecture with clear separation of concerns:

- **Controllers**: Handle user interface and interaction logic
- **Services**: Implement business logic and orchestrate operations
- **Models**: Manage data persistence and retrieval
- **Utils**: Provide core functionality for document processing, embeddings, and LLM interaction

## Prerequisites

- Docker and Docker Compose
- OpenAI API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/limitless-osint-tool.git
   cd limitless-osint-tool
   ```

2. Set up your OpenAI API key in `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Docker Usage

1. Build and start the Docker container:
   ```
   docker-compose up -d
   ```

2. Access the application in your browser at `http://localhost:9000`

3. Upload documents through the "Upload Documents" tab

4. Search and analyze intelligence through the "Search Intelligence" tab

5. Stop the application:
   ```
   docker-compose down
   ```

## Docker Commands

- Build the Docker image:
  ```
  docker-compose build
  ```

- Start the application:
  ```
  docker-compose up -d
  ```

- View logs:
  ```
  docker-compose logs -f
  ```

- Stop the application:
  ```
  docker-compose down
  ```

- Restart the application:
  ```
  docker-compose restart
  ```

## Project Structure

```
limitless-osint-tool/
├── assets/           # Static assets
├── data/             # Data storage (persisted in Docker volume)
│   ├── chroma_db/    # Vector database
│   └── documents/    # Document metadata
├── docs/             # Documentation
├── models/           # Model definitions
├── notebooks/        # Jupyter notebooks for exploration
├── src/              # Source code
│   ├── controllers/  # UI controllers
│   ├── models/       # Data models
│   ├── services/     # Business logic
│   ├── utils/        # Utility functions
│   └── main.py       # Application entry point
├── .env              # Environment variables
├── Dockerfile        # Docker image definition
├── docker-compose.yml # Docker Compose configuration
├── requirements.txt  # Dependencies
└── README.md         # Project documentation
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Inspired by the Limitless OSINT platform
- Built with Streamlit, ChromaDB, Sentence Transformers, and OpenAI