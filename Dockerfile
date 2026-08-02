# Multi-stage Dockerfile para Hardening y optimización
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runner

WORKDIR /app

# Crear usuario y grupo sin privilegios root (Hardening Docker)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

# Copiar dependencias instaladas desde builder al PATH global del sistema
COPY --from=builder /install /usr/local
COPY --chown=appuser:appgroup ./app /app/app

# Crear directorio de logs con permisos para el contenedor
RUN mkdir -p /app/logs && chmod 777 /app/logs

ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
