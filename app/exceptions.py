from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.logger import logger


class APIProblemException(HTTPException):
    """
    Excepción base compatible con RFC 7807 (Problem Details for HTTP APIs).
    """

    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        type_uri: str = "about:blank",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.title = title
        self.type_uri = type_uri
        self.extra = extra or {}


async def rfc7807_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    req_id = getattr(request.state, "request_id", "N/A")
    ip_hash = getattr(request.state, "client_ip_hash", "unknown")

    if isinstance(exc, APIProblemException):
        problem = {
            "type": exc.type_uri,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
            "request_id": req_id,
        }
        if exc.extra:
            problem.update(exc.extra)

        logger.warning(
            f"RFC Problem {exc.status_code} en {request.url.path}: {exc.detail}",
            extra={"request_id": req_id, "status_code": exc.status_code, "client_ip_hash": ip_hash}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem,
            media_type="application/problem+json",
        )

    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        problem = {
            "type": "about:blank",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": str(exc.detail),
            "instance": request.url.path,
            "request_id": req_id,
        }
        logger.warning(
            f"HTTP Exception {exc.status_code} en {request.url.path}: {exc.detail}",
            extra={"request_id": req_id, "status_code": exc.status_code, "client_ip_hash": ip_hash}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=problem,
            media_type="application/problem+json",
        )

    # Error 500 no controlado
    logger.error(
        f"Error interno no controlado: {str(exc)}",
        extra={"request_id": req_id, "status_code": 500, "client_ip_hash": ip_hash}
    )

    problem = {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": "Ha ocurrido un error interno en el servidor. Por favor contacte al administrador.",
        "instance": request.url.path,
        "request_id": req_id,
    }
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=problem,
        media_type="application/problem+json",
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    req_id = getattr(request.state, "request_id", "N/A")
    ip_hash = getattr(request.state, "client_ip_hash", "unknown")
    formatted_errors = []
    for err in exc.errors():
        formatted_errors.append({
            "field": ".".join([str(loc) for loc in err.get("loc", []) if loc != "body"]),
            "message": err.get("msg"),
            "type": err.get("type"),
        })

    problem = {
        "type": "about:blank",
        "title": "Unprocessable Entity (Validation Error)",
        "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": "Uno o más campos de la petición no cumplen con las validaciones de esquema requeridas.",
        "instance": request.url.path,
        "invalid_params": formatted_errors,
        "request_id": req_id,
    }

    logger.warning(
        f"Error de validación en {request.url.path}",
        extra={"request_id": req_id, "status_code": 422, "client_ip_hash": ip_hash}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=problem,
        media_type="application/problem+json",
    )

