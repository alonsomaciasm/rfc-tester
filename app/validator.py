import re
from datetime import datetime
from typing import Optional, Dict, Any

# Expresiones regulares oficiales del SAT
RFC_PHYSICAL_REGEX = re.compile(r"^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$", re.IGNORECASE)
RFC_MORAL_REGEX = re.compile(r"^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$", re.IGNORECASE)

# Tabla de valores para el dígito verificador del SAT
SAT_CHAR_DICT = {
    '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
    'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15, 'G': 16, 'H': 17, 'I': 18, 'J': 19,
    'K': 20, 'L': 21, 'M': 22, 'N': 23, '&': 24, 'O': 25, 'P': 26, 'Q': 27, 'R': 28, 'S': 29,
    'T': 30, 'U': 31, 'V': 32, 'W': 33, 'X': 34, 'Y': 35, 'Z': 36, 'Ñ': 37, ' ': 37
}

def clean_rfc(rfc: str) -> str:
    """Limpia y normaliza la cadena del RFC (mayúsculas, sin espacios externos)."""
    return rfc.strip().upper() if rfc else ""

def get_person_type(rfc: str) -> str:
    """Determina si es Persona Física (13 carats) o Persona Moral (12 carats)."""
    rfc_clean = clean_rfc(rfc)
    if len(rfc_clean) == 13:
        return "FISICA"
    elif len(rfc_clean) == 12:
        return "MORAL"
    return "UNKNOWN"

def check_syntax_format(rfc: str) -> bool:
    """Valida la sintaxis del RFC contra las expresiones regulares oficiales."""
    rfc_clean = clean_rfc(rfc)
    person_type = get_person_type(rfc_clean)
    if person_type == "FISICA":
        return bool(RFC_PHYSICAL_REGEX.match(rfc_clean))
    elif person_type == "MORAL":
        return bool(RFC_MORAL_REGEX.match(rfc_clean))
    return False

def calculate_checksum_digit(rfc: str) -> str:
    """
    Calcula el dígito verificador oficial del SAT usando el algoritmo Módulo 11.
    """
    rfc_clean = clean_rfc(rfc)
    
    # Si es moral (12 caracteres), se antepone un espacio para igualar la longitud a 13
    if len(rfc_clean) == 12:
        rfc_padded = " " + rfc_clean
    else:
        rfc_padded = rfc_clean

    # Tomar los primeros 12 caracteres (excluyendo el dígito verificador original)
    chars_to_calc = rfc_padded[:12]
    
    sum_val = 0
    for i, char in enumerate(chars_to_calc):
        factor = 13 - i
        char_code = SAT_CHAR_DICT.get(char, 0)
        sum_val += char_code * factor

    mod_val = sum_val % 11
    
    if mod_val == 0:
        return "0"
    elif mod_val == 1:
        return "A"
    else:
        return str(11 - mod_val)

def verify_checksum(rfc: str) -> bool:
    """Verifica si el último carácter del RFC coincide con el dígito verificador calculado."""
    rfc_clean = clean_rfc(rfc)
    if not check_syntax_format(rfc_clean):
        return False
    
    expected_digit = calculate_checksum_digit(rfc_clean)
    actual_digit = rfc_clean[-1]
    return expected_digit == actual_digit

def extract_metadata(rfc: str) -> Dict[str, Any]:
    """Extrae metadatos implícitos (Tipo de persona y fecha de nacimiento/creación)."""
    rfc_clean = clean_rfc(rfc)
    person_type = get_person_type(rfc_clean)
    
    if not check_syntax_format(rfc_clean):
        return {
            "person_type": person_type,
            "estimated_date": None,
            "is_valid_date": False
        }
    
    # Extraer dígitos de fecha: YYMMDD
    date_str = rfc_clean[4:10] if person_type == "FISICA" else rfc_clean[3:9]
    
    year_two_digits = int(date_str[0:2])
    month = int(date_str[2:4])
    day = int(date_str[4:6])
    
    # Estimación de siglo (Si el año de 2 dígitos es > año actual % 100, asumimos siglo XX 19xx, sino 20xx)
    current_two_digit_year = datetime.now().year % 100
    century = 1900 if year_two_digits > current_two_digit_year else 2000
    full_year = century + year_two_digits
    
    is_valid_date = False
    iso_date = None
    try:
        dt = datetime(year=full_year, month=month, day=day)
        iso_date = dt.strftime("%Y-%m-%d")
        is_valid_date = True
    except ValueError:
        is_valid_date = False

    return {
        "person_type": person_type,
        "estimated_date": iso_date,
        "is_valid_date": is_valid_date
    }
