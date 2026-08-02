import os

class Settings:
    PROJECT_NAME: str = "API Verificador de RFC SAT"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Seguridad
    API_KEY_NAME: str = "X-API-Key"
    DEFAULT_API_KEY: str = os.getenv("API_KEY", "secret-rfc-key-change-me-in-production")
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "30/minute")
    RATE_LIMIT_LIVE_SAT: str = os.getenv("RATE_LIMIT_LIVE_SAT", "15/minute")
    
    # CORS
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # SAT Endpoints Oficiales Activos (SIAT)
    SAT_CFDI_VAL_URL: str = os.getenv("SAT_CFDI_VAL_URL", "https://siat.sat.gob.mx/ValidaRFC/valida.aspx")
    SAT_SOAP_ENDPOINT: str = os.getenv("SAT_SOAP_ENDPOINT", "https://siat.sat.gob.mx/validadorRFC/ValidadorRFC")
    SAT_SOAP_TIMEOUT_SECONDS: float = float(os.getenv("SAT_SOAP_TIMEOUT_SECONDS", "2.5"))

settings = Settings()
