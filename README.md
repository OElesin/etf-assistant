# JustETF MCP Server

An MCP (Model Context Protocol) server that gives AI agents access to European UCITS ETF data. Search, filter, and evaluate ETFs for tax efficiency — designed for EU investors.

## Tools

| Tool | Description |
|------|-------------|
| `search_etfs` | Search/filter the ETF universe by name, ISIN, domicile, TER, AUM, distribution policy |
| `get_etf_details` | Get full details for a specific ETF by ISIN |
| `calculate_tax_efficiency` | Score an ETF's tax efficiency with a detailed breakdown |
| `refresh_etf_data` | Trigger a fresh scrape of JustETF to update local data |

## Quick Start (Local)

### Prerequisites
- Python 3.10+
- A local ETF data file (`output.json` or `demo.json`) — included in the repo

### Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run
```bash
python server.py
```

This starts the MCP server on stdio transport (the default for local MCP connections).

### Configure in your MCP client

Add to your MCP client configuration (e.g. Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "justetf": {
      "command": "python",
      "args": ["/path/to/etf-assistant/server.py"]
    }
  }
}
```

---

## Deploy to AWS Lambda

The server can be deployed as a remote MCP endpoint on AWS Lambda using the [Lambda Web Adapter](https://github.com/aws/aws-lambda-web-adapter) pattern.

### Architecture

```
MCP Client → API Gateway (HTTP API) → Lambda Web Adapter → FastMCP (uvicorn:8000/mcp)
```

- **Transport:** Streamable HTTP (stateless)
- **Runtime:** Python 3.13, arm64
- **Endpoint:** `POST https://<api-id>.execute-api.<region>.amazonaws.com/prod/mcp`

### Prerequisites
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- AWS credentials configured (`aws configure`)
- Docker (optional, for `--use-container` builds)

### Build & Deploy

```bash
sam build
sam deploy
```

On first deploy, SAM will prompt for confirmation. Subsequent deploys reuse the config in `samconfig.toml`.

The stack outputs the MCP endpoint URL.

### Connect a remote MCP client

Once deployed, configure your MCP client to use the remote endpoint:

```json
{
  "mcpServers": {
    "justetf": {
      "url": "https://etf-mcp.getbrechtai.com/mcp"
    }
  }
}
```

> The server is also accessible via the raw API Gateway URL:
> `https://<api-id>.execute-api.eu-west-1.amazonaws.com/prod/mcp`

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `AWS_LWA_PORT` | `8000` | Port the web adapter forwards to |

---

## Project Structure

```
etf-assistant/
├── server.py           # MCP server entry point (4 tools)
├── run.sh              # Lambda Web Adapter startup script
├── src/
│   ├── etf_data.py     # ETF data loading and normalization
│   └── scraper.py      # JustETF web scraper
├── output.json         # Cached ETF data (primary)
├── demo.json           # Demo ETF dataset (fallback)
├── data/
│   └── etf_data.csv    # Raw CSV export
├── template.yaml       # SAM template (Lambda + API Gateway)
├── samconfig.toml      # SAM deployment config
├── requirements.txt
└── README.md
```

## Data

ETF data is loaded from local JSON files (`output.json` → `demo.json` fallback). The data includes:

- ISIN, name, ticker
- Total Expense Ratio (TER)
- Fund domicile (Ireland, Luxembourg, etc.)
- Assets Under Management (AUM)
- Distribution policy (accumulating vs distributing)
- Replication method
- Computed tax efficiency score

To refresh the data, call the `refresh_etf_data` tool or run the scraper directly:

```bash
python -m src.scraper
```

## Tax Efficiency Scoring

The tax efficiency score (0–1) is a heuristic based on factors relevant to EU investors:

| Factor | Bonus |
|--------|-------|
| Base | 0.50 |
| Accumulating distribution policy | +0.30 |
| Irish domicile | +0.20 |
| Luxembourg domicile | +0.15 |
| Physical/full replication | +0.10 |
| AUM > €1bn | +0.10 |
| AUM > €100m | +0.05 |
| TER < 0.20% | +0.05 |

## License

MIT
