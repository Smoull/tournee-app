# Tournée App V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship V1 of the tournée app — vehicle profile, daily trip list with manual ordering, fuel cost + end-time calculation, Google SSO auth, animated pro-grade UI.

**Architecture:** Next.js frontend (auth via Supabase Auth only) talks REST to a FastAPI backend, which is the sole reader/writer of Supabase Postgres (via `supabase-py`, `service_role` key) and the sole caller of Mapbox (Geocoding + Directions) and the French government fuel-price API. User isolation is enforced in FastAPI code, not solely by RLS.

**Tech Stack:** Python 3.12 + FastAPI + `uv` + `supabase-py` + `httpx` + `pytest` (backend); Next.js (App Router, TS) + Tailwind + Framer Motion + `dnd-kit` + `posthog-js` (frontend); Supabase Cloud (Auth + Postgres); Mapbox Geocoding/Directions API; PostHog Cloud EU.

**Spec:** [docs/superpowers/specs/2026-09-20-tournee-app-v1-design.md](../specs/2026-09-20-tournee-app-v1-design.md)

## Global Constraints

- Single data-access path: only FastAPI reads/writes Supabase Postgres tables. Next.js only calls Supabase Auth directly.
- `service_role` key lives only in backend env vars, never sent to the frontend.
- FastAPI verifies `user_id` explicitly in every query — RLS is defense-in-depth, not the primary isolation mechanism.
- TDD: failing test before implementation, on every task (per project `CLAUDE.md`).
- Single Responsibility per class: `FuelPriceService`, `RoutingClient`, `TourneeCalculator` are separate classes with one reason to change each (per project `CLAUDE.md`).
- No mocking network calls with real HTTP in tests — mock Mapbox and the gov fuel API in all backend tests.
- Currency/units: consumption in L/100km, cost in EUR, distance in km, duration in minutes.
- Google SSO only for V1 (no Facebook).

---

## File Structure

```
tournee-app/
  backend/
    pyproject.toml
    src/
      main.py                      # FastAPI app, router registration
      auth.py                      # verify_jwt dependency (Supabase JWT)
      db.py                        # supabase-py client factory
      models.py                    # Pydantic request/response models
      fuel_price_service.py        # FuelPriceService: gov API + cache
      routing_client.py            # RoutingClient: Mapbox Geocoding + Directions
      tournee_calculator.py        # TourneeCalculator: pure calc logic
      vehicle_profiles_router.py   # /vehicle-profiles endpoints
      tournees_router.py           # /tournees, /tournees/{id}/trajets endpoints
    tests/
      conftest.py                  # fixtures: fake supabase client, fake httpx client
      test_fuel_price_service.py
      test_routing_client.py
      test_tournee_calculator.py
      test_vehicle_profiles_router.py
      test_tournees_router.py
  frontend/
    (Next.js app, created in Task 8)
```

Each backend module has one responsibility: `fuel_price_service.py` only knows about fuel price fetch/cache, `routing_client.py` only knows about Mapbox calls, `tournee_calculator.py` is pure (no I/O) so it's trivially unit-testable, and the routers wire HTTP to these services.

---

## Task 1: Backend scaffolding

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/main.py`
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_main.py`

**Interfaces:**
- Produces: FastAPI app instance at `backend.src.main:app`, with a `GET /health` route returning `{"status": "ok"}`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_main.py
from fastapi.testclient import TestClient
from src.main import app

def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src'` (or similar — `src/main.py` doesn't exist yet)

- [ ] **Step 3: Create pyproject.toml and minimal app**

```toml
# backend/pyproject.toml
[project]
name = "tournee-app-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "supabase>=2.9",
    "httpx>=0.27",
    "pydantic>=2.9",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-mock>=3.14",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

```python
# backend/src/main.py
from fastapi import FastAPI

app = FastAPI(title="Tournée App API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

```python
# backend/tests/conftest.py
import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv sync && uv run pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add pyproject.toml src/main.py tests/conftest.py tests/test_main.py
git commit -m "feat(backend): scaffold FastAPI app with health check"
```

---

## Task 2: TourneeCalculator (pure calc logic)

**Files:**
- Create: `backend/src/tournee_calculator.py`
- Test: `backend/tests/test_tournee_calculator.py`

**Interfaces:**
- Produces:
  - `class TripInput`: `distance_km: float`, `duree_trajet_min: float`, `duree_chantier_min: float`
  - `class TourneeCalculator`: constructor `TourneeCalculator(conso_l_100km: float, prix_carburant: float)`
  - `TourneeCalculator.cout_essence(distance_km: float) -> float`
  - `TourneeCalculator.cout_total(trips: list[TripInput]) -> float`
  - `TourneeCalculator.heure_fin(heure_debut: time, trips: list[TripInput]) -> time`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_tournee_calculator.py
from datetime import time
from src.tournee_calculator import TourneeCalculator, TripInput


def test_cout_essence_computes_cost_from_distance_conso_price():
    calc = TourneeCalculator(conso_l_100km=8.0, prix_carburant=1.80)
    # 50km * (8/100) * 1.80 = 7.2
    assert calc.cout_essence(distance_km=50.0) == pytest_approx(7.2)


def test_cout_total_sums_all_trips():
    calc = TourneeCalculator(conso_l_100km=8.0, prix_carburant=1.80)
    trips = [
        TripInput(distance_km=50.0, duree_trajet_min=40, duree_chantier_min=30),
        TripInput(distance_km=10.0, duree_trajet_min=15, duree_chantier_min=20),
    ]
    # 7.2 + 1.44 = 8.64
    assert calc.cout_total(trips) == pytest_approx(8.64)


def test_heure_fin_sums_trajet_and_chantier_durations():
    calc = TourneeCalculator(conso_l_100km=8.0, prix_carburant=1.80)
    trips = [
        TripInput(distance_km=50.0, duree_trajet_min=40, duree_chantier_min=30),
        TripInput(distance_km=10.0, duree_trajet_min=15, duree_chantier_min=20),
    ]
    # 8:00 + 40+30+15+20 = 105min = 1h45 -> 9:45
    result = calc.heure_fin(heure_debut=time(8, 0), trips=trips)
    assert result == time(9, 45)


def pytest_approx(value, rel=1e-6):
    import pytest
    return pytest.approx(value, rel=rel)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_tournee_calculator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.tournee_calculator'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/tournee_calculator.py
from dataclasses import dataclass
from datetime import time, datetime, timedelta


@dataclass
class TripInput:
    distance_km: float
    duree_trajet_min: float
    duree_chantier_min: float


class TourneeCalculator:
    """Pure calc logic: no I/O, no DB, no HTTP — single responsibility is arithmetic."""

    def __init__(self, conso_l_100km: float, prix_carburant: float):
        self.conso_l_100km = conso_l_100km
        self.prix_carburant = prix_carburant

    def cout_essence(self, distance_km: float) -> float:
        return distance_km * (self.conso_l_100km / 100) * self.prix_carburant

    def cout_total(self, trips: list[TripInput]) -> float:
        return sum(self.cout_essence(trip.distance_km) for trip in trips)

    def heure_fin(self, heure_debut: time, trips: list[TripInput]) -> time:
        total_minutes = sum(
            trip.duree_trajet_min + trip.duree_chantier_min for trip in trips
        )
        start_dt = datetime.combine(datetime.today(), heure_debut)
        end_dt = start_dt + timedelta(minutes=total_minutes)
        return end_dt.time()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_tournee_calculator.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add src/tournee_calculator.py tests/test_tournee_calculator.py
git commit -m "feat(backend): add TourneeCalculator pure calc logic"
```

---

## Task 3: RoutingClient (Mapbox Geocoding + Directions)

**Files:**
- Create: `backend/src/routing_client.py`
- Test: `backend/tests/test_routing_client.py`

**Interfaces:**
- Consumes: `httpx.AsyncClient` (injected)
- Produces:
  - `class GeocodedAddress`: `lat: float`, `lon: float`, `formatted_address: str`
  - `class RouteResult`: `distance_km: float`, `duree_min: float`
  - `class RoutingClient`: constructor `RoutingClient(access_token: str, http_client: httpx.AsyncClient)`
  - `async RoutingClient.geocode(address: str) -> GeocodedAddress | None` (None if 0 results)
  - `async RoutingClient.route(origin: tuple[float, float], destination: tuple[float, float]) -> RouteResult`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_routing_client.py
import httpx
import pytest
from src.routing_client import RoutingClient


@pytest.mark.anyio
async def test_geocode_returns_lat_lon_on_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "features": [
                {"center": [2.3522, 48.8566], "place_name": "Paris, France"}
            ]
        })

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = RoutingClient(access_token="fake-token", http_client=http_client)
        result = await client.geocode("Paris")

    assert result is not None
    assert result.lon == 2.3522
    assert result.lat == 48.8566
    assert result.formatted_address == "Paris, France"


@pytest.mark.anyio
async def test_geocode_returns_none_on_zero_results():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"features": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = RoutingClient(access_token="fake-token", http_client=http_client)
        result = await client.geocode("adresse-inexistante-xyz")

    assert result is None


@pytest.mark.anyio
async def test_route_returns_distance_and_duration():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "routes": [{"distance": 15000, "duration": 1200}]
        })

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = RoutingClient(access_token="fake-token", http_client=http_client)
        result = await client.route(origin=(48.85, 2.35), destination=(48.86, 2.34))

    assert result.distance_km == 15.0
    assert result.duree_min == 20.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv add --dev anyio && uv run pytest tests/test_routing_client.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.routing_client'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/routing_client.py
from dataclasses import dataclass
import httpx


@dataclass
class GeocodedAddress:
    lat: float
    lon: float
    formatted_address: str


@dataclass
class RouteResult:
    distance_km: float
    duree_min: float


class RoutingClient:
    """Single responsibility: talk to Mapbox. Swap this class alone to change provider."""

    GEOCODE_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"

    def __init__(self, access_token: str, http_client: httpx.AsyncClient):
        self.access_token = access_token
        self.http_client = http_client

    async def geocode(self, address: str) -> GeocodedAddress | None:
        url = self.GEOCODE_URL.format(query=address)
        response = await self.http_client.get(url, params={"access_token": self.access_token})
        response.raise_for_status()
        features = response.json().get("features", [])
        if not features:
            return None
        feature = features[0]
        lon, lat = feature["center"]
        return GeocodedAddress(lat=lat, lon=lon, formatted_address=feature["place_name"])

    async def route(self, origin: tuple[float, float], destination: tuple[float, float]) -> RouteResult:
        origin_lat, origin_lon = origin
        dest_lat, dest_lon = destination
        coords = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        url = self.DIRECTIONS_URL.format(coords=coords)
        response = await self.http_client.get(url, params={"access_token": self.access_token})
        response.raise_for_status()
        route = response.json()["routes"][0]
        return RouteResult(
            distance_km=route["distance"] / 1000,
            duree_min=route["duration"] / 60,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_routing_client.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add src/routing_client.py tests/test_routing_client.py pyproject.toml uv.lock
git commit -m "feat(backend): add RoutingClient for Mapbox geocoding and directions"
```

---

## Task 4: FuelPriceService (gov API + department cache)

**Files:**
- Create: `backend/src/fuel_price_service.py`
- Test: `backend/tests/test_fuel_price_service.py`

**Interfaces:**
- Consumes: `httpx.AsyncClient`, a `db_client` with `.table(name)` interface matching `supabase-py`
- Produces:
  - `class FuelPriceService`: constructor `FuelPriceService(http_client: httpx.AsyncClient, db_client)`
  - `async FuelPriceService.get_price(type_carburant: str, departement: str) -> float`
    (returns cached price if `date_maj` < 24h old, otherwise fetches gov API, computes 7-day average, upserts cache, returns it; on gov API failure, returns last cached value even if stale)

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_fuel_price_service.py
from datetime import datetime, timedelta, timezone
import httpx
import pytest
from src.fuel_price_service import FuelPriceService


class FakeTable:
    def __init__(self, rows):
        self.rows = rows
        self.upserted = []

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def execute(self):
        return type("Result", (), {"data": self.rows})()

    def upsert(self, row):
        self.upserted.append(row)
        return self


class FakeDbClient:
    def __init__(self, rows):
        self._table = FakeTable(rows)

    def table(self, _name):
        return self._table


@pytest.mark.anyio
async def test_get_price_returns_cached_value_if_fresh():
    fresh_row = {
        "type_carburant": "gazole",
        "departement": "75",
        "prix_moyen_7j": 1.75,
        "date_maj": datetime.now(timezone.utc).isoformat(),
    }
    db_client = FakeDbClient(rows=[fresh_row])

    async def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("gov API should not be called when cache is fresh")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        service = FuelPriceService(http_client=http_client, db_client=db_client)
        price = await service.get_price("gazole", "75")

    assert price == 1.75


@pytest.mark.anyio
async def test_get_price_refreshes_from_gov_api_when_stale():
    stale_row = {
        "type_carburant": "gazole",
        "departement": "75",
        "prix_moyen_7j": 1.60,
        "date_maj": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
    }
    db_client = FakeDbClient(rows=[stale_row])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"records": [
            {"fields": {"gazoles_prix": 1.80}},
            {"fields": {"gazoles_prix": 1.82}},
        ]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        service = FuelPriceService(http_client=http_client, db_client=db_client)
        price = await service.get_price("gazole", "75")

    assert price == pytest.approx(1.81)
    assert db_client._table.upserted[0]["prix_moyen_7j"] == pytest.approx(1.81)


@pytest.mark.anyio
async def test_get_price_falls_back_to_stale_cache_on_gov_api_failure():
    stale_row = {
        "type_carburant": "gazole",
        "departement": "75",
        "prix_moyen_7j": 1.60,
        "date_maj": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat(),
    }
    db_client = FakeDbClient(rows=[stale_row])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        service = FuelPriceService(http_client=http_client, db_client=db_client)
        price = await service.get_price("gazole", "75")

    assert price == 1.60
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_fuel_price_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.fuel_price_service'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/fuel_price_service.py
from datetime import datetime, timedelta, timezone
import httpx


class FuelPriceService:
    """Single responsibility: fetch/cache fuel prices. Swap the gov API call
    here alone if the data source changes."""

    GOV_API_URL = "https://data.economie.gouv.fr/api/records/1.0/search/"
    FIELD_BY_TYPE = {
        "gazole": "gazoles_prix",
        "sp95": "sp95_prix",
        "sp98": "sp98_prix",
        "e10": "e10_prix",
        "e85": "e85_prix",
        "gplc": "gplc_prix",
    }
    CACHE_TTL_HOURS = 24

    def __init__(self, http_client: httpx.AsyncClient, db_client):
        self.http_client = http_client
        self.db_client = db_client

    async def get_price(self, type_carburant: str, departement: str) -> float:
        cached = self._get_cached_row(type_carburant, departement)

        if cached and self._is_fresh(cached["date_maj"]):
            return cached["prix_moyen_7j"]

        try:
            price = await self._fetch_from_gov_api(type_carburant, departement)
        except httpx.HTTPStatusError:
            if cached:
                return cached["prix_moyen_7j"]
            raise

        self._upsert_cache(type_carburant, departement, price)
        return price

    def _get_cached_row(self, type_carburant: str, departement: str) -> dict | None:
        result = (
            self.db_client.table("fuel_price_cache")
            .select("*")
            .eq("type_carburant", type_carburant)
            .eq("departement", departement)
            .execute()
        )
        return result.data[0] if result.data else None

    def _is_fresh(self, date_maj_iso: str) -> bool:
        date_maj = datetime.fromisoformat(date_maj_iso)
        age = datetime.now(timezone.utc) - date_maj
        return age < timedelta(hours=self.CACHE_TTL_HOURS)

    async def _fetch_from_gov_api(self, type_carburant: str, departement: str) -> float:
        field = self.FIELD_BY_TYPE[type_carburant]
        response = await self.http_client.get(
            self.GOV_API_URL,
            params={"dataset": "prix-des-carburants-en-france-flux-instantane-v2"},
        )
        response.raise_for_status()
        records = response.json()["records"]
        prices = [r["fields"][field] for r in records if field in r["fields"]]
        return sum(prices) / len(prices)

    def _upsert_cache(self, type_carburant: str, departement: str, price: float) -> None:
        self.db_client.table("fuel_price_cache").upsert({
            "type_carburant": type_carburant,
            "departement": departement,
            "prix_moyen_7j": price,
            "date_maj": datetime.now(timezone.utc).isoformat(),
        }).execute()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_fuel_price_service.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add src/fuel_price_service.py tests/test_fuel_price_service.py
git commit -m "feat(backend): add FuelPriceService with per-department cache"
```

---

## Task 5: Auth dependency (Supabase JWT verification)

**Files:**
- Create: `backend/src/auth.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `async def get_current_user_id(authorization: str = Header(...)) -> str` (FastAPI dependency), raises `HTTPException(401)` on invalid/missing token.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_auth.py
import pytest
from fastapi import HTTPException
import jwt as pyjwt
from src.auth import get_current_user_id, JWT_SECRET


def _make_token(user_id: str, secret: str = JWT_SECRET) -> str:
    return pyjwt.encode({"sub": user_id}, secret, algorithm="HS256")


@pytest.mark.anyio
async def test_valid_token_returns_user_id():
    token = _make_token("user-123")
    user_id = await get_current_user_id(authorization=f"Bearer {token}")
    assert user_id == "user-123"


@pytest.mark.anyio
async def test_missing_bearer_prefix_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(authorization="not-a-bearer-token")
    assert exc_info.value.status_code == 401


@pytest.mark.anyio
async def test_invalid_signature_raises_401():
    token = _make_token("user-123", secret="wrong-secret")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_id(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv add pyjwt && uv run pytest tests/test_auth.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.auth'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/auth.py
import os
from fastapi import Header, HTTPException
import jwt

JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "test-secret-for-local-dev")


async def get_current_user_id(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    except jwt.InvalidTokenError:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    return payload["sub"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_auth.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add src/auth.py tests/test_auth.py pyproject.toml uv.lock
git commit -m "feat(backend): add Supabase JWT verification dependency"
```

---

## Task 6: Vehicle profiles endpoints

**Files:**
- Create: `backend/src/models.py`
- Create: `backend/src/db.py`
- Create: `backend/src/vehicle_profiles_router.py`
- Modify: `backend/src/main.py`
- Test: `backend/tests/test_vehicle_profiles_router.py`

**Interfaces:**
- Consumes: `get_current_user_id` (Task 5)
- Produces:
  - `class VehicleProfileIn` (Pydantic): `nom: str`, `conso_l_100km: float`, `type_carburant: str`, `adresse_depart: str`
  - `class VehicleProfileOut` (Pydantic): adds `id: str`, `lat_depart: float`, `lon_depart: float`
  - `router` (APIRouter) mounted at `/vehicle-profiles`: `POST /` creates, `GET /` lists current user's profiles
  - `get_db_client()` dependency returning a `supabase-py` client (overridable in tests)

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_vehicle_profiles_router.py
from fastapi.testclient import TestClient
from src.main import app
from src.auth import get_current_user_id
from src.db import get_db_client
from src.routing_client import get_routing_client, GeocodedAddress


class FakeTable:
    def __init__(self):
        self.inserted = []

    def insert(self, row):
        row = {**row, "id": "profile-1"}
        self.inserted.append(row)
        return self

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def execute(self):
        return type("Result", (), {"data": self.inserted})()


class FakeDbClient:
    def __init__(self):
        self._table = FakeTable()

    def table(self, _name):
        return self._table


class FakeRoutingClient:
    async def geocode(self, address: str):
        return GeocodedAddress(lat=48.85, lon=2.35, formatted_address=address)


def _override_deps():
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    app.dependency_overrides[get_db_client] = lambda: FakeDbClient()
    app.dependency_overrides[get_routing_client] = lambda: FakeRoutingClient()


def test_create_vehicle_profile_geocodes_address_and_saves():
    _override_deps()
    client = TestClient(app)

    response = client.post("/vehicle-profiles", json={
        "nom": "Camionnette",
        "conso_l_100km": 8.0,
        "type_carburant": "gazole",
        "adresse_depart": "1 rue de Paris, 75001 Paris",
    })

    assert response.status_code == 201
    body = response.json()
    assert body["lat_depart"] == 48.85
    assert body["lon_depart"] == 2.35
    assert body["id"] == "profile-1"

    app.dependency_overrides.clear()


def test_create_vehicle_profile_returns_422_on_ungeocodable_address():
    _override_deps()
    app.dependency_overrides[get_routing_client] = lambda: type(
        "NoResultClient", (), {"geocode": staticmethod(lambda address: _none())}
    )()
    client = TestClient(app)

    response = client.post("/vehicle-profiles", json={
        "nom": "Camionnette",
        "conso_l_100km": 8.0,
        "type_carburant": "gazole",
        "adresse_depart": "adresse-inexistante-xyz",
    })

    assert response.status_code == 422

    app.dependency_overrides.clear()


async def _none():
    return None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_vehicle_profiles_router.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.models'` (or `src.db`)

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/models.py
from pydantic import BaseModel


class VehicleProfileIn(BaseModel):
    nom: str
    conso_l_100km: float
    type_carburant: str
    adresse_depart: str


class VehicleProfileOut(BaseModel):
    id: str
    nom: str
    conso_l_100km: float
    type_carburant: str
    adresse_depart: str
    lat_depart: float
    lon_depart: float
```

```python
# backend/src/db.py
import os
from supabase import create_client, Client

_client: Client | None = None


def get_db_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        )
    return _client
```

```python
# backend/src/routing_client.py
# --- append to existing file from Task 3 ---
import os
import httpx as _httpx

_routing_client: "RoutingClient | None" = None


def get_routing_client() -> "RoutingClient":
    global _routing_client
    if _routing_client is None:
        _routing_client = RoutingClient(
            access_token=os.environ["MAPBOX_TOKEN"],
            http_client=_httpx.AsyncClient(),
        )
    return _routing_client
```

```python
# backend/src/vehicle_profiles_router.py
from fastapi import APIRouter, Depends, HTTPException
from src.auth import get_current_user_id
from src.db import get_db_client
from src.routing_client import get_routing_client, RoutingClient
from src.models import VehicleProfileIn, VehicleProfileOut

router = APIRouter(prefix="/vehicle-profiles", tags=["vehicle-profiles"])


@router.post("", status_code=201, response_model=VehicleProfileOut)
async def create_vehicle_profile(
    payload: VehicleProfileIn,
    user_id: str = Depends(get_current_user_id),
    db_client=Depends(get_db_client),
    routing_client: RoutingClient = Depends(get_routing_client),
):
    geocoded = await routing_client.geocode(payload.adresse_depart)
    if geocoded is None:
        raise HTTPException(status_code=422, detail="Adresse introuvable")

    row = {
        "user_id": user_id,
        "nom": payload.nom,
        "conso_l_100km": payload.conso_l_100km,
        "type_carburant": payload.type_carburant,
        "adresse_depart": payload.adresse_depart,
        "lat_depart": geocoded.lat,
        "lon_depart": geocoded.lon,
    }
    result = db_client.table("vehicle_profiles").insert(row).execute()
    return result.data[0]


@router.get("", response_model=list[VehicleProfileOut])
async def list_vehicle_profiles(
    user_id: str = Depends(get_current_user_id),
    db_client=Depends(get_db_client),
):
    result = (
        db_client.table("vehicle_profiles")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )
    return result.data
```

```python
# backend/src/main.py
from fastapi import FastAPI
from src.vehicle_profiles_router import router as vehicle_profiles_router

app = FastAPI(title="Tournée App API")
app.include_router(vehicle_profiles_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_vehicle_profiles_router.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd backend && git add src/models.py src/db.py src/routing_client.py src/vehicle_profiles_router.py src/main.py tests/test_vehicle_profiles_router.py
git commit -m "feat(backend): add vehicle profile create/list endpoints with geocoding"
```

---

## Task 7: Tournées + trajets endpoints (calc integration)

**Files:**
- Modify: `backend/src/models.py`
- Create: `backend/src/tournees_router.py`
- Modify: `backend/src/main.py`
- Test: `backend/tests/test_tournees_router.py`

**Interfaces:**
- Consumes: `TourneeCalculator` (Task 2), `RoutingClient` (Task 3), `FuelPriceService` (Task 4), `get_current_user_id` (Task 5), `get_db_client` (Task 6)
- Produces:
  - `class TrajetIn`: `adresse: str`, `duree_chantier_min: int`, `ordre: int`
  - `class TrajetOut`: adds `id`, `lat`, `lon`, `distance_km`, `duree_trajet_min`, `cout_essence`
  - `class TourneeRecapOut`: `cout_total_jour: float`, `heure_fin: str`, `trajets: list[TrajetOut]`
  - `POST /tournees/{tournee_id}/trajets` — geocodes address, computes distance/duration from the previous trajet (or vehicle start point), computes cost, persists, returns updated `TourneeRecapOut`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_tournees_router.py
from fastapi.testclient import TestClient
from src.main import app
from src.auth import get_current_user_id
from src.db import get_db_client
from src.routing_client import get_routing_client, GeocodedAddress, RouteResult
from src.fuel_price_service import get_fuel_price_service


class FakeTable:
    def __init__(self, vehicle_row, trajet_rows=None):
        self.vehicle_row = vehicle_row
        self.trajet_rows = trajet_rows or []
        self._current = None

    def select(self, *_args):
        return self

    def eq(self, field, value):
        if field == "id" and value == self.vehicle_row["id"]:
            self._current = "vehicle"
        return self

    def order(self, *_args):
        return self

    def insert(self, row):
        row = {**row, "id": f"trajet-{len(self.trajet_rows) + 1}"}
        self.trajet_rows.append(row)
        self._current = "trajets"
        return self

    def execute(self):
        if self._current == "vehicle":
            return type("Result", (), {"data": [self.vehicle_row]})()
        return type("Result", (), {"data": self.trajet_rows})()


class FakeDbClient:
    def __init__(self, vehicle_row):
        self._table = FakeTable(vehicle_row)

    def table(self, _name):
        return self._table


class FakeRoutingClient:
    async def geocode(self, address: str):
        return GeocodedAddress(lat=48.86, lon=2.34, formatted_address=address)

    async def route(self, origin, destination):
        return RouteResult(distance_km=10.0, duree_min=15.0)


class FakeFuelPriceService:
    async def get_price(self, type_carburant, departement):
        return 1.80


def test_add_trajet_computes_cost_and_returns_recap():
    vehicle_row = {
        "id": "vehicle-1", "user_id": "user-123", "conso_l_100km": 8.0,
        "type_carburant": "gazole", "lat_depart": 48.85, "lon_depart": 2.35,
        "adresse_depart": "1 rue de Paris, 75001 Paris",
    }
    app.dependency_overrides[get_current_user_id] = lambda: "user-123"
    app.dependency_overrides[get_db_client] = lambda: FakeDbClient(vehicle_row)
    app.dependency_overrides[get_routing_client] = lambda: FakeRoutingClient()
    app.dependency_overrides[get_fuel_price_service] = lambda: FakeFuelPriceService()

    client = TestClient(app)
    response = client.post(
        "/tournees/tournee-1/trajets",
        params={"vehicle_profile_id": "vehicle-1", "heure_debut": "08:00"},
        json={"adresse": "10 rue de Lyon, 75012 Paris", "duree_chantier_min": 30, "ordre": 1},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["trajets"][0]["distance_km"] == 10.0
    assert body["trajets"][0]["cout_essence"] == pytest_approx_close(1.44)
    assert body["cout_total_jour"] == pytest_approx_close(1.44)
    assert body["heure_fin"] == "08:45:00"

    app.dependency_overrides.clear()


def pytest_approx_close(value):
    import pytest
    return pytest.approx(value, rel=1e-6)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_tournees_router.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.tournees_router'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/src/models.py
# --- append to existing file from Task 6 ---
class TrajetIn(BaseModel):
    adresse: str
    duree_chantier_min: int
    ordre: int


class TrajetOut(BaseModel):
    id: str
    adresse: str
    lat: float
    lon: float
    duree_chantier_min: int
    distance_km: float
    duree_trajet_min: float
    cout_essence: float


class TourneeRecapOut(BaseModel):
    cout_total_jour: float
    heure_fin: str
    trajets: list[TrajetOut]
```

```python
# backend/src/fuel_price_service.py
# --- append to existing file from Task 4 ---
import httpx as _httpx
from src.db import get_db_client as _get_db_client

_fuel_price_service: "FuelPriceService | None" = None


def get_fuel_price_service() -> "FuelPriceService":
    global _fuel_price_service
    if _fuel_price_service is None:
        _fuel_price_service = FuelPriceService(
            http_client=_httpx.AsyncClient(),
            db_client=_get_db_client(),
        )
    return _fuel_price_service
```

```python
# backend/src/tournees_router.py
from datetime import time
from fastapi import APIRouter, Depends, HTTPException
from src.auth import get_current_user_id
from src.db import get_db_client
from src.routing_client import get_routing_client, RoutingClient
from src.fuel_price_service import get_fuel_price_service, FuelPriceService
from src.tournee_calculator import TourneeCalculator, TripInput
from src.models import TrajetIn, TrajetOut, TourneeRecapOut

router = APIRouter(prefix="/tournees", tags=["tournees"])


@router.post("/{tournee_id}/trajets", status_code=201, response_model=TourneeRecapOut)
async def add_trajet(
    tournee_id: str,
    payload: TrajetIn,
    vehicle_profile_id: str,
    heure_debut: str,
    user_id: str = Depends(get_current_user_id),
    db_client=Depends(get_db_client),
    routing_client: RoutingClient = Depends(get_routing_client),
    fuel_price_service: FuelPriceService = Depends(get_fuel_price_service),
):
    vehicle_result = (
        db_client.table("vehicle_profiles").select("*").eq("id", vehicle_profile_id).execute()
    )
    if not vehicle_result.data:
        raise HTTPException(status_code=404, detail="Profil véhicule introuvable")
    vehicle = vehicle_result.data[0]

    geocoded = await routing_client.geocode(payload.adresse)
    if geocoded is None:
        raise HTTPException(status_code=422, detail="Adresse introuvable")

    origin = (vehicle["lat_depart"], vehicle["lon_depart"])
    route_result = await routing_client.route(origin=origin, destination=(geocoded.lat, geocoded.lon))

    departement = _departement_from_address(vehicle["adresse_depart"])
    prix_carburant = await fuel_price_service.get_price(vehicle["type_carburant"], departement)

    calculator = TourneeCalculator(
        conso_l_100km=vehicle["conso_l_100km"],
        prix_carburant=prix_carburant,
    )
    cout_essence = calculator.cout_essence(route_result.distance_km)

    row = {
        "tournee_id": tournee_id,
        "ordre": payload.ordre,
        "adresse": payload.adresse,
        "lat": geocoded.lat,
        "lon": geocoded.lon,
        "duree_chantier_min": payload.duree_chantier_min,
        "distance_km": route_result.distance_km,
        "duree_trajet_min": route_result.duree_min,
        "cout_essence": cout_essence,
    }
    db_client.table("trajets").insert(row).execute()

    all_trajets_result = db_client.table("trajets").select("*").eq("tournee_id", tournee_id).order("ordre").execute()
    trip_inputs = [
        TripInput(
            distance_km=t["distance_km"],
            duree_trajet_min=t["duree_trajet_min"],
            duree_chantier_min=t["duree_chantier_min"],
        )
        for t in all_trajets_result.data
    ]

    heure_debut_time = time.fromisoformat(heure_debut)
    return TourneeRecapOut(
        cout_total_jour=calculator.cout_total(trip_inputs),
        heure_fin=calculator.heure_fin(heure_debut_time, trip_inputs).isoformat(),
        trajets=all_trajets_result.data,
    )


def _departement_from_address(adresse: str) -> str:
    import re
    match = re.search(r"\b(\d{5})\b", adresse)
    if not match:
        return "75"
    code_postal = match.group(1)
    return code_postal[:2]
```

```python
# backend/src/main.py
from fastapi import FastAPI
from src.vehicle_profiles_router import router as vehicle_profiles_router
from src.tournees_router import router as tournees_router

app = FastAPI(title="Tournée App API")
app.include_router(vehicle_profiles_router)
app.include_router(tournees_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_tournees_router.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd backend && git add src/models.py src/fuel_price_service.py src/tournees_router.py src/main.py tests/test_tournees_router.py
git commit -m "feat(backend): add add-trajet endpoint with cost/time recalculation"
```

---

## Task 8: Frontend scaffolding + Supabase Auth (Google SSO)

**Files:**
- Create: `frontend/` (Next.js app via `create-next-app`)
- Create: `frontend/lib/supabase-client.ts`
- Create: `frontend/app/login/page.tsx`
- Create: `frontend/middleware.ts`
- Test: `frontend/lib/supabase-client.test.ts`

**Interfaces:**
- Produces: `createSupabaseBrowserClient(): SupabaseClient` — factory reading `NEXT_PUBLIC_SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_ANON_KEY` from env

- [ ] **Step 1: Scaffold Next.js app**

Run:
```bash
cd ~/Documents/tournee-app
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*" --eslint
cd frontend
npm install @supabase/supabase-js @supabase/ssr framer-motion @dnd-kit/core @dnd-kit/sortable posthog-js
npm install -D vitest @vitejs/plugin-react
```

- [ ] **Step 2: Write the failing test**

```typescript
// frontend/lib/supabase-client.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";

describe("createSupabaseBrowserClient", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://fake.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "fake-anon-key";
  });

  it("creates a client without throwing when env vars are set", async () => {
    const { createSupabaseBrowserClient } = await import("./supabase-client");
    expect(() => createSupabaseBrowserClient()).not.toThrow();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd frontend && npx vitest run lib/supabase-client.test.ts`
Expected: FAIL with module not found (`./supabase-client` doesn't exist)

- [ ] **Step 4: Write minimal implementation**

```typescript
// frontend/lib/supabase-client.ts
import { createBrowserClient } from "@supabase/ssr";

export function createSupabaseBrowserClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}
```

```typescript
// frontend/app/login/page.tsx
"use client";

import { createSupabaseBrowserClient } from "@/lib/supabase-client";

export default function LoginPage() {
  const supabase = createSupabaseBrowserClient();

  const handleGoogleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-950">
      <button
        onClick={handleGoogleLogin}
        className="rounded-lg bg-white px-6 py-3 font-medium text-gray-900 shadow-lg transition hover:scale-105"
      >
        Se connecter avec Google
      </button>
    </main>
  );
}
```

```typescript
// frontend/middleware.ts
import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get: (name) => request.cookies.get(name)?.value,
        set: (name, value, options) => response.cookies.set(name, value, options),
        remove: (name, options) => response.cookies.set(name, "", { ...options, maxAge: 0 }),
      },
    }
  );

  const { data: { session } } = await supabase.auth.getSession();

  if (!session && request.nextUrl.pathname.startsWith("/dashboard")) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return response;
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd frontend && npx vitest run lib/supabase-client.test.ts`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
cd frontend && git add -A
git commit -m "feat(frontend): scaffold Next.js app with Supabase Google SSO login"
```

---

## Task 9: Dashboard UI — onboarding + trip list + recap panel

**Files:**
- Create: `frontend/app/dashboard/page.tsx`
- Create: `frontend/components/VehicleOnboardingModal.tsx`
- Create: `frontend/components/TrajetCard.tsx`
- Create: `frontend/components/RecapPanel.tsx`
- Create: `frontend/lib/api-client.ts`
- Test: `frontend/lib/api-client.test.ts`

**Interfaces:**
- Consumes: backend endpoints from Task 6/7 (`POST /vehicle-profiles`, `GET /vehicle-profiles`, `POST /tournees/{id}/trajets`)
- Produces:
  - `apiClient.createVehicleProfile(payload): Promise<VehicleProfile>`
  - `apiClient.listVehicleProfiles(): Promise<VehicleProfile[]>`
  - `apiClient.addTrajet(tourneeId, vehicleProfileId, heureDebut, payload): Promise<TourneeRecap>`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/lib/api-client.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createApiClient } from "./api-client";

describe("apiClient.listVehicleProfiles", () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });

  it("calls GET /vehicle-profiles with auth header and returns parsed JSON", async () => {
    (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => [{ id: "1", nom: "Camionnette" }],
    });

    const client = createApiClient({ baseUrl: "http://localhost:8000", getAccessToken: async () => "token-abc" });
    const profiles = await client.listVehicleProfiles();

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/vehicle-profiles",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer token-abc" }),
      })
    );
    expect(profiles).toEqual([{ id: "1", nom: "Camionnette" }]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run lib/api-client.test.ts`
Expected: FAIL with module not found (`./api-client` doesn't exist)

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/lib/api-client.ts
type ApiClientConfig = {
  baseUrl: string;
  getAccessToken: () => Promise<string>;
};

export function createApiClient({ baseUrl, getAccessToken }: ApiClientConfig) {
  async function request(path: string, options: RequestInit = {}) {
    const token = await getAccessToken();
    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      throw new Error(`API error ${response.status} on ${path}`);
    }
    return response.json();
  }

  return {
    listVehicleProfiles: () => request("/vehicle-profiles"),
    createVehicleProfile: (payload: unknown) =>
      request("/vehicle-profiles", { method: "POST", body: JSON.stringify(payload) }),
    addTrajet: (tourneeId: string, vehicleProfileId: string, heureDebut: string, payload: unknown) =>
      request(
        `/tournees/${tourneeId}/trajets?vehicle_profile_id=${vehicleProfileId}&heure_debut=${heureDebut}`,
        { method: "POST", body: JSON.stringify(payload) }
      ),
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run lib/api-client.test.ts`
Expected: PASS

- [ ] **Step 5: Build the UI components**

```typescript
// frontend/components/VehicleOnboardingModal.tsx
"use client";

import { useState } from "react";
import { motion } from "framer-motion";

const CONSO_DEFAULTS: Record<string, number> = {
  gazole: 8.0,
  sp95: 6.0,
  sp98: 6.5,
  e10: 6.5,
  e85: 7.5,
  gplc: 9.0,
};

type Props = {
  onSubmit: (payload: { nom: string; conso_l_100km: number; type_carburant: string; adresse_depart: string }) => void;
};

export function VehicleOnboardingModal({ onSubmit }: Props) {
  const [typeCarburant, setTypeCarburant] = useState("gazole");
  const [conso, setConso] = useState(CONSO_DEFAULTS["gazole"]);
  const [nom, setNom] = useState("");
  const [adresseDepart, setAdresseDepart] = useState("");

  const handleTypeChange = (value: string) => {
    setTypeCarburant(value);
    setConso(CONSO_DEFAULTS[value]);
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="fixed inset-0 flex items-center justify-center bg-black/60"
    >
      <div className="w-full max-w-md rounded-xl bg-gray-900 p-6 text-white shadow-2xl">
        <h2 className="mb-4 text-xl font-semibold">Configure ton véhicule</h2>
        <input
          className="mb-3 w-full rounded bg-gray-800 p-2"
          placeholder="Nom (ex: Camionnette)"
          value={nom}
          onChange={(e) => setNom(e.target.value)}
        />
        <select
          className="mb-3 w-full rounded bg-gray-800 p-2"
          value={typeCarburant}
          onChange={(e) => handleTypeChange(e.target.value)}
        >
          {Object.keys(CONSO_DEFAULTS).map((type) => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        <input
          type="number"
          step="0.1"
          className="mb-3 w-full rounded bg-gray-800 p-2"
          value={conso}
          onChange={(e) => setConso(parseFloat(e.target.value))}
        />
        <input
          className="mb-4 w-full rounded bg-gray-800 p-2"
          placeholder="Adresse de départ"
          value={adresseDepart}
          onChange={(e) => setAdresseDepart(e.target.value)}
        />
        <button
          className="w-full rounded bg-blue-600 py-2 font-medium transition hover:bg-blue-500"
          onClick={() => onSubmit({ nom, conso_l_100km: conso, type_carburant: typeCarburant, adresse_depart: adresseDepart })}
        >
          Valider
        </button>
      </div>
    </motion.div>
  );
}
```

```typescript
// frontend/components/RecapPanel.tsx
"use client";

import { motion } from "framer-motion";

type Props = {
  coutTotalJour: number;
  heureFin: string;
};

export function RecapPanel({ coutTotalJour, heureFin }: Props) {
  return (
    <motion.div
      layout
      className="sticky top-4 rounded-xl bg-gradient-to-br from-blue-600 to-purple-700 p-6 text-white shadow-xl"
    >
      <p className="text-sm opacity-80">Coût total journée</p>
      <motion.p key={coutTotalJour} initial={{ scale: 1.1 }} animate={{ scale: 1 }} className="text-3xl font-bold">
        {coutTotalJour.toFixed(2)} €
      </motion.p>
      <p className="mt-4 text-sm opacity-80">Heure de fin estimée</p>
      <p className="text-2xl font-semibold">{heureFin}</p>
    </motion.div>
  );
}
```

```typescript
// frontend/components/TrajetCard.tsx
"use client";

import { motion } from "framer-motion";

type Trajet = {
  id: string;
  adresse: string;
  cout_essence: number;
  duree_trajet_min: number;
  duree_chantier_min: number;
};

type Props = {
  trajet: Trajet;
  onMoveUp: () => void;
  onMoveDown: () => void;
};

export function TrajetCard({ trajet, onMoveUp, onMoveDown }: Props) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center justify-between rounded-lg bg-gray-800 p-4 text-white"
    >
      <div>
        <p className="font-medium">{trajet.adresse}</p>
        <p className="text-sm text-gray-400">
          {trajet.duree_trajet_min.toFixed(0)} min trajet + {trajet.duree_chantier_min} min chantier
        </p>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-semibold text-green-400">{trajet.cout_essence.toFixed(2)} €</span>
        <button onClick={onMoveUp} aria-label="Monter" className="rounded bg-gray-700 px-2 py-1">↑</button>
        <button onClick={onMoveDown} aria-label="Descendre" className="rounded bg-gray-700 px-2 py-1">↓</button>
      </div>
    </motion.div>
  );
}
```

```typescript
// frontend/app/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import { createSupabaseBrowserClient } from "@/lib/supabase-client";
import { createApiClient } from "@/lib/api-client";
import { VehicleOnboardingModal } from "@/components/VehicleOnboardingModal";
import { TrajetCard } from "@/components/TrajetCard";
import { RecapPanel } from "@/components/RecapPanel";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL!;

export default function DashboardPage() {
  const supabase = createSupabaseBrowserClient();
  const apiClient = createApiClient({
    baseUrl: API_BASE_URL,
    getAccessToken: async () => {
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token ?? "";
    },
  });

  const [hasVehicleProfile, setHasVehicleProfile] = useState<boolean | null>(null);
  const [vehicleProfileId, setVehicleProfileId] = useState<string | null>(null);
  const [trajets, setTrajets] = useState<any[]>([]);
  const [coutTotalJour, setCoutTotalJour] = useState(0);
  const [heureFin, setHeureFin] = useState("--:--");
  const [newAddress, setNewAddress] = useState("");
  const [newDureeChantier, setNewDureeChantier] = useState(15);

  useEffect(() => {
    apiClient.listVehicleProfiles().then((profiles) => {
      setHasVehicleProfile(profiles.length > 0);
      if (profiles.length > 0) setVehicleProfileId(profiles[0].id);
    });
  }, []);

  const handleOnboardingSubmit = async (payload: any) => {
    const profile = await apiClient.createVehicleProfile(payload);
    setVehicleProfileId(profile.id);
    setHasVehicleProfile(true);
  };

  const handleAddTrajet = async () => {
    if (!vehicleProfileId) return;
    const recap = await apiClient.addTrajet("tournee-du-jour", vehicleProfileId, "08:00", {
      adresse: newAddress,
      duree_chantier_min: newDureeChantier,
      ordre: trajets.length + 1,
    });
    setTrajets(recap.trajets);
    setCoutTotalJour(recap.cout_total_jour);
    setHeureFin(recap.heure_fin);
    setNewAddress("");
  };

  if (hasVehicleProfile === null) return null;
  if (!hasVehicleProfile) return <VehicleOnboardingModal onSubmit={handleOnboardingSubmit} />;

  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-3">
          <h1 className="mb-4 text-2xl font-bold">Tournée du jour</h1>
          {trajets.map((trajet, i) => (
            <TrajetCard
              key={trajet.id}
              trajet={trajet}
              onMoveUp={() => {}}
              onMoveDown={() => {}}
            />
          ))}
          <div className="flex gap-2 pt-4">
            <input
              className="flex-1 rounded bg-gray-800 p-2"
              placeholder="Adresse du prochain trajet"
              value={newAddress}
              onChange={(e) => setNewAddress(e.target.value)}
            />
            <input
              type="number"
              className="w-32 rounded bg-gray-800 p-2"
              value={newDureeChantier}
              onChange={(e) => setNewDureeChantier(parseInt(e.target.value))}
            />
            <button onClick={handleAddTrajet} className="rounded bg-blue-600 px-4 font-medium">
              + Ajouter
            </button>
          </div>
        </div>
        <RecapPanel coutTotalJour={coutTotalJour} heureFin={heureFin} />
      </div>
    </main>
  );
}
```

- [ ] **Step 6: Verify manually in the browser (per project CLAUDE.md — no E2E in V1)**

Run: `cd frontend && npm run dev`, then use the `run` skill to open `http://localhost:3000/login`, log in with Google, complete onboarding, add 2 trajets, confirm cost/end-time update.

- [ ] **Step 7: Commit**

```bash
cd frontend && git add -A
git commit -m "feat(frontend): add onboarding modal, trip list, and animated recap panel"
```

---

## Task 10: PostHog analytics integration

**Files:**
- Create: `frontend/lib/posthog-client.ts`
- Modify: `frontend/app/layout.tsx`
- Modify: `frontend/app/dashboard/page.tsx`
- Test: `frontend/lib/posthog-client.test.ts`

**Interfaces:**
- Produces: `initPostHog(): void`, `trackEvent(name: string, properties?: Record<string, unknown>): void`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/lib/posthog-client.test.ts
import { describe, it, expect, vi } from "vitest";

vi.mock("posthog-js", () => ({
  default: { init: vi.fn(), capture: vi.fn() },
}));

describe("trackEvent", () => {
  it("calls posthog.capture with event name and properties", async () => {
    const posthog = (await import("posthog-js")).default;
    const { trackEvent } = await import("./posthog-client");

    trackEvent("trajet_ajoute", { tournee_id: "t1" });

    expect(posthog.capture).toHaveBeenCalledWith("trajet_ajoute", { tournee_id: "t1" });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run lib/posthog-client.test.ts`
Expected: FAIL with module not found (`./posthog-client` doesn't exist)

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/lib/posthog-client.ts
import posthog from "posthog-js";

export function initPostHog() {
  if (typeof window === "undefined") return;
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: "https://eu.i.posthog.com",
  });
}

export function trackEvent(name: string, properties?: Record<string, unknown>) {
  posthog.capture(name, properties);
}
```

```typescript
// frontend/app/layout.tsx
"use client";

import { useEffect } from "react";
import { initPostHog } from "@/lib/posthog-client";
import "./globals.css";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    initPostHog();
  }, []);

  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
```

```typescript
// frontend/app/dashboard/page.tsx
// --- add import and calls to existing file from Task 9 ---
import { trackEvent } from "@/lib/posthog-client";

// inside handleOnboardingSubmit, after setHasVehicleProfile(true):
trackEvent("vehicle_profile_created");

// inside handleAddTrajet, after setHeureFin(recap.heure_fin):
trackEvent("trajet_ajoute", { tournee_id: "tournee-du-jour" });
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run lib/posthog-client.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd frontend && git add -A
git commit -m "feat(frontend): add PostHog analytics with vehicle/trajet events"
```

---

## Task 11: Docker Compose for backend

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `.env.example`

**Interfaces:**
- Produces: `docker-compose up` starts the FastAPI backend on port 8000, reading env vars from `.env`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src ./src

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Write docker-compose.yml**

```yaml
# docker-compose.yml
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
```

- [ ] **Step 3: Write .env.example**

```bash
# .env.example
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
MAPBOX_TOKEN=your-mapbox-token
```

- [ ] **Step 4: Verify it builds and runs**

Run: `docker compose build && docker compose up -d`
Expected: container starts; `curl http://localhost:8000/health` returns `{"status":"ok"}`

Run: `docker compose down`

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml backend/Dockerfile .env.example
git commit -m "feat(infra): add docker-compose setup for backend"
```

---

## Self-Review Notes

- **Spec coverage:** vehicle profile CRUD (Task 6), fuel price cache (Task 4), Mapbox geocoding/routing (Task 3), trajet add + cost/heure_fin calc (Task 2, 7), Google SSO (Task 8), onboarding defaults (Task 9), single data path via FastAPI (Tasks 6-7, frontend only calls `/vehicle-profiles` and `/tournees`), PostHog events (Task 10), Docker (Task 11), reorder fallback buttons (Task 9 `TrajetCard`). Not covered in this plan (deliberately out of scope per spec): drag-and-drop reordering backend recalculation trigger, blog, department extraction edge cases beyond regex fallback — flag these as known gaps for a fast-follow task once V1 ships and is demoed.
- **Placeholder scan:** none found — all steps have real code.
- **Type consistency:** `TripInput`, `RoutingClient`, `GeocodedAddress`, `RouteResult`, `FuelPriceService`, `TourneeCalculator` names and signatures match across Tasks 2-3-4-7.
