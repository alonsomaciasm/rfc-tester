import unicodedata
from fastapi import FastAPI, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from app.config import settings
from app.schemas import (
    RFCValidationRequest, 
    SyntaxValidationResponse, 
    RFCMatchRequest, 
    LiveVerificationResponse,
    SATLiveVerificationResponse
)
from app.validator import (
    check_syntax_format, 
    verify_checksum, 
    extract_metadata, 
    clean_rfc
)
from contextlib import asynccontextmanager
from app.sat_service import verify_rfc_live_sat, verify_rfc_sat_live_service, close_http_client
from app.security import verify_api_key
from app.logger import logger, AuditCorrelationMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_http_client()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="API RESTful Enterprise para verificación sintáctica, cálculo de dígito verificador y cotejo de coincidencia de RFC (SAT México).",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware de Correlation ID / Auditoría
app.add_middleware(AuditCorrelationMiddleware)

# CORS Restringido
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Middleware de Límite de Payload (Protección DDoS Max 10KB) y Log de Auditoría Estructurado
@app.middleware("http")
async def audit_and_security_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 1. Límite de tamaño de Payload (Max 10 KB)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 10 * 1024:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "El cuerpo de la petición excede el tamaño máximo permitido (10KB)."}
        )

    response = await call_next(request)
    
    # 2. Inyección de Encabezados de Seguridad OWASP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.path in ["/docs", "/redoc", f"{settings.API_V1_STR}/openapi.json"]:
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com;"
        )
    else:
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    
    
    # 3. Log de Auditoría sin PII
    process_time_ms = round((time.time() - start_time) * 1000, 2)
    req_id = getattr(request.state, "request_id", "N/A")
    ip_hash = getattr(request.state, "client_ip_hash", "N/A")
    ua_hash = getattr(request.state, "user_agent_hash", "N/A")
    
    # Log estructurado (estricto Zero PII: sin registrar RFC, Nombre ni CP)
    logger.info(
        f"HTTP {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time_ms}ms",
        extra={
            "request_id": req_id,
            "http_method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time_ms": process_time_ms,
            "client_ip_hash": ip_hash,
            "user_agent_hash": ua_hash
        }
    )
    
    return response

# Manejador Global de Errores No Controlados (Evita leak de Stack Trace - HTTP 500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "N/A")
    logger.error(f"Error interno no controlado: {str(exc)}", extra={"request_id": req_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "Ha ocurrido un error interno en el servidor. Por favor reintente más tarde.",
            "request_id": req_id
        }
    )

# Manejador Personalizado de Errores de Validación (HTTP 422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", "N/A")
    errors = []
    for err in exc.errors():
        field_name = ".".join([str(loc) for loc in err["loc"] if loc != "body"])
        errors.append({"field": field_name, "message": err["msg"]})
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "INVALID_PAYLOAD",
            "message": "Uno o más campos de la petición no cumplen con el formato requerido.",
            "errors": errors,
            "request_id": req_id
        }
    )

def sanitize_input(text: str) -> str:
    """Normaliza texto eliminando caracteres invisibles y aplicando forma NFKC."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    return normalized.strip()

@app.get("/health", tags=["Health"])
async def health_check():
    """Endpoint público de salud para monitorización y balanceadores de carga."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }

@app.post(
    f"{settings.API_V1_STR}/rfc/validate-syntax",
    response_model=SyntaxValidationResponse,
    tags=["RFC Validation"],
    summary="Validación sintáctica y dígito verificador"
)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def validate_rfc_syntax(
    request: Request,
    body: RFCValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Valida la sintaxis (REGEX), el dígito verificador (Módulo 11) y extrae metadatos.
    **Sin llamadas externas, 100% offline.**
    """
    rfc_clean = clean_rfc(sanitize_input(body.rfc))
    is_syntax_valid = check_syntax_format(rfc_clean)
    is_checksum_valid = verify_checksum(rfc_clean)
    metadata = extract_metadata(rfc_clean)
    
    if is_syntax_valid and is_checksum_valid:
        msg = "Estructura y dígito verificador de RFC válidos."
    elif is_syntax_valid and not is_checksum_valid:
        msg = "Estructura de RFC válida pero el dígito verificador es incorrecto."
    else:
        msg = "Estructura de RFC inválida."

    return SyntaxValidationResponse(
        rfc=rfc_clean,
        is_valid_syntax=is_syntax_valid,
        is_checksum_valid=is_checksum_valid,
        person_type=metadata["person_type"],
        estimated_date=metadata["estimated_date"],
        is_valid_date=metadata["is_valid_date"],
        status_message=msg
    )

@app.post(
    f"{settings.API_V1_STR}/rfc/verify-match",
    response_model=LiveVerificationResponse,
    tags=["RFC Match & Verification"],
    summary="Cotejo de coincidencia con registros del SAT"
)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def verify_rfc_match(
    request: Request,
    body: RFCMatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Realiza la verificación en vivo del RFC y coteja opcionalmente el **Nombre/Razón Social** 
    y **Código Postal** (Trinomio CFDI 4.0).
    """
    clean_r = clean_rfc(sanitize_input(body.rfc))
    clean_nombre = sanitize_input(body.nombre_o_razon_social) if body.nombre_o_razon_social else None
    clean_cp = sanitize_input(body.codigo_postal) if body.codigo_postal else None
    
    result = await verify_rfc_live_sat(
        rfc=clean_r,
        nombre_o_razon_social=clean_nombre,
        codigo_postal=clean_cp
    )
    return LiveVerificationResponse(**result)

@app.post(
    f"{settings.API_V1_STR}/rfc/verify-sat-live",
    response_model=SATLiveVerificationResponse,
    tags=["SAT Live Query"],
    summary="Consulta en vivo al Padrón del SAT (Servicio Web SOAP)"
)
@limiter.limit(settings.RATE_LIMIT_LIVE_SAT)
async def verify_rfc_sat_live(
    request: Request,
    body: RFCValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Verifica la existencia real del RFC en la base de datos oficial del SAT mediante su **Servicio Web SOAP (ValidadorRFC)**.
    
    - **Short-Circuit:** Si el RFC es matemáticamente inválido, no consulta al SAT (`sat_service_status: "SKIPPED"`).
    - **Fallback Controlado:** Si el servidor del SAT está caído, fuera de servicio o bloqueado, la API responderá con `exists_in_sat: null` y `sat_service_status: "UNAVAILABLE"` o `"TIMEOUT"`, garantizando la disponibilidad de tu sistema.
    """
    clean_r = clean_rfc(sanitize_input(body.rfc))
    result = await verify_rfc_sat_live_service(clean_r)
    return SATLiveVerificationResponse(**result)

