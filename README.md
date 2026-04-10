# Threat Detection System

A full-stack system that detects anomalous user behavior on Linux endpoints and presents actionable security insights. It combines **privacy-preserving command hashing** (PSI), **unsupervised ML** (Isolation Forest), and **explainable AI** (XAI) to surface alerts and risk scores in a modern web dashboard.

---

## Table of contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Hardware sensors](#hardware-sensors)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Running with Docker](#running-with-docker)
- [Running the agent](#running-the-agent)
- [Configuration](#configuration)
- [Threat hashes (PSI)](#threat-hashes-psi)
- [Sample data and demos](#sample-data-and-demos)
- [API reference](#api-reference)
- [Testing](#testing)
- [Project layout](#project-layout)
- [Security and operations](#security-and-operations)

---

## Overview

The system has four main parts:

| Component | Role |
|-----------|------|
| **Endpoint Agent** | Runs on Linux hosts; collects auth logs, shell commands (as hashes only), and process execution; buffers and sends events to the engine with retry/backoff. |
| **Hardware Sensors** | Physical IoT sensors (MPU-6050 gyroscope/accelerometer, HW-485 sound sensor, HW-509 magnetic sensor) attached to monitored hardware; readings are sent directly to the engine as `sensor` events. |
| **Detection Engine** | FastAPI service that receives events from both the endpoint agent and hardware sensors, runs hash-based PSI (threat-command check), unsupervised ML (Isolation Forest), and XAI (human-readable explanations); stores raw events, processed events, and alerts in PostgreSQL. |
| **Web Dashboard** | React + TypeScript + Vite app that shows alerts, risk scores, explanations, sensor readings, and an activity timeline with filtering; proxies `/api` to the engine. |

**Data flow (high level):**
- Agent → `POST /api/v1/events` → Engine (PSI → ML → XAI) → DB → Dashboard
- Hardware sensors → `POST /api/v1/events` → Engine (ML → XAI) → DB → Dashboard (Sensors page)

---

## Architecture

```
┌─────────────────┐                              ┌──────────────────────────────────────┐
│  Linux host(s)  │  POST /api/v1/events         │  Detection Engine (FastAPI)           │
│                 │ ──────────────────────────► │  • Ingest & validate (event schema)   │
│  • Auth log     │                              │  • PSI: command_hash ∈ threat DB?     │
│  • Bash history │                              │  • ML: Isolation Forest anomaly score │
│  • Process list │                              │  • XAI: explanation text              │
│  Agent          │                              │  • Store: raw_event, processed_event, │
└─────────────────┘                              │         alert (if risk ≥ threshold)   │
                                                 │                                       │
┌─────────────────┐                              │  Sensor pipeline:                     │
│ Hardware sensors│  POST /api/v1/events         │  • Validate sensor payload            │
│                 │ ──────────────────────────► │  • Extract features (accel, gyro,     │
│  • MPU-6050     │                              │    trigger, sensor_type, time, etc.)  │
│    gyro/accel   │                              │  • ML: Isolation Forest risk score    │
│  • HW-485 sound │                              │  • XAI: explanation + anomaly reason  │
│  • HW-509 magnet│                              │  • Alert if risk ≥ threshold          │
└─────────────────┘                              └──────────────────┬───────────────────┘
                                                                     │
                                                                     ▼
┌─────────────────┐     GET /api/v1/alerts       ┌──────────────────────────────────────┐
│  Web Dashboard  │ ◄────────────────────────── │  PostgreSQL                           │
│  (React + Vite) │     GET /api/v1/activity     │  • raw_events, processed_events,      │
│                 │     GET /api/v1/events       │    alerts, threat_hashes, machines,   │
│  • Alerts list  │                              │    users                              │
│  • Activity     │                              │  • Persisted model: global_model.joblib│
│  • Risk & XAI   │                              └──────────────────────────────────────┘
│  • Sensors page │
└─────────────────┘
```

- **PSI (Private Set Intersection):** Commands are sent only as SHA-256 hashes; the server never sees raw command text. The engine checks each `command_hash` against a threat database (file + DB table).
- **ML:** For events not in the threat set, the engine extracts features (time, source, user/machine buckets, command hash bucket, etc.) and scores them with a global Isolation Forest. Risk is mapped to 0–100; scores above the configured threshold create an alert.
- **XAI:** Every processed event gets a short explanation (e.g. “Known malicious command” for PSI hits, or “Highly anomalous activity…” with contributing factors for ML anomalies).
- **Sensor pipeline:** Sensor events bypass PSI (no command hash) and go directly to ML feature extraction and scoring. Sensor features include accelerometer/gyroscope axes, trigger state, sensor type encoding, and temporal features.

---

## Components

### Endpoint Agent (`agent/`)

- **Collectors:**  
  - **AuthCollector:** Reads `/var/log/auth.log` or `journalctl` for logins, logouts, sudo, failures.  
  - **CommandCollector:** Reads shell history (e.g. `/home/*/.bash_history`); normalizes and hashes each command; sends only `command_hash` and optional `command_length`.  
  - **ProcessCollector:** Samples running processes (e.g. exe, argv, pid, parent_pid, start_time).
- **Buffer:** In-memory (optional file persist via `AGENT_PERSIST_PATH`) event buffer; batches are sent at a configurable interval or when batch size is reached.
- **Sender:** HTTP POST to engine with optional `Authorization: Bearer <AGENT_API_KEY>`; retries with backoff on failure.

### Detection Engine (`engine/`)

- **API:** FastAPI app; routes under `/api/v1` (events, alerts, activity, admin, dashboard). Optional API-key auth via `ENGINE_API_KEY`.
- **Pipeline:** For each raw event: run PSI (if command); if not in threat set, ensure global Isolation Forest is fitted (from DB or disk), score event, build contributing factors; run XAI to produce explanation; store `ProcessedEvent` and optionally `Alert` if risk ≥ threshold.
- **Models:** `RawEvent`, `ProcessedEvent`, `Alert`, `ThreatHash`, etc.; Alembic migrations in `engine/db/migrations`.
- **ML:** `engine/ml/features.py` (feature vector from event), `engine/ml/model.py` (Isolation Forest), `engine/ml/registry.py` (load/save global model, score events).
- **PSI:** `engine/psi/checker.py` — set of threat hashes from DB + file; `check(hash)` returns (in_threat, category).
- **XAI:** `engine/xai/explainer.py` — builds explanation string from risk score, PSI result, and event context.

### Web Dashboard (`dashboard/`)

- **Stack:** React, TypeScript, Vite; Recharts for charts; proxy `/api` to engine.
- **Pages:** Dashboard (overview), Alerts (list/detail), Activity (timeline), Sensors (live sensor readings and risk), with filters (machine, user, time range, risk).
- **Features:** Risk badges, explanation blocks, timeline strip, sensor charts (line chart for gyro axes, bar chart for risk); auto-refresh for live view.

### Shared (`shared/`)

- **Event schema:** `event_schema.json` defines the unified activity event format (event_type, machine_id, user, timestamp, source, payload). Agent, sensors, and engine all validate against it; command events require normalized `command_hash` (see [Threat hashes (PSI)](#threat-hashes-psi)).

---

## Hardware sensors

The system supports three physical IoT sensors that report environmental and physical state. Sensor events are sent as `POST /api/v1/events` with `event_type: "sensor"` and `source: "sensor"`.

### MPU-6050 — Gyroscope / Accelerometer (`sensor_type: "gyro"`)

3-axis accelerometer (g) and 3-axis gyroscope (°/s) attached to monitored hardware.

| Field | Unit | Normal range |
|-------|------|--------------|
| `ax` | g | ~0 (stationary) |
| `ay` | g | ~0 (stationary) |
| `az` | g | ~9.81 (upright) |
| `gx` | °/s | ~0 (no rotation) |
| `gy` | °/s | ~0 (no rotation) |
| `gz` | °/s | ~0 (no rotation) |

**Anomaly scenarios detected:**

| Scenario | Description |
|----------|-------------|
| `impact_detected` | Sudden high-g spike — possible physical tampering or collision |
| `freefall` | Near-zero gravity on all axes — device detached or dropped |
| `sustained_vibration` | Persistent high-frequency vibration — motor fault or structural resonance |
| `tilt_anomaly` | Device tilted beyond safe angle — mounting may have shifted |

### HW-485 — Big Sound Sensor (`sensor_type: "sound"`)

Binary trigger sensor. `triggered: true` means a loud sound threshold was exceeded.

| Anomaly reason | Scenario |
|----------------|----------|
| Loud sound burst | Possible glass break or explosion |
| Sustained loud noise | Possible alarm or machinery malfunction |
| Repeated triggers in short interval | Possible intrusion attempt |

### HW-509 — Magnetic Sensor (`sensor_type: "magnetic"`)

Binary trigger sensor mounted on enclosures or doors. `triggered: true` means a magnetic field change was detected.

| Anomaly reason | Scenario |
|----------------|----------|
| Magnetic field change | Door or enclosure may have been opened |
| Strong magnetic interference | Possible magnet-based tampering |
| Triggered in restricted hours | Unauthorized physical access |

### Sensor data flow

```
Physical sensor reading
        │
        ▼
POST /api/v1/events  (event_type="sensor", source="sensor")
        │
        ▼
Engine ingests RawEvent
        │
        ▼
Feature extraction:
  hour, dow, sensor_type_enc,
  ax, ay, az (clipped to ±1 at ±16 g),
  gx, gy, gz (clipped to ±1 at ±2000 °/s),
  triggered (0.0 / 1.0)
        │
        ▼
Isolation Forest scores event → risk 0–100
        │
        ▼
XAI builds explanation
  • payload.reason from sensor (pre-classified)
  • ML contributing factors (axis deviations, trigger state)
        │
        ├── risk ≥ threshold → Alert created → Dashboard Alerts page
        └── always → ProcessedEvent → Dashboard Sensors + Activity pages
```

### Running the sensor simulator

The simulator generates realistic sensor readings and streams them to the engine:

```bash
pip install requests
python scripts/sensor_simulator.py                         # defaults: localhost:8000, 2-second interval
python scripts/sensor_simulator.py --url http://<host>:8000/api/v1/events --interval 1.0
python scripts/sensor_simulator.py --api-key <key> --machine-id <uuid>
```

Each cycle sends one gyro reading, one sound reading, and one magnetic reading. Approximately 15% of gyro and sound events and 10% of magnetic events are randomly generated as unsafe anomalies.

### Sending sensor data directly

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '[{
    "event_type": "sensor",
    "machine_id": "a3f1b2c4-1234-5678-abcd-ef0123456789",
    "user": "system",
    "timestamp": "2026-04-10T10:00:00Z",
    "source": "sensor",
    "payload": {
      "sensor_id": "mpu-6050-01",
      "sensor_type": "gyro",
      "ax": 0.02, "ay": -0.01, "az": 9.81,
      "gx": 0.5,  "gy": -0.3,  "gz": 0.1,
      "status": "safe",
      "reason": "Normal orientation and motion — readings within expected range"
    }
  }]'
```

See [docs/sensor_schema.md](docs/sensor_schema.md) for the full sensor payload schema and example payloads for all three sensor types.

---

## Prerequisites

- **Python** 3.10+ (engine and agent)
- **Node** 20+ (dashboard dev/build)
- **PostgreSQL** 16 (or use Docker)
- **Docker** and **Docker Compose** (optional; for one-command stack)

---

## Quick start

### 1. Database and engine

```bash
# Create database
createdb threat_detection

# From project root
export PYTHONPATH=.
pip install -r engine/requirements.txt

# Run migrations (set ENGINE_DATABASE_URL if your DB URL differs)
alembic -c engine/alembic.ini upgrade head

# Start engine
uvicorn engine.main:app --reload --host 0.0.0.0 --port 8000
```

- **Engine:** http://localhost:8000  
- **API docs:** http://localhost:8000/docs  

### 2. Dashboard

```bash
cd dashboard
npm install
npm run dev
```

- **Dashboard:** http://localhost:5173 (Vite proxies `/api` to the engine)

### 3. Agent (on a Linux host)

```bash
pip install -r agent/requirements.txt
export AGENT_ENDPOINT_URL=http://<engine-host>:8000/api/v1/events
python -m agent.main
```

Alternatively, install as a systemd service (see [Running the agent](#running-the-agent)).

---

## Running with Docker

From the project root you can start or stop all services (Postgres, Engine, Dashboard) with:

```bash
./start   # Start Postgres, Engine, and Dashboard (builds images if needed)
./stop    # Stop all services
```

Or run Docker Compose directly:

```bash
docker compose up -d
```

- **Engine:** http://localhost:8000  
- **Dashboard:** http://localhost:5173 (serves built app; no dev proxy)  
- **PostgreSQL:** localhost:5432  

**Notes:**

- Place `data/threat_hashes.txt` in the project so the engine can mount it.
- The persisted anomaly model is written to `data/models/global_model.joblib`; Docker mounts `./data/models` as writable for the engine.

---

## Running the agent

### One-off

```bash
export AGENT_ENDPOINT_URL=http://<engine-host>:8000/api/v1/events
# Optional: AGENT_API_KEY, AGENT_MACHINE_ID, AGENT_PERSIST_PATH, etc.
python -m agent.main
```

### Systemd

Use the provided unit file as a template:

- Copy `agent/threat_detection_agent.service` to `/etc/systemd/system/`.
- Set `WorkingDirectory` (e.g. `/opt/threat_detection_agent`) and ensure the agent code and dependencies are there.
- Set `Environment=AGENT_ENDPOINT_URL=http://<engine>:8000/api/v1/events` (and optionally `AGENT_API_KEY`).
- Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable threat_detection_agent
sudo systemctl start threat_detection_agent
```

---

## Configuration

### Engine (environment)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENGINE_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/threat_detection` | PostgreSQL connection URL |
| `ENGINE_THREAT_DB_PATH` | `data/threat_hashes.txt` | Path to file with threat hashes (one per line) |
| `ENGINE_ALERT_THRESHOLD` | `50.0` | Minimum risk score (0–100) to create an alert |
| `ENGINE_API_KEY` | (none) | If set, all `/api/v1` routes require `Authorization: Bearer <key>` |
| `ENGINE_LOG_LEVEL` | `INFO` | Log level |

`.env` in the project root is loaded if present (with `ENGINE_` prefix).

### Agent (environment and config)

| Variable / config | Description |
|-------------------|-------------|
| `AGENT_ENDPOINT_URL` | Engine URL (e.g. `http://localhost:8000/api/v1/events`). Required. |
| `AGENT_BATCH_SIZE` | Max events per batch (default 50). |
| `AGENT_SEND_INTERVAL_SECONDS` | Seconds between sends (default 30). |
| `AGENT_API_KEY` | Optional; sent as `Authorization: Bearer <key>`. |
| `AGENT_MACHINE_ID` | Override machine ID (default: `/etc/machine-id`). |
| `AGENT_PERSIST_PATH` | Optional file path to persist buffer across restarts. |

The agent also reads `agent/config.yaml` (e.g. `auth_log_path`, `history_glob`, `auth_source`, `log_level`). Env vars override config file values where applicable.

---

## Threat hashes (PSI)

Commands are compared by **hash** only; the server never sees raw command text. Agent and engine use the same normalization before hashing:

1. Strip leading/trailing whitespace  
2. Collapse internal whitespace to a single space  
3. Lowercase the string  

Then compute **SHA-256** of the UTF-8 encoded string.

**Example (Python):**

```python
from hashlib import sha256

def norm(c):
    return " ".join(c.strip().lower().split())

# Example: add hash for "rm -rf /"
h = sha256(norm("rm -rf /").encode()).hexdigest()
# Add that hash to data/threat_hashes.txt (one per line)
# Or POST to /api/v1/admin/threat-hashes
```

**Adding hashes:**

- **File:** Append one hash per line to `data/threat_hashes.txt` (path set by `ENGINE_THREAT_DB_PATH`).
- **API:** `POST /api/v1/admin/threat-hashes` with body `{"command_hash": "<hex>", "category": "optional"}`.

See `shared/README.md` and `shared/event_schema.json` for the full event and command-hash schema.

---

## Sample data and demos

### One-time seed (populate dashboard)

Send test events to the engine so the dashboard has data:

```bash
./scripts/seed_events.sh
```

Uses `ENGINE_URL` (default `http://localhost:8000`) and optionally `ENGINE_API_KEY`. Then refresh the dashboard at http://localhost:5173.

### Continuous demo agents

Stream events continuously to see the dashboard update:

```bash
# From project root; ensure engine is running
pip install requests   # if not already installed
python scripts/demo_agents.py
```

Set `ENGINE_URL` and optionally `ENGINE_API_KEY`. The script runs three demo agents that send auth, command, and process events every few seconds; the dashboard and Alerts/Activity pages can auto-refresh (e.g. every 5 seconds).

### Sensor simulator

Stream live sensor data from the three hardware sensor types:

```bash
pip install requests
python scripts/sensor_simulator.py
```

Each cycle (default 2 seconds) emits one gyro, one sound, and one magnetic reading with ~15% anomaly probability. The Sensors page in the dashboard auto-refreshes to show live risk scores and charts. See [Hardware sensors](#hardware-sensors) for full usage options.

### Force model file creation

Create the persisted anomaly model on disk without running demo agents:

```bash
# Engine must be running
python scripts/force_model_create.py
```

The script sends benign events until the engine has enough to fit the global Isolation Forest (e.g. ≥30 raw events), then saves `data/models/global_model.joblib`. Set `ENGINE_URL` and `ENGINE_API_KEY` if needed.

---

## API reference

Base path: `/api/v1`. If `ENGINE_API_KEY` is set, send `Authorization: Bearer <key>` for all `/api/v1` routes.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/events` | Ingest event batch (from agents or sensors). Body: JSON array of activity events (see `shared/event_schema.json`). Supports `event_type`: `auth`, `command`, `process`, `sensor`. |
| `GET`  | `/alerts` | List alerts. Query params: `machine_id`, `user`, `since`, `until`, `risk_min`, `limit`. |
| `GET`  | `/activity` | List processed events. Same query params as alerts. |
| `GET`  | `/events` | List raw events. Same query params. |
| `POST` | `/admin/threat-hashes` | Add threat hash. Body: `{"command_hash": "<hex>", "category": "optional"}`. |
| `GET`  | `/admin/threat-hashes` | List threat hashes. |

**Health (no auth):**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check; returns `{"status": "ok"}`. |

Root: `GET /` returns service name, version, and links to `/docs` and `/health`.

---

## Testing

From the project root, run all component tests:

```bash
./run_tests.sh
```

This runs:

- **Engine tests:** API (health, events ingest), PSI checker, ML features, XAI explainer, config. Uses in-memory SQLite by default (`ENGINE_DATABASE_URL=sqlite:///:memory:`).
- **Agent tests:** Event schema (normalize_command, command_hash, build_event), buffer, sender (mocked HTTP).
- **Dashboard:** `npm run lint` if available in `dashboard/package.json`.

**Optional:** use a virtualenv for isolated dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r engine/requirements.txt -r agent/requirements.txt
./run_tests.sh
```

**Run only engine or agent tests:**

```bash
export PYTHONPATH=.
pytest engine/tests -v
pytest agent/tests -v
```

---

## Project layout

```
threat_detection/
├── agent/                    # Endpoint agent
│   ├── collectors/           # Auth, Command, Process collectors
│   ├── buffer.py             # Event buffer (optional persist)
│   ├── sender.py             # HTTP send with retry
│   ├── main.py               # Entry point; config + collectors + loop
│   ├── config_loader.py      # Load config.yaml + env
│   ├── schema.py             # Event build + validation
│   ├── config.yaml           # Agent config (paths, batch, etc.)
│   ├── threat_detection_agent.service  # Systemd unit template
│   ├── requirements.txt
│   └── tests/
├── engine/                   # Detection engine (FastAPI)
│   ├── api/                  # Routes: events, alerts, activity, admin, dashboard, auth
│   ├── db/                   # Session, models, Alembic migrations
│   ├── ml/                   # Features, Isolation Forest, registry
│   ├── psi/                  # Threat-hash checker
│   ├── xai/                  # Explainer
│   ├── models/               # SQLAlchemy models (raw_event, processed_event, alert, etc.)
│   ├── main.py               # FastAPI app, CORS, routers
│   ├── config.py             # Settings (env prefix ENGINE_)
│   ├── pipeline.py            # Process raw event: PSI → ML → XAI → store
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── tests/
├── dashboard/                # React + TypeScript + Vite
│   ├── src/
│   │   ├── api/              # API client
│   │   ├── components/       # RiskBadge, AlertCard, FiltersBar, etc.
│   │   ├── pages/            # Dashboard, Alerts, Activity, AlertDetail
│   │   └── types/
│   ├── public/
│   ├── Dockerfile
│   ├── .gitignore
│   └── package.json
├── shared/
│   ├── event_schema.json     # Unified event JSON schema
│   └── README.md             # Schema and command-hash normalization
├── data/
│   ├── threat_hashes.txt     # One threat hash per line (optional; can use API only)
│   └── models/               # global_model.joblib (persisted Isolation Forest)
├── docs/
│   └── sensor_schema.md      # Sensor event schema reference
├── scripts/
│   ├── seed_events.sh        # One-time sample events
│   ├── demo_agents.py        # Continuous demo agents (auth, command, process)
│   ├── sensor_simulator.py   # Real-time IoT sensor data simulator
│   ├── clear_sensor_data.py  # Clear sensor events from the database
│   └── force_model_create.py # Create global_model.joblib
├── docker-compose.yml        # Postgres, engine, dashboard
├── start                     # ./start — start stack with Docker Compose
├── stop                      # ./stop — stop stack
├── run_tests.sh              # Run engine + agent (+ dashboard lint) tests
└── README.md
```

---

## Security and operations

- **Permissions:** The agent may need root or read access to `/var/log/auth.log` and to user shell history under `/home`. Run with least privilege where possible.
- **Secrets:** Keep `ENGINE_API_KEY` and `AGENT_API_KEY` secret; use HTTPS and secure channels in production.
- **Threat DB:** The threat database holds only hashes; raw malicious commands are not stored on the server.
- **Model file:** `data/models/global_model.joblib` is fitted from event data; ensure that directory is writable by the engine (e.g. Docker volume `./data/models`).
- **Database:** Run migrations after upgrades: `alembic -c engine/alembic.ini upgrade head`.

For event schema and command-hash normalization details, see `shared/README.md`.
