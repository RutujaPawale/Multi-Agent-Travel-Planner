# 🌍 Multi-Agent AI Travel Planner

A production-ready multi-agent travel planning platform orchestrated using **LangGraph** (Python FastAPI), managed through a **Spring Boot** API service (Java 21), and visualized via a modern **React + TypeScript** dashboard backed by a **PostgreSQL** database.

---

## 🏗️ Architecture Overview

```
                      +-----------------------------+
                      |   React + TypeScript UI     |
                      |   (Vite Dashboard :3000)    |
                      +--------------+--------------+
                                     |
                                     | REST: /api/trips
                                     v
                      +-----------------------------+
                      |    Java Spring Boot API     |
                      |    (api-service :8080)      |
                      +----+-------------------+----+
                           |                   |
               POST /plan-trip|                   | CRUD & History
                           |                   |
                           v                   v
              +-----------------------+   +-------------------+
              |  Python LangGraph     |   |    PostgreSQL     |
              |  (agent-service :8000)|-->|      (:5432)      |
              +-----------------------+   |  trips, users,    |
                           |              |  agent_runs       |
                           |              +-------------------+
                           v
              +-----------------------------------------------+
              |            LangGraph State Pipeline           |
              |  1. Orchestrator Init Node                    |
              |  2. Flight Agent (Provider: Duffel / Mock)    |
              |  3. Hotel Agent (Provider: Duffel / Mock)     |
              |  4. Activity Agent (Stubbed Curated Tours)    |
              |  5. Budget Agent (Cost & Feasibility Review)  |
              |  6. Itinerary Synthesizer Node                |
              +-----------------------------------------------+
```

### Components

1. **`agent-service/` (Python 3.11+, FastAPI, LangGraph)**
   - Houses the `StateGraph` orchestration workflow.
   - **Provider Architecture**:
     - `FlightProvider` & `HotelProvider`: Abstract interfaces with normalized Pydantic models (`FlightOption`, `HotelOption`).
     - `DuffelProvider`: Integrates with Duffel API v2 (`/air/offer_requests` for flight searches, `/stays/search` for hotel offers).
     - `MockProvider`: Generates realistic offline mock data with calibrated pricing and rankings.
     - Provider selection controlled via `FLIGHT_PROVIDER` and `HOTEL_PROVIDER` environment variables (`duffel` | `mock`), defaulting to `mock` when `DUFFEL_API_KEY` is omitted.
     - Automatically logs fallback reasons (missing API key, HTTP status codes, or exceptions) to `agent_runs.error_message`.
   - **Hotel Agent**: Allocates a configurable lodging percentage (`HOTEL_BUDGET_PCT`, default `35.0%`) to establish a per-night budget cap, ranking top 3 options by rating (descending), then price (ascending).
   - **Activity Agent (Stub)**: Curates top tourist activities and food tours.
   - **Budget Agent (Stub)**: Computes total projected expenses, budget surplus/deficit, and financial feasibility.
   - **PostgreSQL Agent Logger**: Logs every agent step (`agent_name`, `input_data`, `output_data`, `status`, `error_message`, `created_at`) directly to the `agent_runs` table in PostgreSQL.

2. **`api-service/` (Java 21, Spring Boot 3.3, Spring Data JPA)**
   - Handles trip lifecycle and persistence (`trips` table).
   - Dispatches planning tasks to `agent-service:8000/plan-trip`.
   - Exposes REST endpoints (`/api/trips`, `/api/trips/{id}`, `/api/health`).
   - Retrieves persistent agent run history from `agent_runs` table.

3. **`dashboard/` (React 18, TypeScript, Vite)**
   - User-friendly travel planning form (Origin, Destination, Dates, Budget, Preferences).
   - Interactive demo presets for quick testing.
   - **Raw JSON Response Viewer**: Pretty-printed JSON view with copy-to-clipboard and export.
   - **Structured UI Viewer**: Tabbed view of Flights, Hotels, Activities, Budget, and live PostgreSQL agent run execution timeline with fallback status inspection.

4. **`PostgreSQL` (Database)**
   - Initialized via `docker/init.sql`.
   - Stores `users`, `trips`, and `agent_runs`.

---

## 🚀 Quickstart with Docker Compose

Run the entire stack with a single command:

```bash
docker compose up --build
```

Once running, access:
- **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Spring Boot API**: [http://localhost:8080/api/health](http://localhost:8080/api/health)
- **Agent Service Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL**: `localhost:5432` (`postgres:postgres`, DB: `travel_planner`)

---

## 🔑 Duffel API & Provider Configuration

To enable live flight and hotel searches using Duffel API v2:

1. Create a free developer account at [Duffel](https://duffel.com/).
2. In developer test mode, generate a test API token (prefixed with `duffel_test_`).
3. Set your token and provider preferences in `.env`:

```env
# Duffel Test Mode Token
DUFFEL_API_KEY=duffel_test_your_token_here

# Provider Selection (duffel | mock)
FLIGHT_PROVIDER=duffel
HOTEL_PROVIDER=duffel

# Lodging Budget Allocation Percentage (default: 35%)
HOTEL_BUDGET_PCT=35.0
```

> **Automatic Fallback Guarantee**: If `DUFFEL_API_KEY` is empty, omitted, or encounters an API error, both agents seamlessly fall back to `MockProvider`. The exact fallback reason (e.g. `Missing DUFFEL_API_KEY environment variable` or HTTP error status) is recorded in `agent_runs.error_message`.

---

## 🧪 Local Testing & Verification

### 1. Verify LangGraph Orchestration Flow & Providers
```bash
python -c "import sys; sys.path.insert(0, 'agent-service'); from agents.orchestrator import create_travel_planner_graph; graph = create_travel_planner_graph(); print('LangGraph compiled successfully')"
```

### 2. Verify React + TypeScript Dashboard Build
```bash
cd dashboard
npm install
npm run build
```

### 3. Validate Docker Compose Wiring
```bash
docker compose config
docker compose up --build
```
