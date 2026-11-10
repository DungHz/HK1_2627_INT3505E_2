# Stage 1: install dependencies in an isolated virtual environment.
FROM python:3.12-slim AS builder

WORKDIR /build
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: small, non-root runtime image.
FROM python:3.12-slim AS runtime

RUN groupadd --system app \
    && useradd --system --gid app --create-home app
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ /app/src/
COPY migrations/ /app/migrations/
COPY wsgi.py /app/wsgi.py

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

USER app
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]
