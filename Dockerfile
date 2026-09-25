FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # The JSON store lives on a mounted volume so a redeploy does not wipe the
    # demo caseload. Without a volume it is just container-local and resets.
    BRIDGE_DATA=/data/bridge.json

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests

RUN mkdir -p /data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD python -c "import os,urllib.request,sys; port=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz').status==200 else 1)"

# Shell form on purpose: Render assigns the port through PORT, and the app has
# to bind the one it was given. 8000 stays the default so `docker run -p 8000`
# and ./run.sh still behave the same.
CMD python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
