# Dev-oriented backend image: uv-managed deps + uvicorn with --reload.
FROM python:3.12-slim

# uv: fast, reproducible installs from pyproject.toml + uv.lock.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install deps first (cached unless the manifest/lock change). The source is bind-mounted
# at runtime by docker-compose, so we only need the dependency files here.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
