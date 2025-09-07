FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

ENV PATH="/venv/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy


# Set temporary working directory for installation
WORKDIR /venv

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /uvx /bin/

# Copy only dependencies for caching
COPY pyproject.toml uv.lock* /venv/

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --extra dev

# Set the working directory
WORKDIR /app

# Run the application
CMD ["./start.sh"]