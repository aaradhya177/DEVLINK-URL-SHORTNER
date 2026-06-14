FROM python:3.13-slim AS builder

ENV POETRY_VERSION=1.8.5 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1

WORKDIR /app

RUN python -m pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml ./
RUN poetry install --only main --no-root


FROM python:3.13-slim AS runtime

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system devlink && adduser --system --ingroup devlink devlink

COPY --from=builder /app/.venv /app/.venv
COPY worker ./worker

RUN chown -R devlink:devlink /app
USER devlink

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import worker.config, worker.consumer; print('ok')"

CMD ["python", "-m", "worker.worker"]
