<div align="center">
  <img src="assets/hero-banner.svg" alt="MCP LLM Pricing Intelligence" width="100%" />
  <br/><br/>
  <p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Protocol-Model%20Context%20Protocol%20%28FastMCP%29-7C3AED?style=flat-square" alt="MCP" />
    <img src="https://img.shields.io/badge/Client-Claude%20Sonnet%204.5-2563EB?style=flat-square" alt="Claude 4.5" />
    <img src="https://img.shields.io/badge/Storage-MCP%20SQLite%20%2B%20Firecrawl%20v2-0D9488?style=flat-square" alt="SQLite" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-475569?style=flat-square" alt="License" /></a>
  </p>
</div>

---

![MCP Cross-Provider LLM Pricing Intelligence Architecture](docs/images/architecture_blueprint.png)

Autonomous LLM inference pricing analyst built on the **Model Context Protocol (MCP)**—orchestrating three concurrent `stdio` JSON-RPC MCP servers (**custom FastMCP Firecrawl v2 scraper**, **SQLite persistence server**, and **Filesystem MCP server**) under a **Claude Sonnet 4.5** tool-calling client.

![MCP Cross-Provider Pricing](docs/images/mcp_cross_provider_pricing.png)

---

## 1. Multi-Server MCP Architecture

```mermaid
flowchart LR
    C["mcp_client.py<br/>(Claude Sonnet 4.5 + DataExtractor)"] <-->|"stdio JSON-RPC"| S1["mcp_server.py (FastMCP)<br/>scrape_websites + extract_scraped_info"]
    C <-->|"stdio JSON-RPC"| S2["mcp-server-sqlite<br/>test.db (pricing_plans)"]
    C <-->|"stdio JSON-RPC"| S3["server-filesystem<br/>scraped_content/"]
    S1 --> FC["Firecrawl v2 API<br/>(CloudRift, DeepInfra, Fireworks, Groq)"]
```

---

## 2. Live Execution Transcript Excerpt ([`docs/live_run_transcript.md`](docs/live_run_transcript.md))

```markdown
# PriceScout — Evidence of Working Project

This is a text transcript captured directly from a live run of `mcp_client.py`
(via `script`, so it is a verbatim terminal capture), sanitized to
remove the local machine's absolute file path. It demonstrates the three required
test prompts from the project README/instructions, run back-to-back in one session.


## Test 1 — Scraping

Command run:
```
scrape these sites: {'cloudrift': 'https://www.cloudrift.ai/inference', 'deepinfra': 'https://deepinfra.com/pricing', 'fireworks': 'https://fireworks.ai/pricing#serverless-pricing', 'groq': 'https://groq.com/pricing'}
```

```
Query: scrape these sites: {'cloudrift': 'https://www.cloudrift.ai/inference', 'deepinfra': 'https://deepinfra.com/pricing', 'fireworks': 'https://fireworks.ai/pricing#serverless-pricing', 'groq': 'https://groq.com/pricing'}
I'll scrape these websites for you to gather their pricing and inference information.
Calling tool scrape_websites with args {'websites': {'cloudrift': 'https://www.cloudrift.ai/inference', 'deepinfra': 'https://deepinfra.com/pricing', 'fireworks': 'https://fireworks.ai/pricing#serverless-pricing', 'groq': 'https://groq.com/pricing'}}
Scraping cloudrift: https://www.cloudrift.ai/inference
Scraping deepinfra: https://deepinfra.com/pricing
Scraping fireworks: https://fireworks.ai/pricing#serverless-pricing
Scraping groq: https://groq.com/pricing
Successfully scraped 4 out of 4 websites

Great! I've successfully scraped all four websites:
 V
1. **cloudrift** - https://www.cloudrift.ai/inference
2. **deepinfra** - https://deepinfra.com/pricing
3. **fireworks** - https://fireworks.ai/pricing#serverless-pricing
4. **groq** - https://groq.com/pricing

All the content has been stored and is now available for extraction and analysis.
```

## Test 2 — Asking Questions & Comparing

Command run:
```
How much does cloudrift ai (https://www.cloudrift.ai/inference) charge for deepseek v3?
```

---

## 3. Quick Start

```bash
cp .env.example .env   # Configure ANTHROPIC_API_KEY & FIRECRAWL_API_KEY
uv sync
uv run mcp_client.py
```

## License

MIT License — see [LICENSE](LICENSE).
