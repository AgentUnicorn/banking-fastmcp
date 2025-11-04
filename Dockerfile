# Use Astral's official uv image with Python 3.12
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install uv binary (ensures latest uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Pre-cache dependencies using uv.lock + pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the entire application into container
COPY . /app

# Install dependencies into .venv (creates virtual environment)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose FastAPI port
EXPOSE 8005

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8005
ENV PATH="/app/.venv/bin:$PATH"

# Run the FastAPI app with Uvicorn directly (no python main)
CMD ["uv", "run", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8005", "--log-level", "info"]

