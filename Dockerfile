FROM python:3.12-alpine AS requirements-builder

WORKDIR /tmp
COPY poetry.lock pyproject.toml ./

RUN python -m pip install poetry && \
    poetry export -f requirements.txt -o requirements.txt

FROM python:3.12-alpine

WORKDIR /app

ENV PYTHONPATH /app

COPY config/ ./config/
COPY --from=requirements-builder /tmp/requirements.txt ./
COPY lesbot/ ./lesbot/

VOLUME ["/app/config", "/app/logs"]

RUN apk update && \
    apk add --no-cache libmagic && \
    python -m pip install -r requirements.txt

CMD ["/usr/local/bin/python", "/app/lesbot/app.py"]
