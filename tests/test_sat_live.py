import pytest
from unittest.mock import patch, AsyncMock
import httpx
from app.sat_service import verify_rfc_sat_live_service

@pytest.mark.anyio
async def test_sat_live_invalid_structure_skipped():
    # RFC inválido debe hacer short-circuit y no llamar al SAT
    result = await verify_rfc_sat_live_service("INVALID123")
    assert result["is_structurally_valid"] is False
    assert result["exists_in_sat"] is False
    assert result["sat_service_status"] == "SKIPPED"

@pytest.mark.anyio
async def test_sat_live_valid_rfc_online_exists():
    mock_xml_response = """<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
       <soap:Body>
          <ConsultaRFCResponse xmlns="http://respuesta.validador.sat.gob.mx">
             <ConsultaRFCResult>
                <esValido>true</esValido>
                <codigo>1</codigo>
                <mensaje>RFC Válido</mensaje>
             </ConsultaRFCResult>
          </ConsultaRFCResponse>
       </soap:Body>
    </soap:Envelope>"""

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200, text=mock_xml_response)
        
        result = await verify_rfc_sat_live_service("XAXX010101004")
        assert result["is_structurally_valid"] is True
        assert result["exists_in_sat"] is True
        assert result["sat_service_status"] == "ONLINE"

@pytest.mark.anyio
async def test_sat_live_valid_rfc_online_not_exists():
    mock_xml_response = """<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
       <soap:Body>
          <ConsultaRFCResponse xmlns="http://respuesta.validador.sat.gob.mx">
             <ConsultaRFCResult>
                <esValido>false</esValido>
                <codigo>0</codigo>
                <mensaje>RFC No Registrado</mensaje>
             </ConsultaRFCResult>
          </ConsultaRFCResponse>
       </soap:Body>
    </soap:Envelope>"""

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200, text=mock_xml_response)
        
        result = await verify_rfc_sat_live_service("XAXX010101004")
        assert result["is_structurally_valid"] is True
        assert result["exists_in_sat"] is False
        assert result["sat_service_status"] == "ONLINE"

@pytest.mark.anyio
async def test_sat_live_timeout_fallback():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout error")
        
        result = await verify_rfc_sat_live_service("XAXX010101004")
        assert result["is_structurally_valid"] is True
        assert result["exists_in_sat"] is None
        assert result["sat_service_status"] == "TIMEOUT"

@pytest.mark.anyio
async def test_sat_live_service_unavailable_fallback():
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(503, text="Service Unavailable")
        
        result = await verify_rfc_sat_live_service("XAXX010101004")
        assert result["is_structurally_valid"] is True
        assert result["exists_in_sat"] is None
        assert result["sat_service_status"] == "UNAVAILABLE"

@pytest.mark.anyio
async def test_sat_live_xml_escaping_ampersand():
    from app.sat_service import query_sat_soap_service
    mock_xml_response = "<esValido>true</esValido>"
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = httpx.Response(200, text=mock_xml_response)
        
        await query_sat_soap_service("G&M920415XYZ")
        
        # Verificar que en el contenido post enviado al SAT el ampersand esté escapado como &amp;
        assert mock_post.called
        kwargs = mock_post.call_args.kwargs
        assert "&amp;" in kwargs["content"]


