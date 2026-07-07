# T-Cloud Public Pricing Pipeline

Offloaded pricing data from the [T Cloud Public Price Calculator API][api-docs],
published as versioned JSON snapshots on GitHub Pages — useful for cost analysis,
comparisons over time, and offline tooling.

[api-docs]: https://docs.otc.t-systems.com/price-calculator/api-ref/

## How it works

```
 ┌───────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
 │ price API │ ──→ │ pipeline CLI │ ──→ │ deploy/ dir   │ ──→ │ GitHub Pages │
 │(paginated)│     │ fetch+flatten│     │ JSON + HTML   │     │ (public)     │
 └───────────┘     └──────────────┘     └───────────────┘     └──────────────┘
```

1. **Fetch** — queries the T‑Cloud pricing API with pagination, collecting all records
2. **Transform** — flattens nested API responses into a compact columnar format
3. **Checksum** — an MD5 hash of the normalised data detects whether anything changed
4. **Publish** — if new data differs, a timestamped JSON file is saved, the manifest
   updated, and the index page re‑rendered from a Jinja2 template
5. **Deploy** — GitHub Actions deploys `deploy/` to GitHub Pages on a schedule
   (Mon/Wed/Fri) or on push to `main`

## Project structure

```
├── pipeline/              # Python package
│   ├── __init__.py        #   version detection (git describe)
│   ├── __main__.py        #   CLI: fetch, checksum, transform, output
│   ├── price_api.py       #   paginated API client
│   └── transform.py       #   record normalisation
├── html/                  # GitHub Pages site
│   ├── index.html         #   Jinja2 template (rendered with j2cli)
│   └── index.css          #   Telekom-magenta colour scheme
├── .github/workflows/
│   └── publish.yml        # CI: fetch → check → publish → deploy to Pages
├── Makefile               # Task runner (fetch, vcheck, publish, serve, …)
├── pys                    # venv bootstrap + python runner
├── setup.sh               # venv creation / update
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Package metadata
```

## Quick start

```bash
# One‑time setup — creates .venv and installs dependencies
./pys -V

# Fetch latest prices from the API and save locally
make fetch PARAM=eu-de,eu-nl

# Run a local PHP dev server to preview the Pages site
make serve
# → http://localhost:9000
```

## Make targets

| Target      | Description |
|-------------|-------------|
| `fetch`     | Fetch pricing data from the API, write `deploy/prices-latest.json` + `deploy/sum.txt` |
| `vcheck`    | Compare current checksum against the deployed version; writes `changed=true\|false` to `$GITHUB_OUTPUT` |
| `publish`   | If changed: create timestamped copy, update `manifest.json`, render `index.html`, copy `index.css` |
| `tdep`      | Test deploy — copy `deploy/` → `www/` for local inspection |
| `serve`     | Start PHP dev server on `www/` (port 9000) |
| `help`      | Show all targets |

## Pipeline CLI

```bash
./pys -m pipeline [options] [params...]

Options:
  --url URL       API endpoint (default: EN endpoint)
  --en / --de     Shortcuts for English / German endpoints
  --load FILE     Read prices from a local JSON file instead of the API
  --save FILE     Save raw (pre‑transform) API response
  --cksum FILE    Compute MD5 checksum and write metadata to FILE
  -o, --output F  Write transformed JSON to FILE (default: stdout)

Params:
  region=eu-de,eu-nl   Comma‑separated region list
  serviceType=ecs      Filter by service type
```

## Data format

### Output JSON (`prices-latest.json`, `pricing-YYYY-MM-DD.json`)

```json
{
  "schema": "pipeline-pricing-1.0",
  "params": { "region[]": ["eu-de", "eu-nl"] },
  "columns": ["productName", "serviceType", "price", "…"],
  "services": { "ecs": "Elastic Cloud Server", "…": "…" },
  "count": 12345,
  "keys": ["productName", "serviceType", "…"],
  "records": [ ["ECS-001", "ecs", 0.042, "…"], "…" ],
  "timestamp": 1783412746.53,
  "datetime": "2026-07-07 10:25:46",
  "cksum": "44455e0992b92bc06e427772bf7d825f",
  "generatedBy": "pipeline v2ebf87b"
}
```

### Manifest (`manifest.json`)

```json
[
  {
    "datetime": "2026-07-07 10:25:46",
    "timestamp": "1783412746.530722",
    "cksum": "44455e0992b92bc06e427772bf7d825f",
    "file": "pricing-2026-07-07.json",
    "generatedBy": "pipeline v2ebf87b",
    "size": 3226416
  }
]
```

### Checksum (`sum.txt`)

```
44455e0992b92bc06e427772bf7d825f 2026-07-07 10:25:46 1783412746.530722 pipeline v2ebf87b
```


## Licence

MIT — see [LICENSE](LICENSE).
