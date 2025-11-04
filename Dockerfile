# Use the official UV Python image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Copy uv binary (for compatibility)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Pre-cache dependencies based on lockfile
RUN --mount=type=cache,id=cache-uv,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy project files
COPY . /app

# Install all dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose port 8005 for FastMCP
EXPOSE 8005

# Use environment variable for Railway’s dynamic port (fallback to 8005)
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "${PORT:-8005}"]

