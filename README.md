# Multi-Agent AI Travel Planner

A full-stack travel planning app built around a LangGraph multi-agent pipeline that searches flights, finds lodging, discovers activities, generates an LLM-curated day-by-day itinerary, and **adaptively re-plans itself** when the total cost exceeds the user's budget — with every agent decision streamed live to the browser over WebSocket and logged to Postgres for full auditability.

Built as a portfolio project to go deeper on multi-agent orchestration, real-time systems, and resilient integration with third-party APIs than a typical CRUD app allows.

\---

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│  Dashboard  │◄────►│  api-service │◄────►│  agent-service   │
│ React + TS  │ REST │ Java/Spring  │ REST │ Python/FastAPI   │
│             │  WS  │   Boot       │      │   + LangGraph    │
└─────────────┘      └──────┬───────┘      └────────┬─────────┘
                             │                       │
                             ▼                       ▼
                       ┌─────────────────────────────────┐
                       │          PostgreSQL              │
                       │  users · trips · agent\_runs       │
                       └───────────────────────────────────┘
```

**Agent pipeline (LangGraph):**

```
Orchestrator → Flight Agent ─┐
               Hotel Agent ──┼──► Budget Agent ──► over budget? ──► re-query
               Activity Agent┘         │                              over-budget
                                        │ within budget / max retries
                                        ▼
                                   Synthesizer → final itinerary
```

The Budget Agent isn't just a cost calculator — it identifies which category is over budget, cuts that agent's budget cap by 20%, and routes execution **directly back to that one agent** (not the whole pipeline) via conditional LangGraph edges. Capped at 2 re-planning attempts to avoid infinite loops. Every attempt, including the reasoning ("flight over budget by $X, re-querying with 20% lower cap"), is logged to `agent\_runs` and streamed live.

\---

## Features

* **Live flight search** via the Duffel API, with real OAuth, offer ranking, and budget-cap-aware filtering
* **Real activity discovery** via OpenTripMap, enriched and curated into a day-by-day plan by an LLM (Gemini), with a multi-model fallback chain for resilience
* **Adaptive budget re-planning** — the system detects overages and autonomously re-queries the responsible agent with a tighter budget, up to 2 attempts
* **Real-time agent execution streaming** over WebSocket — watch each agent start, succeed, or trigger a re-plan live, with JWT-authenticated, trip-ownership-scoped connections
* **JWT authentication** with BCrypt-hashed passwords and user-scoped trip history (My Trips view, full itinerary + agent execution log per saved trip)
* **Full observability** — every agent invocation (input, output, status, real-vs-mock, fallback reason) is logged to Postgres, independent of whether it succeeded or fell back

\---

## Integration status — what's actually live vs. simulated

Being upfront about this matters more than it sounds like it should, so here's the honest breakdown:

|Integration|Status|Notes|
|-|-|-|
|**Flights** (Duffel)|✅ Live|Real OAuth + offer search against Duffel's test environment|
|**Hotels** (Duffel Stays)|⚠️ Mock fallback|Duffel Stays requires a sales-approved account (`403: feature not enabled`); falls back to a tagged, budget-aware mock provider|
|**Activities** (OpenTripMap)|✅ Live|Real points-of-interest, geocoded correctly from IATA airport codes|
|**Itinerary planning** (Gemini)|✅ Live|LLM-generated day-by-day plan, JSON-schema validated, with a model fallback chain for reliability|

Every agent tags its own output with `is\_mock: true/false` and, on fallback, logs the exact reason to `agent\_runs.error\_message` — so "real vs. simulated" is never ambiguous, even in the raw data.

\---

## Setup

### Prerequisites

* Docker Desktop
* API keys (all free tiers, no credit card required for OpenTripMap/Gemini; Duffel requires signup but no card for test mode):

  * [Duffel](https://duffel.com) — test-mode access token
  * [OpenTripMap](https://dev.opentripmap.com) — free API key
  * [Gemini](https://aistudio.google.com/apikey) — free API key

### Run it

```bash
git clone https://github.com/RutujaPawale/Multi-Agent-Travel-Planner
cd multi-agent-travel-planner
cp .env.example .env
# edit .env and fill in your API keys
docker compose up --build
```

|Service|URL|
|-|-|
|Dashboard|http://localhost:3000|
|API (Spring Boot)|http://localhost:8080|
|Agent service docs|http://localhost:8000/docs|

### Required `.env` variables

```env
DUFFEL\_API\_KEY=duffel\_test\_...
FLIGHT\_PROVIDER=duffel        # or 'mock'
HOTEL\_PROVIDER=duffel         # or 'mock'
HOTEL\_BUDGET\_PCT=35.0

OPENTRIPMAP\_API\_KEY=...
ACTIVITY\_PROVIDER=opentripmap # or 'mock'
ACTIVITY\_BUDGET\_PCT=20.0

LLM\_PROVIDER=gemini
LLM\_API\_KEY=...
LLM\_MODEL=gemini-flash-latest # alias, avoids model-deprecation issues

JWT\_SECRET=<long random string>

POSTGRES\_DB=travel\_planner
POSTGRES\_USER=postgres
POSTGRES\_PASSWORD=postgres
```

If any key is missing, that agent automatically falls back to mock data rather than failing the whole pipeline — the system is designed to degrade gracefully.

\---

## Try it

1. **Submit a well-funded trip** (e.g. JFK → CDG, $1500+ budget) to see a clean, single-pass run — all agents succeed, no re-planning needed.
2. **Submit a tight-budget trip** (e.g. JFK → CDG, $700 budget) to watch the Budget Agent trigger live re-planning — the WebSocket feed will show the Flight Agent getting re-queried with progressively lower caps in real time.
3. **Sign up, save a trip, log in as a second user** — confirm you can't see or access the first user's trips (403 on cross-user access, enforced on both REST and WebSocket endpoints).

\---

## Challenges \& how they were solved

Building this surfaced several real integration and debugging problems — documenting them here because the debugging was as instructive as the build itself.

* **Amadeus Self-Service was decommissioned mid-build.** The originally planned flight/hotel provider shut down its developer portal entirely. Solution: refactored to a `FlightProvider`/`HotelProvider` abstract-interface pattern with pluggable implementations (`DuffelProvider`, `MockProvider`), selected via env var — meaning a future provider swap is a config change, not a rewrite.
* **A budget cap was logged but silently not enforced.** Early versions of the re-planning loop passed a `budget` parameter into the flight search, but the underlying provider never actually filtered offers against it — it just returned the cheapest 3 regardless. Caught by noticing the overage amount *increasing* between re-plan attempts instead of decreasing. Fixed by explicitly filtering offers under the cap, with a transparent `FALLBACK\_CHEAPEST\_AVAILABLE` tag when no offer qualifies.
* **Geocoding bug silently fetched the wrong city.** The Activity Agent's location resolver passed IATA airport codes (e.g. `CDG`) directly into a general place-name search, which matched an unrelated city (Córdoba, Argentina) instead of Paris. Fixed with a proper IATA-to-city mapping layer, resolved *before* the geocoding call.
* **The Gemini model name went stale three times in one session** (`gemini-1.5-flash` deprecated → `gemini-2.5-flash` restricted for new accounts → `gemini-3.8-flash` overloaded/quota-limited). Solution: pinned to the `gemini-flash-latest` alias instead of a specific version, and built a retry-with-backoff + multi-model fallback chain so a single provider hiccup doesn't fail the whole trip.
* **The WebSocket endpoint was initially unauthenticated.** Anyone who knew a `tripId` could connect to its live event stream. Closed by adding JWT validation and trip-ownership checks to the WebSocket handshake itself (not just the REST API), verified with an automated test suite covering missing/invalid/wrong-user tokens.

\---

## Tech stack

**Backend (orchestration):** Python, FastAPI, LangGraph
**Backend (API/persistence):** Java, Spring Boot, Spring Security, JWT, JPA
**Frontend:** React, TypeScript, Vite
**Database:** PostgreSQL
**Infra:** Docker, Docker Compose
**External APIs:** Duffel (flights/hotels), OpenTripMap (points of interest), Gemini (LLM itinerary planning)

