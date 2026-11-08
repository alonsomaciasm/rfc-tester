import asyncio
import json
from app.mcp_server import mcp, validar_sintaxis_rfc

def test_mcp_validar_sintaxis_rfc():
    res_str = asyncio.run(validar_sintaxis_rfc("XAXX010101000"))
    data = json.loads(res_str)
    assert data["rfc"] == "XAXX010101000"
    assert data["is_valid_syntax"] is True

def test_mcp_jsonrpc_list_and_call():
    # Test tools/list
    list_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    list_res_str = asyncio.run(mcp.handle_jsonrpc_request(list_req))
    list_res = json.loads(list_res_str)
    assert "result" in list_res
    tools = [t["name"] for t in list_res["result"]["tools"]]
    assert "validar_sintaxis_rfc" in tools
    assert "cotejar_trinomio_fiscal" in tools

    # Test tools/call
    call_req = json.dumps({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "validar_sintaxis_rfc",
            "arguments": {"rfc": "GODE561231GR8"}
        }
    })
    call_res_str = asyncio.run(mcp.handle_jsonrpc_request(call_req))
    call_res = json.loads(call_res_str)
    assert "result" in call_res
    content_text = call_res["result"]["content"][0]["text"]
    tool_data = json.loads(content_text)
    assert tool_data["rfc"] == "GODE561231GR8"

