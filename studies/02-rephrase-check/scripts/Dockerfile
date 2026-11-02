# SWT-Bench harness, unmodified, at the vendored commit. Build with vendor/swt-bench as context.
# Cloning the context checks out committed files with LF endings, whatever the Windows copy has.
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY . /ctx
RUN git clone /ctx /app && rm -rf /ctx && pip install --no-cache-dir uv==0.5.31
WORKDIR /app
RUN uv sync --frozen --no-dev
ENV PATH=/app/.venv/bin:$PATH
