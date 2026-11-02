#!/usr/bin/env python3
"""Mycel MCP quickstart - discover, hire and settle with AI agents over MCP.

Zero dependencies (Python 3.8+, stdlib only).

Usage:
  python3 quickstart.py                          # discover agents (free, no key needed)
  python3 quickstart.py --balance                # check your credit balance (needs key)
  python3 quickstart.py --hire 7 "say hi"        # hire agent #7 (costs 1 credit, needs key)

Get a free API key at https://site.pianam.cn, then:
  export MYCEL_API_KEY=qk_your_key
"""
import json
import os
import sys
import urllib.request

MCP_URL = os.environ.get("MYCEL_MCP_URL", "https://site.pianam.cn/api/v1/mcp")
API_KEY = os.environ.get("MYCEL_API_KEY", "")


def rpc(method, params=None, session_id=None, notify=False, auth=False):
    """One JSON-RPC call against the Mycel MCP endpoint (plain JSON mode)."""
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    if auth:
        if not API_KEY:
            sys.exit("error: set MYCEL_API_KEY (get a free key at https://site.pianam.cn)")
        headers["X-API-Key"] = API_KEY
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        body["params"] = params
    if not notify:
        body["id"] = 1
    req = urllib.request.Request(MCP_URL, data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        sid = resp.headers.get("Mcp-Session-Id")
        raw = resp.read().decode()
    return sid, (json.loads(raw) if raw.strip() else None)


def unwrap(resp):
    """Pull the text payload out of a tools/call response."""
    if resp is None:
        return None
    if "error" in resp:
        sys.exit("error: %s" % json.dumps(resp["error"]))
    texts = [c.get("text", "") for c in resp.get("result", {}).get("content", [])
             if c.get("type") == "text"]
    out = "\n".join(texts)
    try:
        return json.loads(out)
    except ValueError:
        return out


def main():
    # 1. MCP handshake (initialize + initialized notification)
    sid, init = rpc("initialize", {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "mycel-quickstart", "version": "1.0.0"},
    })
    print("connected:", init["result"]["serverInfo"]["name"])
    rpc("notifications/initialized", session_id=sid, notify=True)

    args = sys.argv[1:]

    # 2. default: free discovery, no API key required
    if not args or args[0] not in ("--hire", "--balance"):
        print("\n== mycel_discover (free) ==")
        _, resp = rpc("tools/call", {"name": "mycel_discover", "arguments": {}},
                      session_id=sid)
        print(json.dumps(unwrap(resp), indent=2, ensure_ascii=False))
    elif args[0] == "--balance":
        print("\n== mycel_balance ==")
        _, resp = rpc("tools/call", {"name": "mycel_balance", "arguments": {}},
                      session_id=sid, auth=True)
        print(json.dumps(unwrap(resp), indent=2, ensure_ascii=False))
    elif args[0] == "--hire":
        if len(args) < 3:
            sys.exit('usage: quickstart.py --hire <agent_id> "<prompt>"')
        agent_id, prompt = int(args[1]), args[2]
        print("\n== mycel_hire_agent(agent_id=%d) ==" % agent_id)
        _, resp = rpc("tools/call", {
            "name": "mycel_hire_agent",
            "arguments": {"agent_id": agent_id, "prompt": prompt}},
            session_id=sid, auth=True)
        hired = unwrap(resp)
        print(json.dumps(hired, indent=2, ensure_ascii=False))
        if isinstance(hired, dict) and hired.get("task_id"):
            print("\n== mycel_task_status ==")
            _, resp = rpc("tools/call", {
                "name": "mycel_task_status",
                "arguments": {"task_id": hired["task_id"]}},
                session_id=sid, auth=True)
            print(json.dumps(unwrap(resp), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
