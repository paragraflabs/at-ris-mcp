# syntax=docker/dockerfile:1
# Minimal image for the at-ris-mcp MCP server (stdio transport).
FROM python:3.12-slim

# Descriptive OCI labels (used by registries/aggregators).
LABEL org.opencontainers.image.title="at-ris-mcp" \
      org.opencontainers.image.description="MCP server for Austria's legal information system (RIS): federal & state law, case law, gazettes, change monitoring." \
      org.opencontainers.image.source="https://github.com/paragraflabs/at-ris-mcp" \
      org.opencontainers.image.licenses="Apache-2.0" \
      io.modelcontextprotocol.server.name="io.github.paragraflabs/at-ris-mcp"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install the package (with the MCP server extra) from the source tree.
COPY pyproject.toml README.md LICENSE NOTICE CHANGELOG.md ./
COPY src ./src
RUN pip install ".[mcp]"

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# The server speaks MCP over stdio by default. For a hosted/remote deployment,
# run with an HTTP transport, e.g.:
#   docker run -e RIS_MCP_TRANSPORT=http -e RIS_MCP_HOST=0.0.0.0 -p 8000:8000 at-ris-mcp
EXPOSE 8000
ENTRYPOINT ["at-ris-mcp"]
