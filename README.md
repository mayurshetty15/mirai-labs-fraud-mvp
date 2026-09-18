# MiRai Fraud Intelligence

MiRai is a fraud-investigation prototype for analyst-assisted transaction review. It combines a time-split machine-learning model with transaction rules, Redis velocity checks, Neo4j device relationships, PostgreSQL history, anomaly scoring, and a Streamlit analyst console.

This repository is suitable for local development, demonstrations, and controlled evaluation. It is **not production-ready or a compliance certification**. Production use requires security review, data-governance approval, model-risk approval, operational monitoring, and a documented incident-response process.

## Contents

- [System Overview](#system-overview)
- [Repository Layout](#repository-layout)
- [Prerequisites](#prerequisites)
- [Configuration and Secrets](#configuration-and-secrets)
- [Quick Start](#quick-start)
- [Services and Endpoints](#services-and-endpoints)
- [Analyst Workflow](#analyst-workflow)
- [Data and Time Semantics](#data-and-time-semantics)
- [Modeling](#modeling)
- [Database Seeding](#database-seeding)
- [Testing](#testing)
- [Engineering Standards](#engineering-standards)
- [Security and Privacy](#security-and-privacy)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Contribution Checklist](#contribution-checklist)

## System Overview

```text
CSV dataset
   |
   +--> time-based model training --> LightGBM artifact
   |
   +--> PostgreSQL transactions <---- FastAPI API <---- Streamlit console
   |             ^                     |
   |             |                     +--> Redis velocity checks
   |             |                     +--> Neo4j device/card graph
   |             |                     +--> IsolationForest anomaly check
   |             |                           +--> bounded investigation agent
   |             +--> persisted analyst decisions and traces
```

The request path for a card investigation is:

1. Streamlit sends `GET /transaction/{card_id}`.
2. FastAPI retrieves the latest transaction and card history from PostgreSQL.
3. A missing source card can be seeded on demand from the full CSV.
4. The pipeline evaluates velocity, device graph, LightGBM, anomaly, and decision layers.
5. The optional Gemini investigation agent gathers evidence through bounded tool calls.
6. The API returns the case, history, display timestamps, decision, and agent result.

## Repository Layout

```text
mirai_project/
├── app/
│   ├── api.py                  FastAPI application and HTTP endpoints
│   ├── agent.py                Bounded Gemini investigation loop and trace persistence
│   ├── batch_score.py          Batch scoring for unscored database rows
│   ├── config.py               Environment configuration
│   ├── db_neo4j.py             Neo4j connection helper
│   ├── db_postgres.py          PostgreSQL connection helper
│   ├── db_redis.py             Redis connection helper
│   ├── layer1_rules.py         Velocity rule
│   ├── layer2_graph.py         Device/card graph rule
│   ├── layer3_model.py         Time split, LightGBM, baseline, SHAP, metrics
│   ├── layer4_anomaly.py       IsolationForest scoring
│   ├── layer5_decision.py      Deterministic allow/review/block decision logic
│   ├── lookup.py               PostgreSQL lookups and decision persistence
│   ├── print_model_metrics.py  Launcher metrics output
│   ├── pipeline.py             End-to-end scoring pipeline
│   ├── seed_database.py        Deliberate complete-card-history seeding
│   ├── time_utils.py           Shared dataset-time display conversion
│   └── tools.py                Structured historical investigation tools
├── data/
│   └── creditcard_augmented.csv
├── frontend/
│   └── app.py                  Streamlit analyst console
├── models/
│   ├── anomaly_model.pkl
│   ├── anomaly_threshold.json
│   └── gbt_model.pkl
├── tests/
│   ├── test_agent.py
│   ├── test_connections.py
│   └── test_tools.py
├── requirements.txt
└── run_project.ps1
```

## Prerequisites

- Windows PowerShell 5.1 or PowerShell 7 for the supplied launcher.
- Python 3.12 or a compatible supported Python version.
- PostgreSQL 14+ recommended.
- Redis with sorted-set support.
- Neo4j 5+ recommended.
- Network access to configured services.
- Optional: Gemini API key for the LLM investigation loop.

## Configuration and Secrets

Create a local `.env` file in the project root. Never commit `.env`, passwords, API keys, private certificates, or production connection strings.

Required variables:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mirai_fraud_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<local-secret>

REDIS_HOST=<redis-host>
REDIS_PORT=<redis-port>
REDIS_USERNAME=<redis-username>
REDIS_PASSWORD=<redis-secret>

NEO4J_URI=neo4j+s://<instance>.databases.neo4j.io
NEO4J_USERNAME=<neo4j-username>
NEO4J_PASSWORD=<neo4j-secret>

# Optional. Without this, investigations explicitly escalate instead of
# pretending that an LLM decision was produced.
GEMINI_API_KEY=<gemini-secret>
GEMINI_MODEL=gemini-3.6-flash
```

The checked-in `.env.example` must contain placeholders only. If any real credential has ever been committed or shared, revoke and rotate it before using the repository. Secret rotation is required even when the credential appears to be for development.

## Quick Start

From `mirai_project`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env with local credentials.
```

Verify database connectivity:

```powershell
python tests/test_connections.py
```

Seed PostgreSQL with a deliberate sample of complete card histories:

```powershell
python -m app.seed_database
```

Start the API and Streamlit console:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_project.ps1
```

The launcher prints saved-model holdout metrics, stops processes on ports `8001` and `8502`, and starts both services without opening additional PowerShell windows.

## Services and Endpoints

Base API URL: `http://127.0.0.1:8001`

| Method | Endpoint                                | Purpose                                          |
| ------ | --------------------------------------- | ------------------------------------------------ |
| `GET`  | `/health`                               | PostgreSQL, Redis, and Neo4j connectivity status |
| `GET`  | `/queue`                                | Highest-risk pre-scored transactions             |
| `GET`  | `/transaction/{card_id}`                | Retrieve and investigate a card transaction      |
| `POST` | `/decision`                             | Persist an analyst decision                      |
| `GET`  | `/model-metrics`                        | Current saved-model holdout metrics              |
| `GET`  | `/investigation/{transaction_id}/trace` | Retrieve persisted agent trace                   |

Interactive API documentation is available at `http://127.0.0.1:8001/docs` while the API is running.

```powershell
Invoke-RestMethod http://127.0.0.1:8001/transaction/card_b39a7255
```

## Analyst Workflow

1. Open `http://127.0.0.1:8502`.
2. Enter a card ID and select **Begin investigation**.
3. Review the transaction summary, decision signal, velocity, device links, anomaly state, and explanation.
4. Select **View Full Card History** for the dedicated history page.
5. Use `Most Recent`, `Show All`, or `Fraud Only` history views.
6. Use **Back to Case** to return to the overview.
7. Confirm the system decision or submit an allow/block override with a reason.

The UI uses page-level session-state navigation. A new card lookup always returns to the case overview.

## Data and Time Semantics

The source dataset is `data/creditcard_augmented.csv`. Its `Time` column contains transaction-relative seconds, not real calendar timestamps.

- Raw `time` remains numeric dataset-relative seconds in PostgreSQL and model inputs.
- `app/time_utils.py` maps `time=0` to `01/09/2026 00:00:00 UTC` for display only.
- Display format is `DD/MM/YYYY` and `HH:MM:SS`.
- Query filters, as-of comparisons, velocity windows, and model features continue using raw seconds.
- Velocity messages remain relative durations such as `5 transactions in the last 60 seconds`.

Do not use display fields for queries, training, thresholding, or feature generation.

## Modeling

`app/layer3_model.py` sorts the CSV by `Time` and reserves the most recent 20% as a time-based holdout. It evaluates ROC-AUC, PR-AUC, precision, recall, and accuracy for the baseline and LightGBM model. The launcher evaluates the saved LightGBM artifact without retraining.

The current decision pipeline is:

- **Layer 1:** Redis sorted-set velocity rule.
- **Layer 2:** Neo4j device-to-card relationship rule.
- **Layer 3:** LightGBM score and SHAP explanation helper.
- **Layer 4:** IsolationForest anomaly score.
- **Layer 5:** deterministic allow/review/block combination logic.

Layer 5 thresholds are prototype rules, not a calibrated production authorization policy.

## Database Seeding

`app/seed_database.py` selects cards deliberately instead of taking the first rows of the CSV.

```python
SEED_CARD_LIMIT = 400
SEED_ROW_LIMIT = 25_000
```

The sample prioritizes high-history cards, cards containing confirmed fraud rows, and the documented demo card `card_b39a7255`. Every selected card receives its complete source history. The script truncates the development table before inserting and prints coverage statistics.

If a valid source card is requested but is not in the limited PostgreSQL sample, the API can seed that card’s complete history on demand. Unknown source cards still return `404`.

## Structured Investigation Tools

`app/tools.py` exposes:

- `get_transaction`
- `get_card_history`
- `get_device_history`
- `get_email_domain_profile`
- `get_velocity`
- `get_similar_transactions`
- `get_model_explanation`

Historical tools accept an `as_of` datetime and filter stored dataset-relative seconds before that cutoff. The velocity evidence tool is read-only. Card, device, and email identifiers are masked at the tool boundary.

## Testing

```powershell
python -m pytest -q
python -m pytest tests/test_tools.py -q
python -m pytest tests/test_agent.py -q
python -m py_compile app/*.py frontend/app.py
```

Connectivity tests depend on live services. Unit tests must not require production credentials or external network access.

## Engineering Standards

- Keep functions small and single-purpose.
- Preserve public function contracts unless a migration is documented.
- Prefer typed parameters and return values for shared APIs and tools.
- Use parameterized SQL; never concatenate user input into SQL.
- Keep raw data semantics separate from presentation formatting.
- Add focused regression tests for every bug fix.
- Do not commit generated model artifacts without documenting provenance and reproducibility.
- Pull requests must include problem statement, implementation summary, test results, data/model impact, security impact, and rollback notes where relevant.
- Model/data changes must document dataset version, schema, time split, feature rationale, training command, artifact checksum, and evaluation results.

## Security and Privacy

- Do not place credentials in source files, README examples, screenshots, logs, or issue comments.
- Use secret managers in shared or production environments.
- Revoke and rotate credentials immediately if exposed.
- Use TLS for PostgreSQL, Redis, Neo4j, and API traffic outside local development.
- Restrict CORS origins to approved applications; the local configuration is not a production allowlist.
- Mask card identifiers, devices, and email domains before analyst or model exposure where possible.
- Treat customer free text and external metadata as untrusted input.
- Never allow text embedded in a customer field to become an agent instruction.
- Minimize stored PII and define retention/deletion policies before production use.
- Do not log full card numbers, credentials, access tokens, or raw customer messages.

## Known Limitations

- Gemini investigation requires `GEMINI_API_KEY`; without it, the agent escalates.
- Model output is not calibrated to a validated probability interpretation.
- Thresholds lack a documented fraud-capture/workload trade-off.
- The dataset uses anonymized features and a synthetic display-time anchor.
- The evaluation harness is not yet a complete 200+ transaction agent benchmark with adversarial and OOD suites.
- External database availability affects live velocity, graph, and history behavior.
- The API has local-development CORS and no production authentication/authorization layer.
- Trace persistence requires PostgreSQL and needs retention/access controls.

Do not present this prototype as a certified fraud decisioning system or evidence of regulatory compliance.

## Troubleshooting

### `ModuleNotFoundError: app.time_utils; 'app' is not a package`

The frontend file is also named `app.py`, which can shadow the root `app` package when Streamlit loads it. The frontend loads `app/time_utils.py` by absolute path to avoid this collision. Run the launcher from `mirai_project`.

### Card lookup returns `404`

Confirm the card exists in `data/creditcard_augmented.csv`, verify PostgreSQL connectivity, and inspect API logs. Valid source cards missing from the limited seed can be inserted on demand.

### Database connection failure

```powershell
python tests/test_connections.py
```

Then verify `.env`, service availability, firewall rules, TLS settings, and credentials. Never paste secrets into support tickets.

### Port already in use

`run_project.ps1` stops processes on ports `8001` and `8502`. Confirm process ownership before stopping another application manually.

## Contribution Checklist

- [ ] No secrets, credentials, or personal data were added.
- [ ] Raw transaction-time semantics are unchanged.
- [ ] Unit tests cover the changed behavior.
- [ ] Full test suite passes.
- [ ] API/UI behavior was manually checked when applicable.
- [ ] SQL is parameterized.
- [ ] New dependencies are justified and reviewed.
- [ ] README and operational documentation are updated.
- [ ] Model/data changes include split policy and evaluation evidence.
- [ ] Schema or seed changes include rollback/reseed instructions.

## License and Ownership

No license or formal ownership policy is currently declared. Before external distribution or production adoption, add an approved license, data-use policy, code-owner configuration, and contribution policy.
