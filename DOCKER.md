# Docker Setup for Limitless OSINT Tool

This document describes how to set up and run the Limitless OSINT Tool using Docker.

## Prerequisites

- Docker
- Docker Compose
- OpenAI API key

## Setup

1. Create a `.env` file in the root directory with your OpenAI API key:

```
OPENAI_API_KEY=sk-your-openai-api-key
```

2. Make sure Docker and Docker Compose are installed on your system.

## Docker Commands

### Build and Start the Application

To build and start the application in detached mode:

```bash
docker-compose up -d
```

This will:
- Build the Docker image if it doesn't exist
- Create and start the container
- Map port 9000 to allow access to the Streamlit interface
- Mount the data directory as a volume for persistence
- Enable healthcheck to monitor application status

### View Logs

To view logs from the running container:

```bash
docker-compose logs -f
```

Press `Ctrl+C` to exit log viewing.

### Stop the Application

To stop the application and remove the container:

```bash
docker-compose down
```

### Rebuild the Application

If you make changes to the code or Dockerfile, rebuild the image:

```bash
docker-compose build
```

Then restart the application:

```bash
docker-compose up -d
```

### Clean Up

To stop and remove containers, networks, and volumes:

```bash
docker-compose down -v
```

## Accessing the Application

Once the container is running, access the application at:

```
http://localhost:9000
```

## Data Persistence

The application stores data in the `./data` directory, which is mounted as a volume in the Docker container. This ensures data persistence between container restarts.

## Security Features

The Docker container includes several security enhancements:

1. Non-root user: The application runs as a non-privileged user 'app'
2. Minimal base image: Uses python:3.9-slim to reduce attack surface
3. Version pinning: All dependencies have fixed versions to prevent unexpected changes

## Dependency Compatibility

The application uses specific package versions to ensure compatibility:

1. huggingface-hub==0.16.4
2. transformers==4.30.2 
3. sentence-transformers==2.2.2

These versions are known to work together. If you need to update any of these packages,
ensure you test for compatibility issues, as newer versions may introduce breaking changes.

## Troubleshooting

1. If the application fails to start, check the logs:
   ```bash
   docker-compose logs
   ```

2. If the OpenAI API key is not being recognized, make sure it's correctly set in the `.env` file.

3. If you need to access the container shell for debugging:
   ```bash
   docker exec -it limitless-osint bash
   ```

4. If the healthcheck is failing, verify that the application is running correctly:
   ```bash
   docker ps  # Check the STATUS column for health information
   ```

5. If you encounter dependency conflicts:
   ```bash
   docker exec -it limitless-osint pip list  # Check installed package versions
   ``` 