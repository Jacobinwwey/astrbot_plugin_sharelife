FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY . .

ENV SHARELIFE_HOST=0.0.0.0 \
    SHARELIFE_PORT=8106 \
    SHARELIFE_DATA_ROOT=/data \
    SHARELIFE_SEED_DEMO=1 \
    SHARELIFE_STATE_BACKEND=sqlite \
    SHARELIFE_STATE_SQLITE_FILE=/data/sharelife_state.sqlite3 \
    SHARELIFE_STATE_MIGRATE_FROM_JSON=1

VOLUME ["/data"]
EXPOSE 8106

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${SHARELIFE_PORT:-8106}/api/health" >/dev/null || exit 1

CMD ["python3", "scripts/run_sharelife_webui_standalone.py"]
