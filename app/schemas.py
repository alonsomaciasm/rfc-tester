from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re

class RFCValidationRequest(BaseModel):
    rfc: str = Field(..., description="RFC a validar (12 o 13 caracteres)", example="NSE011210267")

    @field_validator("rfc")

    def clean_and_check_rfc(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not (12 <= len(v_clean) <= 13):
            raise ValueError("El RFC debe tener exactamente 12 (Persona Moral) o 13 (Persona Física) caracteres.")
        return v_clean

class RFCMatchRequest(BaseModel):
    rfc: str = Field(..., description="RFC a verificar", example="NSE011210267")
    nombre_o_razon_social: Optional[str] = Field(
        None, 
        description="Nombre o Razón Social exacta sin régimen capital (ej. EMPRESA SA DE CV -> EMPRESA)",
        example="NUEVA SOLUCION EMPRESARIAL"
    )
    codigo_postal: Optional[str] = Field(
        None, 
        description="Código postal del domicilio fiscal (5 dígitos)", 
        example="06700"
    )

    @field_validator("rfc")

    def clean_rfc(cls, v: str) -> str:
        v_clean = v.strip().upper()
        if not (12 <= len(v_clean) <= 13):
            raise ValueError("El RFC debe tener exactamente 12 o 13 caracteres.")
        return v_clean

    @field_validator("codigo_postal")

    def validate_cp(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_clean = v.strip()
            if not re.match(r"^\d{5}$", v_clean):
                raise ValueError("El código postal debe contener exactamente 5 dígitos numéricos.")
            return v_clean
        return None

class SyntaxValidationResponse(BaseModel):
    rfc: str
    is_valid_syntax: bool
    is_checksum_valid: bool
    person_type: str
    estimated_date: Optional[str] = None
    is_valid_date: bool
    status_message: str

class MatchDetails(BaseModel):
    nombre_matches: Optional[bool] = None
    codigo_postal_matches: Optional[bool] = None

class LiveVerificationResponse(BaseModel):
    rfc: str
    is_valid_syntax: bool
    is_checksum_valid: bool
    is_structurally_valid: bool = Field(
        ..., 
        description="Indica si el RFC cumple estructural y matemáticamente con la especificación (Módulo 11)."
    )
    match_details: Optional[MatchDetails] = None
    overall_match: bool
    status_message: str

class SATLiveVerificationResponse(BaseModel):
    rfc: str
    is_valid_syntax: bool
    is_checksum_valid: bool
    is_structurally_valid: bool
    exists_in_sat: Optional[bool] = Field(
        None,
        description="True si el RFC está registrado en el SAT, False si no existe, null si el servicio del SAT no estuvo disponible."
    )
    sat_service_status: str = Field(
        ...,
        description="Estado del servicio del SAT: 'ONLINE', 'UNAVAILABLE', 'TIMEOUT', 'SKIPPED'."
    )
    status_message: str

