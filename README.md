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
              |  4. Activity Agent (OpenTripMap API + LLM Planner) |
              |  5. Budget Agent (Cost & Feasibility Review)  |
              |  6. Itinerary Synthesizer Node                |
              +-----------------------------------------------+
```

### Components

1. **`agent-service/` (Python 3.11+, FastAPI, LangGraph)**
   - Houses the `StateGraph` orchestration workflow.
   - **Provider Architecture**:
     - `FlightProvider` & `HotelProvider`: Abstract interfaces with normalized Pydantic models (`FlightOption`, `HotelOption`).
     - `PlacesProvider`: Abstract interface for attraction and point-of-interest discovery returning `PlaceItem`.
     - `OpenTripMapProvider`: Queries OpenTripMap API (`https://opentripmap.io` via `/places/radius` and `/places/xid/{xid}`) for top attractions, dining, and sights matching traveler preferences. Free API key, no billing required.
     - `DuffelProvider`: Integrates with Duffel API v2 (`/air/offer_requests` for flight searches, `/stays/search` for hotel offers).
     - `MockProvider`: Generates realistic offline mock data for flights, hotels, and candidate places with calibrated pricing and rankings.
     - Provider selection controlled via `FLIGHT_PROVIDER`, `HOTEL_PROVIDER`, and `ACTIVITY_PROVIDER` environment variables, defaulting to `mock` when API keys are omitted.
     - Automatically logs fallback reasons (missing API key, HTTP status codes, or exceptions) to `agent_runs.error_message`.
   - **Activity Agent & LLM Planner**:
     - Discovers candidate places via `PlacesProvider`.
     - Allocates a configurable share of total budget to activities (`ACTIVITY_BUDGET_PCT`, default `20.0%`).
     - Generates a structured day-by-day plan using an LLM call (`LLM_PROVIDER` / `LLM_API_KEY`, supporting Gemini and OpenAI) with Pydantic JSON validation and single-retry error recovery.
     - Automatically falls back to a balanced rule-based daily distribution if the LLM key is absent or invalid.
   - **Hotel Agent**: Allocates a configurable lodging percentage (`HOTEL_BUDGET_PCT`, default `35.0%`) to establish a per-night budget cap, ranking top 3 options by rating (descending), then price (ascending).
   - **Budget Agent**: Computes total projected expenses, budget surplus/deficit, and financial feasibility.
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
   - **Structured UI Viewer**: Tabbed view of Flights, Hotels, Activities (grouped day-by-day with time slots, categories, addresses, and daily costs), Budget overview, and live PostgreSQL agent run execution timeline with fallback status inspection.

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

## 🔑 API & Provider Configuration

Configure keys in `.env` to enable live APIs:

```env
# Duffel Test Mode Token (Flights & Hotels)
DUFFEL_API_KEY=duffel_test_your_token_here
FLIGHT_PROVIDER=duffel
HOTEL_PROVIDER=duffel

# OpenTripMap API (Attractions & Points of Interest - https://opentripmap.io)
OPENTRIPMAP_API_KEY=your_opentripmap_api_key_here
ACTIVITY_PROVIDER=opentripmap

# LLM Planner (Day-by-Day Activity Synthesis)
LLM_PROVIDER=gemini
LLM_API_KEY=your_llm_api_key_here
LLM_MODEL=gemini-2.5-flash
LLM_FALLBACK_MODEL=gemini-3.1-flash-lite

# Budget Allocations (%)
HOTEL_BUDGET_PCT=35.0
ACTIVITY_BUDGET_PCT=20.0
```

> **Resilient LLM Execution & Automatic Fallback**: The Activity Agent LLM planner implements retry with exponential backoff (`2s`, `5s`, `10s`) specifically for HTTP 503 (High Demand) and HTTP 429 (Rate Limit) responses. If `LLM_MODEL` remains unavailable, it automatically switches to `LLM_FALLBACK_MODEL` (e.g. `gemini-3.1-flash-lite`). If all models in the chain fail or credentials are omitted, it gracefully falls back to the deterministic rule-based planner. The model that succeeded (or the fallback reason) is recorded in `agent_runs.output_data` and `agent_runs.error_message`.

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
