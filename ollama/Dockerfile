FROM ollama/ollama:latest

# Install curl for healthcheck
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Keep entrypoint/command from base image
