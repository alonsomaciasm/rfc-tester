"""
Model Context Protocol (MCP) Server para la API de RFC de México (SAT).
Permite a Agentes de Inteligencia Artificial (Gemini, Claude, OpenAI, Antigravity)
validar sintaxis de RFC, verificar algoritmo de dígito verificador y consultar listas SAT
reduciendo drásticamente el consumo de tokens en comparación con inyectar reglas complejas en el prompt.
"""

import json
import unicodedata
from typing import Any, Callable

from app.validator import (
    check_syntax_format,
    verify_checksum,
    extract_metadata,
    clean_rfc,
)
from app.sat_service import verify_rfc_sat_live_service, verify_rfc_live_sat


class FastMCPServer:
    """Servidor ligero JSON-RPC 2.0 compatible con Model Context Protocol (MCP)."""

    def __init__(self, name: str = "RFC-Tester-MCP-Server") -> None:
        self.name = name
        self.tools: dict[str, dict[str, Any]] = {}

    def tool(self, description: str = "") -> Callable:
        def decorator(func: Callable) -> Callable:
            tool_name = func.__name__
            self.tools[tool_name] = {
                "name": tool_name,
                "description": description or func.__doc__ or "",
                "handler": func,
            }
            return func
        return decorator

    async def call_tool(self, tool_name: str, **kwargs: Any) -> str:
        if tool_name not in self.tools:
            return json.dumps({"error": f"Tool '{tool_name}' no encontrada."})
        handler = self.tools[tool_name]["handler"]
        return await handler(**kwargs)

    async def handle_jsonrpc_request(self, request_json: str) -> str:
        """Procesa solicitudes entrantes JSON-RPC 2.0 de Agentes de IA."""
        try:
            req = json.loads(request_json)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                tool_list = [
                    {"name": t["name"], "description": t["description"]}
                    for t in self.tools.values()
                ]
                return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tool_list}})

            if method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result_content = await self.call_tool(tool_name, **tool_args)
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": result_content}]},
                })

            return json.dumps({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})
        except Exception as e:
            return json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}})


mcp = FastMCPServer()


@mcp.tool(description="Valida la estructura sintáctica de un RFC (física o moral) y su dígito verificador matemático oficial (Módulo 11 del SAT).")
async def validar_sintaxis_rfc(rfc: str) -> str:
    """Valida sintaxis, dígito verificador y extrae tipo de persona y fecha estimada."""
    cleaned = clean_rfc(rfc.strip().upper())
    is_valid_format = check_syntax_format(cleaned)
    is_checksum_valid = verify_checksum(cleaned)
    meta = extract_metadata(cleaned)

    return json.dumps({
        "rfc": cleaned,
        "is_valid_syntax": is_valid_format,
        "is_checksum_valid": is_checksum_valid,
        "person_type": meta.get("person_type"),
        "estimated_date": meta.get("estimated_date"),
        "is_valid_date": meta.get("is_valid_date"),
        "status": "VALID" if (is_valid_format and is_checksum_valid) else "INVALID"
    }, separators=(",", ":"))


@mcp.tool(description="Coteja un RFC junto a la Razón Social y Código Postal para validación de Trinomio Fiscal CFDI 4.0.")
async def cotejar_trinomio_fiscal(rfc: str, nombre_o_razon_social: str = "", codigo_postal: str = "") -> str:
    """Valida consistencia entre RFC, Nombre y Código Postal del contribuyente."""
    cleaned = clean_rfc(rfc.strip().upper())
    res = await verify_rfc_live_sat(
        rfc=cleaned,
        nombre_o_razon_social=nombre_o_razon_social.strip() if nombre_o_razon_social else None,
        codigo_postal=codigo_postal.strip() if codigo_postal else None
    )
    return json.dumps(res, separators=(",", ":"))


@mcp.tool(description="Consulta en vivo al servicio SOAP del SAT para verificar si el RFC se encuentra registrado en el padrón oficial.")
async def consultar_rfc_sat_live(rfc: str) -> str:
    """Verifica la existencia real del RFC en la base oficial del SAT."""
    cleaned = clean_rfc(rfc.strip().upper())
    res = await verify_rfc_sat_live_service(cleaned)
    return json.dumps(res, separators=(",", ":"))


if __name__ == "__main__":
    print(f"⚡ Servidor FastMCP '{mcp.name}' activo para herramientas de IA (stdio/JSON-RPC 2.0)...")

