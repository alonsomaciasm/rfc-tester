from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verifica que la petición incluya un Header X-API-Key válido.
    Soporta múltiples claves activas separadas por coma para rotación segura.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Falta el encabezado de autenticación requerido '{settings.API_KEY_NAME}'"
        )
    
    valid_keys = [k.strip() for k in settings.DEFAULT_API_KEY.split(",") if k.strip()]
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida o no autorizada"
        )
    
    return api_key
