"""MCP server (stdio, JSON-RPC 2.0). Python standard library only, no network.

Start: python -m zenginname.server
"""
import json
import sys

from . import __version__
from .name import DEFAULT_MAX, check_name, format_name, match_names

PROTOCOLS = ["2025-06-18", "2025-03-26", "2024-11-05"]
RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}

TOOLS = [
    {
        "name": "zengin_name_format",
        "title": "Format a Japanese bank-transfer account name (振込名義カナ)",
        "annotations": RO,
        "description": ("Turn a payee or payer name into the form Japanese banks accept in transfers (Zengin): half-width "
                        "katakana, digits, A-Z and a few symbols; small kana made large (ッ->ﾂ, ャ->ﾔ), ー->-, ・->., "
                        "legal-entity words replaced by the bank abbreviation with the position rule "
                        "(株式会社 at the start 'ｶ)', in the middle '(ｶ)', at the end '(ｶ'). Accepts kana (hiragana or "
                        "katakana, full or half width), Latin letters and digits, and legal-entity words in kanji or "
                        "spelled out (カブシキガイシャ). It does NOT read other kanji: pass the reading. Returns ok, zengin "
                        "(half-width), display (full-width), length (voiced kana count 2), entities, changes, errors, "
                        "warnings (code, message in English and Japanese). 振込名義を全銀の形に整える。"),
        "inputSchema": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Name as kana reading, e.g. '株式会社 ニッポンショウジ'"},
            "max_length": {"type": "integer", "description": f"Warn above this many half-width chars (default {DEFAULT_MAX}, 0 = off)"}},
            "required": ["name"]},
    },
    {
        "name": "zengin_name_check",
        "title": "Check an already formatted half-width transfer name",
        "annotations": RO,
        "description": ("Validate a half-width Zengin name from a CSV or bank file: only allowed characters, no small kana, "
                        "no full-width characters, spacing, length. Returns ok, length, errors, warnings, abbreviations found."),
        "inputSchema": {"type": "object", "properties": {
            "name": {"type": "string"}, "max_length": {"type": "integer"}}, "required": ["name"]},
    },
    {
        "name": "zengin_name_match",
        "title": "Compare two names for payment reconciliation (入金消込)",
        "annotations": RO,
        "description": ("Decide whether a payer name on a bank statement (half-width, abbreviated) and a customer name "
                        "(kana reading) are the same, ignoring entity abbreviations, spaces, punctuation, small/large kana "
                        "and width. Returns match, name_match, key_a, key_b, entity_a, entity_b, entity_type_differs "
                        "(e.g. ﾕ) vs 株式会社), errors."),
        "inputSchema": {"type": "object", "properties": {
            "a": {"type": "string"}, "b": {"type": "string"}}, "required": ["a", "b"]},
    },
]


def _str(args, key):
    v = args.get(key)
    if not isinstance(v, str):
        raise ValueError(f"'{key}' must be a string")
    return v


def _max(args):
    v = args.get("max_length", DEFAULT_MAX)
    if not isinstance(v, int) or isinstance(v, bool) or v < 0:
        raise ValueError("'max_length' must be a non-negative integer")
    return v


HANDLERS = {
    "zengin_name_format": lambda a: format_name(_str(a, "name"), _max(a)),
    "zengin_name_check": lambda a: check_name(_str(a, "name"), _max(a)),
    "zengin_name_match": lambda a: match_names(_str(a, "a"), _str(a, "b")),
}


def _handle_legacy(msg):
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if mid is None:
        return None
    try:
        if method == "initialize":
            want = params.get("protocolVersion")
            result = {"protocolVersion": want if want in PROTOCOLS else PROTOCOLS[0],
                      "capabilities": {"tools": {"listChanged": False}},
                      "serverInfo": {"name": "jp-zengin-name", "version": __version__},
                      "instructions": ("Before writing a Japanese bank transfer (総合振込 CSV, payroll, refunds), pass each "
                                       "name through zengin_name_format with its kana reading. Do not guess kanji readings.")}
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            name = params.get("name")
            if name not in HANDLERS:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"Unknown tool: {name}"}}
            try:
                out = HANDLERS[name](params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False)}],
                          "structuredContent": out, "isError": False}
            except ValueError as e:
                result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    except Exception as e:  # keep the server alive
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": f"Internal error: {e}"}}


# --- MCP 2026-07-28 (stateless) support. The legacy initialize flow above stays as it was. ---
# Spec: https://modelcontextprotocol.io/specification/2026-07-28/changelog
MODERN_PROTOCOLS = ["2026-07-28"]
_K = "io.modelcontextprotocol/"
_TOOLS_TTL_MS = 300000


def _legacy_info():
    r = _handle_legacy({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}})["result"]
    return r["serverInfo"], r.get("instructions"), {k: {} for k in r.get("capabilities", {})}


def _modern_error(mid, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": mid, "error": err}


def _handle_modern(msg):
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:
        return None
    params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
    meta = params.get("_meta") if isinstance(params.get("_meta"), dict) else {}
    version = meta.get(_K + "protocolVersion")
    if not isinstance(version, str):
        return _modern_error(mid, -32602, "Missing _meta io.modelcontextprotocol/protocolVersion")
    if version not in MODERN_PROTOCOLS:
        return _modern_error(mid, -32022, "Unsupported protocol version",
                             {"supported": MODERN_PROTOCOLS + PROTOCOLS, "requested": version})
    if not isinstance(meta.get(_K + "clientCapabilities"), dict):
        return _modern_error(mid, -32602, "Missing _meta io.modelcontextprotocol/clientCapabilities")
    server_info, instructions, caps = _legacy_info()
    if method == "server/discover":
        result = {"resultType": "complete", "supportedVersions": list(MODERN_PROTOCOLS), "capabilities": caps,
                  "_meta": {_K + "serverInfo": server_info}, "ttlMs": 3600000, "cacheScope": "public"}
        if instructions:
            result["instructions"] = instructions
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method not in ("tools/list", "tools/call"):
        return _modern_error(mid, -32601, f"Method not found: {method}")
    resp = _handle_legacy(msg)
    if "result" in resp:
        result = dict(resp["result"])
        result["resultType"] = "complete"
        result.setdefault("_meta", {})[_K + "serverInfo"] = server_info
        if method == "tools/list":
            result["ttlMs"] = _TOOLS_TTL_MS
            result["cacheScope"] = "public"
        resp = {"jsonrpc": "2.0", "id": mid, "result": result}
    return resp


def handle(msg):
    """Dual-era: server/discover or a request with modern _meta is stateless 2026-07-28; initialize keeps the old flow."""
    params = msg.get("params")
    meta = params.get("_meta") if isinstance(params, dict) else None
    method = msg.get("method")
    if method == "server/discover" or (method != "initialize" and isinstance(meta, dict)
                                       and _K + "protocolVersion" in meta):
        return _handle_modern(msg)
    return _handle_legacy(msg)


def main():
    for s in (sys.stdin, sys.stdout):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}) + "\n")
            sys.stdout.flush()
            continue
        resp = handle(msg) if isinstance(msg, dict) else None
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
