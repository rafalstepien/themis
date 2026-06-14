# ── Stage 1: dependency installer ────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project


# ── Stage 2: minimal runtime image ───────────────────────────────────────────
FROM python:3.14-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="Themis" \
      org.opencontainers.image.description="GitLab-native AI code review engine" \
      org.opencontainers.image.source="https://github.com/rstepien095/themis"

WORKDIR /app

# Copy pre-built venv and application source
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/
COPY main.py .

# Run as non-root for GitLab runner compatibility
RUN useradd --no-create-home --shell /bin/false themis
USER themis

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["python", "main.py"]
CMD ["--mode=engine"]
