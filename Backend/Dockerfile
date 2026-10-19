# Backend AquaSmart (Flask). Build dari folder Backend/:
#   docker build -t aquasmart-backend .

# Stage 1: pasang dependensi ke venv terpisah supaya pip dan cache-nya
# tidak ikut ke image akhir.
FROM python:3.12-slim AS builder
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime.
FROM python:3.12-slim
# venv di /opt, bukan /root/.local, karena proses berjalan sebagai appuser
# yang tidak bisa membaca /root.
COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_CONFIG=production

WORKDIR /app
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/instance \
    && chown appuser:appuser /app/instance
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=4).status == 200 else 1)"

# --preload: wsgi.py menjalankan db.create_all() sekali di proses master,
# bukan sekali per worker yang bisa saling bertabrakan di Postgres.
CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "--preload"]
