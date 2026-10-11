# DeFiLlama Free MCP Starter

A read-only MCP server that wraps DeFiLlama's public REST API. No API key is used.

## Tools
- `search_protocols(query, limit=10)` — compact search results from `/protocols`.
- `get_protocol_tvl(protocol)` — current TVL, chain breakdown, recent historical values.
- `get_protocol_fees_revenue(protocol)` — fees/revenue summary where reported.
- `get_dex_volume(protocol)` — DEX volume summary where available.
- `get_chain_tvl(limit=15)` — largest chains by current TVL.

## Deploy to Render
1. On a computer, sign in to GitHub and create a repository named `defillama-mcp-free`.
2. Upload all files in this folder, keeping the `tests` folder.
3. Sign in to Render, select **New → Blueprint**, and connect that repository.
4. Review and deploy the service detected from `render.yaml`.
5. Copy the HTTPS service URL Render gives you. Your MCP endpoint is that URL plus `/mcp`.
6. Free services may sleep after inactivity, so the first request can be slow. Availability and pricing may change.

## Test the MCP server
On a computer with Node.js LTS, run:

```bash
npx @modelcontextprotocol/inspector
```

Use Streamable HTTP, paste your deployed endpoint ending in `/mcp`, connect, then call `search_protocols` with `aave` and `get_protocol_tvl` with `aave`.

## Test upstream public API endpoints
With Python 3.11+ and internet access:

```bash
python -m unittest discover -s tests -v
```

These tests check DeFiLlama directly, not the deployed server. They can fail due to connectivity, rate limits, or upstream outages.

## ChatGPT limitation
Do not assume a personal Free account can attach a custom remote MCP app. OpenAI's custom MCP connection options depend on plan, workspace permissions, and web UI availability. If your account does not show the relevant custom app/developer-mode controls on ChatGPT web, this server can still be tested using MCP Inspector, but cannot be attached through that account's current UI.

## Security / accuracy
- The upstream host is fixed to `https://api.llama.fi`; tool inputs cannot supply arbitrary URLs.
- No API credentials are stored and all tools are read-only.
- Missing fee/revenue fields do not mean zero. TVL, fees, revenue and volume are different metrics.
- Free API rate limits and uptime are controlled by DeFiLlama.
