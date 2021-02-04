FROM python:3.9-alpine3.12

# enables proper stdout flushing
ENV PYTHONUNBUFFERED yes
# no .pyc files
ENV PYTHONDONTWRITEBYTECODE yes

# pip optimizations
ENV PIP_NO_CACHE_DIR yes
ENV PIP_DISABLE_PIP_VERSION_CHECK yes

WORKDIR /code

COPY requirements.txt .

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    && pip install -U pip \
    && pip install -U -r requirements.txt \
    && apk del --purge .build-deps

RUN addgroup -S potato_bot \
    && adduser -S potato_bot -G potato_bot \
    && chown -R potato_bot:potato_bot /code

COPY --chown=potato_bot:potato_bot potato_bot potato_bot
COPY --chown=potato_bot:potato_bot migrations migrations

USER potato_bot

ENTRYPOINT ["python", "-m", "potato_bot"]
