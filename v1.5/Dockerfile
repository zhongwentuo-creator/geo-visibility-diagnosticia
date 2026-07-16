FROM python:3.12-slim

# GitHub 发布后，此 Dockerfile 位于仓库的 v1.5/ 目录；构建上下文必须是仓库根目录。
WORKDIR /app

COPY config.py main.py /app/engine/
COPY stages /app/engine/stages
COPY report /app/engine/report
COPY utils /app/engine/utils
COPY v1.5/requirements.txt /app/web/requirements.txt
RUN pip install --no-cache-dir -r /app/web/requirements.txt

COPY v1.5/src /app/web
WORKDIR /app/web

ENV GEO_ENGINE_ROOT=/app/engine
ENV PYTHONPATH=/app/web:/app/engine
ENV PORT=8000
EXPOSE 8000

CMD uvicorn api:app --host 0.0.0.0 --port "${PORT}"
