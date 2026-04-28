ARG PYTHON_BUILD_IMAGE=python:3.12-slim-bookworm
ARG PYTHON_RUNTIME_IMAGE=python:3.12-slim-bookworm

FROM ${PYTHON_BUILD_IMAGE} AS build

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY --from=ghcr.io/astral-sh/uv:0.10.0 /uv /uvx /bin/

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-install-project

COPY config ./config
COPY weather ./weather
COPY manage.py ./manage.py
RUN uv sync --locked

FROM ${PYTHON_RUNTIME_IMAGE} AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

COPY --from=build /app/.venv /app/.venv
COPY --from=build /app/config ./config
COPY --from=build /app/weather ./weather
COPY --from=build /app/manage.py ./manage.py
COPY --from=build /app/pyproject.toml ./pyproject.toml
COPY --from=build /app/README.md ./README.md

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info"]
