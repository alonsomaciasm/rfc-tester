import logging
import json
import uuid
import os
import hashlib
from logging.handlers import TimedRotatingFileHandler
from typing import Any, Dict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class JSONFormatter(logging.Formatter):
    """
    Formateador de logs en estructura JSON plana para sistemas de auditoría enterprise.
    Garantiza estricto cumplimiento de 'Zero PII Logging' (Sin RFC, Nombre, CP ni IP en texto plano).
    """
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name
        }
        
        # Inyección de metadatos técnicos de auditoría sin PII
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "http_method"):
            log_obj["http_method"] = record.http_method
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "process_time_ms"):
            log_obj["process_time_ms"] = record.process_time_ms
        if hasattr(record, "client_ip_hash"):
            log_obj["client_ip_hash"] = record.client_ip_hash
        if hasattr(record, "user_agent_hash"):
            log_obj["user_agent_hash"] = record.user_agent_hash

        return json.dumps(log_obj, ensure_ascii=False)

def hash_anonymize(data: str) -> str:
    """Aplica hashing SHA-256 trunco para anonimizar datos técnicos sin registrar PII."""
    if not data:
        return "N/A"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

def setup_logger():
    logger = logging.getLogger("rfc_api")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = JSONFormatter()
        
        # 1. Handler para consola (Docker stdout)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        
        # 2. Handler de Archivos con Rotación Diaria a medianoche (90 Días de Retención)
        try:
            log_dir = os.getenv("LOG_DIR", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_filepath = os.path.join(log_dir, "api_audit.log")
            
            file_handler = TimedRotatingFileHandler(
                filename=log_filepath,
                when="midnight",
                interval=1,
                backupCount=90,  # Conserva 90 días exactos de auditoría
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.suffix = "%Y-%m-%d.log"
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            logger.warning(f"No se pudo inicializar el archivo de log en disco ({e}). Fallback activado a stdout.")
        
        
    return logger

logger = setup_logger()

class AuditCorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware que asigna un X-Request-ID a cada solicitud para trazabilidad y auditoría.
    """
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Anonimización Hash para auditoría técnica de seguridad
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        request.state.client_ip_hash = hash_anonymize(client_ip)
        request.state.user_agent_hash = hash_anonymize(user_agent)
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

