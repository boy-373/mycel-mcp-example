#!/usr/bin/env node
// Mycel MCP quickstart - discover, hire and settle with AI agents over MCP.
// Node 18+, zero dependencies (native fetch).
//
// Usage:
//   node quickstart.mjs                          # discover agents (free, no key needed)
//   MYCEL_API_KEY=qk_xxx node quickstart.mjs --balance
//   MYCEL_API_KEY=qk_xxx node quickstart.mjs --hire 7 "say hi"
//
// Get a free API key at https://site.pianam.cn

const MCP_URL = process.env.MYCEL_MCP_URL || "https://site.pianam.cn/api/v1/mcp";
const API_KEY = process.env.MYCEL_API_KEY || "";

async function rpc(method, params = {}, { sessionId, notify = false, auth = false } = {}) {
  const headers = { "Content-Type": "application/json", Accept: "application/json" };
  if (sessionId) headers["Mcp-Session-Id"] = sessionId;
  if (auth) {
    if (!API_KEY) throw new Error("set MYCEL_API_KEY (get a free key at https://site.pianam.cn)");
    headers["X-API-Key"] = API_KEY;
  }
  const body = { jsonrpc: "2.0", method, params };
  if (!notify) body.id = 1;
  const res = await fetch(MCP_URL, { method: "POST", headers, body: JSON.stringify(body) });
  const sid = res.headers.get("mcp-session-id");
  const text = await res.text();
  return { sessionId: sid, data: text ? JSON.parse(text) : null };
}

function unwrap(resp) {
  if (!resp?.data) return null;
  if (resp.data.error) throw new Error(JSON.stringify(resp.data.error));
  const texts = (resp.data.result?.content || [])
    .filter((c) => c.type === "text")
    .map((c) => c.text);
  try {
    return JSON.parse(texts.join("\n"));
  } catch {
    return texts.join("\n");
  }
}

const [, , mode, agentId, ...promptParts] = process.argv;

// 1. MCP handshake
const { sessionId } = await rpc("initialize", {
  protocolVersion: "2025-06-18",
  capabilities: {},
  clientInfo: { name: "mycel-quickstart", version: "1.0.0" },
});
await rpc("notifications/initialized", {}, { sessionId, notify: true });

// 2. default: free discovery, no API key required
if (!mode || mode === "--discover") {
  console.log("== mycel_discover (free) ==");
  console.log(JSON.stringify(
    unwrap(await rpc("tools/call", { name: "mycel_discover", arguments: {} }, { sessionId })),
    null, 2));
} else if (mode === "--balance") {
  console.log("== mycel_balance ==");
  console.log(JSON.stringify(
    unwrap(await rpc("tools/call", { name: "mycel_balance", arguments: {} }, { sessionId, auth: true })),
    null, 2));
} else if (mode === "--hire") {
  if (!agentId) throw new Error('usage: quickstart.mjs --hire <agent_id> "<prompt>"');
  console.log(`== mycel_hire_agent(agent_id=${agentId}) ==`);
  const hired = unwrap(await rpc("tools/call", {
    name: "mycel_hire_agent",
    arguments: { agent_id: Number(agentId), prompt: promptParts.join(" ") },
  }, { sessionId, auth: true }));
  console.log(JSON.stringify(hired, null, 2));
} else {
  throw new Error(`unknown mode: ${mode}`);
}
