FROM python:3.12-alpine AS requirements-builder

WORKDIR /tmp
COPY poetry.lock pyproject.toml ./

RUN set -ex && \
    python -m pip install --disable-pip-version-check poetry==1.8.3 && \
    poetry self add poetry-plugin-export && \
    poetry export -f requirements.txt -o requirements.txt

FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY config/ ./config/
COPY --from=requirements-builder /tmp/requirements.txt ./
COPY lesbot/ ./lesbot/

RUN set -ex && \
    addgroup -S nonroot && \
    adduser -S nonroot -G nonroot && \
    chown -R nonroot:nonroot /app

RUN set -ex && \
    apk update && \
    apk add --no-cache libmagic && \
    python -m pip install --disable-pip-version-check --no-cache-dir -r requirements.txt

CMD ["/usr/local/bin/python", "/app/lesbot/app.py"]

USER nonroot
