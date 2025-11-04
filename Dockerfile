# Use the official UV Python image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Copy uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy only lock and config first (for better caching)
COPY uv.lock pyproject.toml ./

# Install dependencies (no mount flags)
RUN uv sync --locked --no-install-project

# Copy entire project
COPY . .

# Expose FastMCP port
EXPOSE 8005

# Run the server (Railway sets PORT automatically)
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8005", "--log-level", "info"]

