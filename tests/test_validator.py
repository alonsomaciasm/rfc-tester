import pytest
from app.validator import check_syntax_format, verify_checksum, calculate_checksum_digit, extract_metadata

def test_physical_rfc_validation():
    assert check_syntax_format("XAXX010101000") == True

def test_moral_rfc_validation():
    assert check_syntax_format("NSE011210267") == True
    assert check_syntax_format("ABC990101AB1") == True

def test_invalid_rfc_syntax():
    assert check_syntax_format("INVALID_RFC_123") == False
    assert check_syntax_format("123456789012") == False

def test_metadata_extraction():
    meta = extract_metadata("XAXX010101000")
    assert meta["person_type"] == "FISICA"
    assert meta["estimated_date"] == "2001-01-01"
    assert meta["is_valid_date"] == True
