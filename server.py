import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "https://api.llama.fi"
TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
mcp = FastMCP(
    "DeFiLlama Free Data",
    instructions="Read-only tools for public DeFiLlama API data. No API key is used. Missing data is not zero and outputs are not investment advice.",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)

def get_json(path: str) -> Any:
    # Fixed upstream host: inputs cannot select arbitrary URLs.
    with httpx.Client(timeout=TIMEOUT, follow_redirects=False) as client:
        r = client.get(BASE_URL + path, headers={"accept": "application/json", "user-agent": "defillama-mcp-starter/1.0"})
        r.raise_for_status()
        return r.json()

def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None

@mcp.tool()
def search_protocols(query: str, limit: int = 10) -> dict:
    """Search public DeFiLlama protocol data by name, symbol, category, or chain. Example query='aave'."""
    q = query.strip().lower()
    if not q:
        return {"error": "query must not be empty"}
    limit = max(1, min(int(limit), 25))
    data = get_json("/protocols")
    out = []
    for p in data:
        haystack = " ".join([str(p.get("name", "")), str(p.get("symbol", "")), str(p.get("category", "")), " ".join(p.get("chains") or [])]).lower()
        if q in haystack:
            out.append({"name": p.get("name"), "slug": p.get("slug"), "symbol": p.get("symbol"), "category": p.get("category"), "chains": (p.get("chains") or [])[:12], "tvl_usd": num(p.get("tvl")), "change_1d_pct": num(p.get("change_1d")), "change_7d_pct": num(p.get("change_7d")), "url": p.get("url")})
            if len(out) >= limit:
                break
    return {"query": query, "count": len(out), "results": out, "source": BASE_URL + "/protocols"}

@mcp.tool()
def get_protocol_tvl(protocol: str) -> dict:
    """Get current TVL and a short historical TVL series for a protocol slug, e.g. aave or uniswap."""
    slug = protocol.strip().lower()
    if not slug or "/" in slug or ".." in slug:
        return {"error": "Provide a protocol slug such as 'aave' or 'uniswap'."}
    current = get_json("/tvl/" + slug)
    details = get_json("/protocol/" + slug)
    series = details.get("tvl", []) if isinstance(details, dict) else []
    history = []
    for item in series[-8:] if isinstance(series, list) else []:
        if isinstance(item, dict):
            history.append({"date": item.get("date"), "tvl_usd": item.get("totalLiquidityUSD", item.get("tvl"))})
    chains = details.get("currentChainTvls", {}) if isinstance(details, dict) else {}
    chain_rows = sorted([(k, v) for k, v in chains.items() if isinstance(v, (int, float))], key=lambda x: x[1], reverse=True)[:12] if isinstance(chains, dict) else []
    return {"protocol": details.get("name", slug) if isinstance(details, dict) else slug, "slug": slug, "current_tvl_usd": num(current), "chains": dict(chain_rows), "recent_tvl_history": history, "source_current": f"{BASE_URL}/tvl/{slug}", "source_history": f"{BASE_URL}/protocol/{slug}"}

@mcp.tool()
def get_protocol_fees_revenue(protocol: str) -> dict:
    """Get public fees/revenue summary for a protocol slug where available; missing fields do not mean zero."""
    slug = protocol.strip().lower()
    if not slug or "/" in slug or ".." in slug:
        return {"error": "Provide a protocol slug such as 'aave' or 'uniswap'."}
    data = get_json("/summary/fees/" + slug)
    if not isinstance(data, dict):
        return {"protocol": slug, "data": data, "source": f"{BASE_URL}/summary/fees/{slug}"}
    keys = ["name", "displayName", "category", "chains", "total24h", "total48hto24h", "total7d", "total30d", "total1y", "totalAllTime", "totalDataChart", "totalDataChartBreakdown", "dailyRevenue", "dailyUserFees", "dailySupplySideRevenue", "revenue24h", "revenue7d", "revenue30d", "revenue1y", "revenueAllTime", "methodology", "url"]
    out = {k: data[k] for k in keys if k in data}
    for k in ("totalDataChart", "totalDataChartBreakdown"):
        if isinstance(out.get(k), list): out[k] = out[k][-8:]
    out.update({"slug": slug, "source": f"{BASE_URL}/summary/fees/{slug}", "note": "Fees are paid by users; revenue is the portion retained by the protocol where reported."})
    return out

@mcp.tool()
def get_dex_volume(protocol: str) -> dict:
    """Get public DEX volume summary for a protocol slug, e.g. uniswap, where available."""
    slug = protocol.strip().lower()
    if not slug or "/" in slug or ".." in slug:
        return {"error": "Provide a protocol slug such as 'uniswap'."}
    data = get_json("/summary/dexs/" + slug)
    if not isinstance(data, dict):
        return {"protocol": slug, "data": data, "source": f"{BASE_URL}/summary/dexs/{slug}"}
    keys = ["name", "displayName", "category", "chains", "total24h", "total48hto24h", "total7d", "total30d", "total1y", "totalAllTime", "totalDataChart", "totalDataChartBreakdown", "methodology", "url"]
    out = {k: data[k] for k in keys if k in data}
    for k in ("totalDataChart", "totalDataChartBreakdown"):
        if isinstance(out.get(k), list): out[k] = out[k][-8:]
    out.update({"slug": slug, "source": f"{BASE_URL}/summary/dexs/{slug}"})
    return out

@mcp.tool()
def get_chain_tvl(limit: int = 15) -> dict:
    """List leading chains by current TVL from the public DeFiLlama API."""
    limit = max(1, min(int(limit), 30))
    data = get_json("/v2/chains")
    rows = [{"chain": c.get("name"), "tvl_usd": num(c.get("tvl")), "token_symbol": c.get("tokenSymbol"), "chain_id": c.get("chainId")} for c in data]
    rows.sort(key=lambda x: x["tvl_usd"] or 0, reverse=True)
    return {"count_returned": min(limit, len(rows)), "chains": rows[:limit], "source": BASE_URL + "/v2/chains"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
