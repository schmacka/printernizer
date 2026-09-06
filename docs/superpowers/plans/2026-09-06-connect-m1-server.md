# Printernizer Connect M1 — Server-Side API Keys & Connect Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Printernizer authenticated endpoints a desktop companion can call: API-key auth, `GET /api/v1/connect/info` for capability discovery, and `POST /api/v1/connect/exports` for authenticated file upload.

**Architecture:** A new `api_keys` table behind an `ApiKeyRepository`, a `require_api_key` FastAPI dependency, a new `connect` router that depends on it, and key management in the existing settings router and Settings UI. Uploads delegate to the existing `FileService.upload_files` so the library, thumbnail and metadata pipelines are reused unchanged.

**Tech Stack:** Python 3.11, FastAPI, aiosqlite, Pydantic v1-style models (matching the codebase), pytest + `fastapi.testclient.TestClient`, structlog. Frontend: vanilla JS, the existing `ApiClient`.

**Spec:** `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md` (§8.1, §8.2, §9)

## Global Constraints

- **Routing:** never use `"/"` as an endpoint path — use `""` for root resources. `redirect_slashes=False` is set app-wide; a `"/"` path produces 405s. (Project CLAUDE.md, "API Routing Standards".)
- **Language:** English for logging, GUI, reports and code comments.
- **Errors:** raise the `PrinternizerError` subclasses in `src/utils/errors.py`; they render the project's standard `{status, message, error_code, details, timestamp}` envelope. Successes use `success_response(...)` from the same module.
- **Auth scope:** the key is enforced **only** on `/api/v1/connect/*`. Existing routes, the frontend and HA ingress stay unauthenticated — retrofitting global auth is explicitly out of scope (spec §8.1).
- **Migrations:** SQL files in `migrations/`, named `NNN_description.sql`, applied in sorted order by `Database._run_sql_migrations`. The runner records them; do not `INSERT INTO migrations` yourself. Next free number is **040**.
- **Repositories:** subclass `BaseRepository`; use `_execute_write(sql, params: tuple)`, `_fetch_one(sql, params: list)`, `_fetch_all(sql, params: list)`.
- **Branch:** work on `feature/connect-m1-server` off `master`. Never commit to `master` directly.
- **Version floor:** `MIN_CONNECT_VERSION = "0.1.0"` — the oldest companion this server accepts.
- **Tests:** `pytest.ini` sets `asyncio_mode = auto`, so a bare `async def test_…` runs without `@pytest.mark.asyncio`. Do not add the marker.
- **Database access in tests:** the `async_database` fixture (`tests/conftest.py`) builds a real `Database` and calls `initialize()`, which applies everything in `migrations/`. Get its connection with `async_database.get_connection()`.

## Scope note (read before starting)

Spec §8.2 describes `POST /connect/exports` applying order/customer links and `print_on`. **Those are M3**, because both depend on the provenance stamps and the `print_after_upload` flow that M3 builds. M1's `/exports` accepts `is_business` and `notes` only, and **rejects unknown metadata fields** so a client is never told something was stored when it was not. M3 widens the contract along with the migration it needs.

## File Structure

| File | Responsibility |
|---|---|
| `migrations/040_api_keys.sql` | The `api_keys` table |
| `src/database/repositories/api_key_repository.py` | CRUD for API keys; hashing lives in the service layer, not here |
| `src/database/repositories/__init__.py` | Export the new repository |
| `src/services/api_key_service.py` | Key generation, hashing, verification — the only place that knows the key format |
| `src/utils/dependencies.py` | `get_api_key_repository`, `get_api_key_service` |
| `src/api/dependencies/auth.py` | `require_api_key` — new package, since this is the first cross-router dependency of its kind |
| `src/api/routers/connect.py` | `GET /info`, `POST /exports` |
| `src/api/routers/settings.py` | Key management endpoints (append to the existing router) |
| `src/main.py` | Register the connect router |
| `frontend/index.html` | Integrations settings tab |
| `frontend/js/api-keys.js` | Key management UI |
| `frontend/locales/{en,de}.json` | Strings |
| `tests/backend/test_api_key_service.py` | Generation, hashing, verification |
| `tests/backend/test_api_keys.py` | Key management endpoints |
| `tests/backend/test_api_connect.py` | Auth enforcement, `/info`, `/exports` |

---

### Task 1: `api_keys` table and repository

**Files:**
- Create: `migrations/040_api_keys.sql`
- Create: `src/database/repositories/api_key_repository.py`
- Modify: `src/database/repositories/__init__.py`
- Test: `tests/backend/test_api_key_repository.py`

**Interfaces:**
- Consumes: `BaseRepository` from `src.database.repositories.base_repository`.
- Produces: `ApiKeyRepository(connection)` with
  `create(key_id: str, name: str, key_hash: str) -> bool`,
  `list_keys() -> List[Dict[str, Any]]`,
  `get_by_hash(key_hash: str) -> Optional[Dict[str, Any]]`,
  `touch(key_id: str) -> bool`,
  `delete(key_id: str) -> bool`.
  Rows are dicts with keys `id, name, key_hash, created_at, last_used_at`.

- [ ] **Step 1: Create the branch**

```bash
cd /Users/sebastianseubert/Developer/printernizer
git checkout master && git pull origin master
git checkout -b feature/connect-m1-server
```

- [ ] **Step 2: Write the migration**

`migrations/040_api_keys.sql`:

```sql
-- Migration: 040_api_keys.sql
-- Description: API keys for authenticating Printernizer Connect (the PrusaSlicer
--              companion) against the /api/v1/connect endpoints. Only the SHA-256
--              hash of a key is stored; the plaintext is shown to the user once.
-- Date: 2026-09-06

CREATE TABLE IF NOT EXISTS api_keys (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    key_hash     TEXT NOT NULL UNIQUE,
    created_at   TEXT NOT NULL,
    last_used_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
```

- [ ] **Step 3: Write the failing repository test**

`tests/backend/test_api_key_repository.py`:

```python
"""Tests for ApiKeyRepository — storage and lookup of API key records."""
import pytest

from src.database.repositories.api_key_repository import ApiKeyRepository


@pytest.fixture
async def repo(async_database):
    """ApiKeyRepository bound to a real temporary database."""
    return ApiKeyRepository(async_database.get_connection())


class TestApiKeyRepository:
    async def test_create_then_get_by_hash(self, repo):
        created = await repo.create("key1", "My laptop", "hash-aaa")
        assert created is True

        row = await repo.get_by_hash("hash-aaa")
        assert row is not None
        assert row["id"] == "key1"
        assert row["name"] == "My laptop"
        assert row["last_used_at"] is None

    async def test_get_by_hash_returns_none_when_unknown(self, repo):
        assert await repo.get_by_hash("nope") is None

    async def test_list_keys_returns_all_without_hashes_stripped(self, repo):
        await repo.create("key1", "Laptop", "hash-aaa")
        await repo.create("key2", "Workshop PC", "hash-bbb")

        keys = await repo.list_keys()
        assert {k["id"] for k in keys} == {"key1", "key2"}

    async def test_touch_sets_last_used_at(self, repo):
        await repo.create("key1", "Laptop", "hash-aaa")
        assert await repo.touch("key1") is True

        row = await repo.get_by_hash("hash-aaa")
        assert row["last_used_at"] is not None

    async def test_delete_removes_the_key(self, repo):
        await repo.create("key1", "Laptop", "hash-aaa")
        assert await repo.delete("key1") is True
        assert await repo.get_by_hash("hash-aaa") is None

    async def test_delete_returns_false_for_unknown_key(self, repo):
        assert await repo.delete("ghost") is False
```

- [ ] **Step 4: Run the test and confirm it fails for the right reason**

```bash
pytest tests/backend/test_api_key_repository.py -v
```

Expected: collection error — `ModuleNotFoundError: No module named 'src.database.repositories.api_key_repository'`.

If instead it fails with "table api_keys does not exist", the `async_database` fixture is not applying `migrations/`. Check `tests/conftest.py`'s `async_database` fixture and make it call the same initialisation path as production (`Database.connect()`), rather than creating a bare schema.

- [ ] **Step 5: Implement the repository**

`src/database/repositories/api_key_repository.py`:

```python
"""
Repository for API key records.

Stores only the SHA-256 hash of each key. Generation, hashing and verification
live in `src.services.api_key_service` — this class is pure storage.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from .base_repository import BaseRepository

logger = structlog.get_logger()


class ApiKeyRepository(BaseRepository):
    """Storage for API keys used by Printernizer Connect."""

    async def create(self, key_id: str, name: str, key_hash: str) -> bool:
        """Insert a new API key record. Returns True on success."""
        await self._execute_write(
            """
            INSERT INTO api_keys (id, name, key_hash, created_at, last_used_at)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (key_id, name, key_hash, datetime.now(timezone.utc).isoformat()),
        )
        logger.info("API key created", key_id=key_id, name=name)
        return True

    async def list_keys(self) -> List[Dict[str, Any]]:
        """Return all API key records, newest first."""
        return await self._fetch_all(
            "SELECT id, name, key_hash, created_at, last_used_at "
            "FROM api_keys ORDER BY created_at DESC"
        )

    async def get_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Look up a key record by its hash, or None."""
        return await self._fetch_one(
            "SELECT id, name, key_hash, created_at, last_used_at "
            "FROM api_keys WHERE key_hash = ?",
            [key_hash],
        )

    async def touch(self, key_id: str) -> bool:
        """Record that a key was just used. Returns True if the key exists."""
        existing = await self._fetch_one(
            "SELECT id FROM api_keys WHERE id = ?", [key_id]
        )
        if existing is None:
            return False
        await self._execute_write(
            "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), key_id),
        )
        return True

    async def delete(self, key_id: str) -> bool:
        """Delete a key. Returns True if it existed."""
        existing = await self._fetch_one(
            "SELECT id FROM api_keys WHERE id = ?", [key_id]
        )
        if existing is None:
            return False
        await self._execute_write("DELETE FROM api_keys WHERE id = ?", (key_id,))
        logger.info("API key deleted", key_id=key_id)
        return True
```

- [ ] **Step 6: Export the repository**

In `src/database/repositories/__init__.py`, add the import next to the others and the name to `__all__`:

```python
from .api_key_repository import ApiKeyRepository
```

```python
    'ApiKeyRepository',
```

- [ ] **Step 7: Run the tests and confirm they pass**

```bash
pytest tests/backend/test_api_key_repository.py -v
```

Expected: 6 passed.

- [ ] **Step 8: Commit**

```bash
git add migrations/040_api_keys.sql \
        src/database/repositories/api_key_repository.py \
        src/database/repositories/__init__.py \
        tests/backend/test_api_key_repository.py
git commit -m "feat: Add api_keys table and repository"
```

---

### Task 2: API key service — generation, hashing, verification

**Files:**
- Create: `src/services/api_key_service.py`
- Modify: `src/utils/dependencies.py`
- Test: `tests/backend/test_api_key_service.py`

**Interfaces:**
- Consumes: `ApiKeyRepository` from Task 1.
- Produces:
  `ApiKeyService(repository)` with
  `async create_key(name: str) -> Tuple[str, Dict[str, Any]]` returning `(plaintext_key, record)`,
  `async verify(key: str) -> Optional[Dict[str, Any]]` returning the record (and touching it) or None,
  `async list_keys() -> List[Dict[str, Any]]` (records **without** `key_hash`),
  `async delete_key(key_id: str) -> bool`,
  and the module constant `KEY_PREFIX = "pk_"`.
- Also produces DI providers `get_api_key_repository(...)` and `get_api_key_service(...)` in `src/utils/dependencies.py`.

**Why plain SHA-256 and not bcrypt/argon2:** keys are 32 random url-safe bytes (~256 bits of entropy) generated by us, not user-chosen passwords. There is no dictionary to attack, so a slow KDF buys nothing and would add per-request latency to every companion call. Do not "upgrade" this to bcrypt.

- [ ] **Step 1: Write the failing service test**

`tests/backend/test_api_key_service.py`:

```python
"""Tests for ApiKeyService — key generation, hashing and verification."""
import hashlib
from unittest.mock import AsyncMock

import pytest

from src.services.api_key_service import ApiKeyService, KEY_PREFIX


@pytest.fixture
def repo():
    """Repository double."""
    r = AsyncMock()
    r.create = AsyncMock(return_value=True)
    r.get_by_hash = AsyncMock(return_value=None)
    r.touch = AsyncMock(return_value=True)
    r.delete = AsyncMock(return_value=True)
    r.list_keys = AsyncMock(return_value=[])
    return r


@pytest.fixture
def service(repo):
    return ApiKeyService(repo)


class TestCreateKey:
    async def test_returns_plaintext_key_with_prefix(self, service):
        plaintext, record = await service.create_key("My laptop")
        assert plaintext.startswith(KEY_PREFIX)
        assert len(plaintext) > len(KEY_PREFIX) + 20
        assert record["name"] == "My laptop"

    async def test_stores_only_the_hash_never_the_plaintext(self, service, repo):
        plaintext, _ = await service.create_key("My laptop")

        repo.create.assert_awaited_once()
        _key_id, _name, stored_hash = repo.create.await_args.args
        assert stored_hash == hashlib.sha256(plaintext.encode()).hexdigest()
        assert plaintext not in stored_hash

    async def test_two_keys_differ(self, service):
        first, _ = await service.create_key("a")
        second, _ = await service.create_key("b")
        assert first != second

    async def test_returned_record_does_not_leak_the_hash(self, service):
        _plaintext, record = await service.create_key("My laptop")
        assert "key_hash" not in record


class TestVerify:
    async def test_returns_none_for_unknown_key(self, service):
        assert await service.verify("pk_nope") is None

    async def test_returns_none_for_empty_key(self, service, repo):
        assert await service.verify("") is None
        repo.get_by_hash.assert_not_awaited()

    async def test_returns_record_and_touches_on_success(self, service, repo):
        repo.get_by_hash.return_value = {
            "id": "key1", "name": "Laptop", "key_hash": "h",
            "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None,
        }

        record = await service.verify("pk_whatever")

        assert record["id"] == "key1"
        repo.touch.assert_awaited_once_with("key1")

    async def test_looks_up_by_hash_not_plaintext(self, service, repo):
        await service.verify("pk_secret")
        repo.get_by_hash.assert_awaited_once_with(
            hashlib.sha256(b"pk_secret").hexdigest()
        )


class TestListKeys:
    async def test_strips_hashes_from_listed_keys(self, service, repo):
        repo.list_keys.return_value = [
            {"id": "key1", "name": "Laptop", "key_hash": "secret-hash",
             "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None},
        ]

        keys = await service.list_keys()

        assert keys == [{
            "id": "key1", "name": "Laptop",
            "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None,
        }]
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
pytest tests/backend/test_api_key_service.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.services.api_key_service'`.

- [ ] **Step 3: Implement the service**

`src/services/api_key_service.py`:

```python
"""
API key generation and verification for Printernizer Connect.

Keys are 32 random url-safe bytes behind a `pk_` prefix. Only the SHA-256 hash
is persisted; the plaintext is returned exactly once, at creation.

A fast hash is deliberate: keys are high-entropy values we generate, not
user-chosen passwords, so there is nothing for a slow KDF to defend against and
verification runs on every companion request.
"""
import hashlib
import secrets
import uuid
from typing import Any, Dict, List, Optional, Tuple

import structlog

from src.database.repositories.api_key_repository import ApiKeyRepository

logger = structlog.get_logger()

KEY_PREFIX = "pk_"
_KEY_BYTES = 32


def hash_key(key: str) -> str:
    """Return the storage hash for a plaintext key."""
    return hashlib.sha256(key.encode()).hexdigest()


class ApiKeyService:
    """Creates, verifies and revokes API keys."""

    def __init__(self, repository: ApiKeyRepository):
        self.repository = repository

    async def create_key(self, name: str) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new API key.

        Returns:
            (plaintext_key, record) — the plaintext is not recoverable later.
        """
        plaintext = KEY_PREFIX + secrets.token_urlsafe(_KEY_BYTES)
        key_id = str(uuid.uuid4())

        await self.repository.create(key_id, name, hash_key(plaintext))

        record = await self.repository.get_by_hash(hash_key(plaintext))
        if record is None:
            # The row was just written; a miss means the write silently failed.
            record = {"id": key_id, "name": name,
                      "created_at": None, "last_used_at": None}
        return plaintext, _without_hash(record)

    async def verify(self, key: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return the key record if `key` is valid, else None. Touches on success."""
        if not key:
            return None

        record = await self.repository.get_by_hash(hash_key(key))
        if record is None:
            return None

        await self.repository.touch(record["id"])
        return _without_hash(record)

    async def list_keys(self) -> List[Dict[str, Any]]:
        """Return all keys, without their hashes."""
        return [_without_hash(r) for r in await self.repository.list_keys()]

    async def delete_key(self, key_id: str) -> bool:
        """Revoke a key. Returns True if it existed."""
        return await self.repository.delete(key_id)


def _without_hash(record: Dict[str, Any]) -> Dict[str, Any]:
    """Copy a record with the hash removed — hashes never leave this module."""
    return {k: v for k, v in record.items() if k != "key_hash"}
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
pytest tests/backend/test_api_key_service.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Add the DI providers**

In `src/utils/dependencies.py`, add the imports next to the existing ones:

```python
from src.database.repositories import ApiKeyRepository
from src.services.api_key_service import ApiKeyService
```

and the providers after `get_file_repository`:

```python
async def get_api_key_repository(
    database: Database = Depends(get_database)
) -> ApiKeyRepository:
    """Get API key repository instance."""
    return ApiKeyRepository(database._connection)


async def get_api_key_service(
    repository: ApiKeyRepository = Depends(get_api_key_repository)
) -> ApiKeyService:
    """Get API key service instance."""
    return ApiKeyService(repository)
```

- [ ] **Step 6: Verify the providers import cleanly**

```bash
python3 -c "
from src.utils.dependencies import get_api_key_service, get_api_key_repository
print('dependencies OK')
"
```

Expected: `dependencies OK`

- [ ] **Step 7: Commit**

```bash
git add src/services/api_key_service.py src/utils/dependencies.py \
        tests/backend/test_api_key_service.py
git commit -m "feat: Add API key service with generation and verification"
```

---

### Task 3: `require_api_key` dependency

**Files:**
- Create: `src/api/dependencies/__init__.py`
- Create: `src/api/dependencies/auth.py`
- Test: `tests/backend/test_require_api_key.py`

**Interfaces:**
- Consumes: `get_api_key_service` from Task 2, `AuthenticationError` from `src.utils.errors`.
- Produces: `require_api_key(...)` — a FastAPI dependency returning the key record dict, raising `AuthenticationError` otherwise. Accepts `X-Api-Key: <key>` or `Authorization: Bearer <key>`.

- [ ] **Step 1: Write the failing test**

`tests/backend/test_require_api_key.py`:

```python
"""Tests for the require_api_key dependency."""
from unittest.mock import AsyncMock

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies.auth import require_api_key
from src.utils.dependencies import get_api_key_service
from src.utils.errors import setup_exception_handlers

VALID = {"id": "key1", "name": "Laptop",
         "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None}


@pytest.fixture
def app_and_service():
    """A minimal app with one protected route and a stubbed key service."""
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/protected")
    async def protected(key=Depends(require_api_key)):
        return {"key_id": key["id"]}

    service = AsyncMock()
    service.verify = AsyncMock(return_value=None)
    app.dependency_overrides[get_api_key_service] = lambda: service
    return app, service


class TestRequireApiKey:
    def test_rejects_request_with_no_key(self, app_and_service):
        app, _ = app_and_service
        response = TestClient(app).get("/protected")
        assert response.status_code == 401

    def test_rejects_unknown_key(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = None
        response = TestClient(app).get(
            "/protected", headers={"X-Api-Key": "pk_wrong"}
        )
        assert response.status_code == 401

    def test_accepts_valid_x_api_key_header(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = VALID
        response = TestClient(app).get(
            "/protected", headers={"X-Api-Key": "pk_right"}
        )
        assert response.status_code == 200
        assert response.json()["key_id"] == "key1"
        service.verify.assert_awaited_once_with("pk_right")

    def test_accepts_valid_bearer_token(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = VALID
        response = TestClient(app).get(
            "/protected", headers={"Authorization": "Bearer pk_right"}
        )
        assert response.status_code == 200
        service.verify.assert_awaited_once_with("pk_right")

    def test_ignores_non_bearer_authorization_scheme(self, app_and_service):
        app, service = app_and_service
        response = TestClient(app).get(
            "/protected", headers={"Authorization": "Basic dXNlcjpwYXNz"}
        )
        assert response.status_code == 401
        service.verify.assert_not_awaited()

    def test_x_api_key_wins_over_authorization_header(self, app_and_service):
        app, service = app_and_service
        service.verify.return_value = VALID
        TestClient(app).get(
            "/protected",
            headers={"X-Api-Key": "pk_primary",
                     "Authorization": "Bearer pk_secondary"},
        )
        service.verify.assert_awaited_once_with("pk_primary")

    def test_error_body_uses_the_project_envelope(self, app_and_service):
        app, _ = app_and_service
        body = TestClient(app).get("/protected").json()
        assert body["status"] == "error"
        assert "message" in body
```

- [ ] **Step 2: Confirm the error-handler helper name before running**

The test imports `setup_exception_handlers`. Verify the real name:

```bash
grep -n "^def setup_exception\|^def register_exception\|add_exception_handler" src/utils/errors.py | head
```

If it is named differently, update the import in the test to the real name. If no such helper exists, drop that import and the `test_error_body_uses_the_project_envelope` case, and instead assert only on status codes.

- [ ] **Step 3: Run the test and confirm it fails**

```bash
pytest tests/backend/test_require_api_key.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.api.dependencies'`.

- [ ] **Step 4: Create the package**

`src/api/dependencies/__init__.py`:

```python
"""Shared FastAPI dependencies for API routers."""
```

- [ ] **Step 5: Implement the dependency**

`src/api/dependencies/auth.py`:

```python
"""
API key authentication for the Printernizer Connect endpoints.

Only `/api/v1/connect/*` requires a key today. The rest of the API and the
frontend remain unauthenticated — see spec section 8.1.
"""
from typing import Any, Dict, Optional

import structlog
from fastapi import Depends, Header

from src.services.api_key_service import ApiKeyService
from src.utils.dependencies import get_api_key_service
from src.utils.errors import AuthenticationError

logger = structlog.get_logger()

_BEARER = "bearer "


async def require_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key"),
    authorization: Optional[str] = Header(None),
    api_key_service: ApiKeyService = Depends(get_api_key_service),
) -> Dict[str, Any]:
    """
    Require a valid API key.

    Accepts `X-Api-Key: <key>` or `Authorization: Bearer <key>`; `X-Api-Key`
    takes precedence when both are present.

    Returns:
        The key record (id, name, created_at, last_used_at).

    Raises:
        AuthenticationError: no key supplied, or the key is unknown.
    """
    key = x_api_key
    if not key and authorization and authorization.lower().startswith(_BEARER):
        key = authorization[len(_BEARER):].strip()

    if not key:
        raise AuthenticationError(reason="API key required")

    record = await api_key_service.verify(key)
    if record is None:
        logger.warning("Rejected request with invalid API key")
        raise AuthenticationError(reason="Invalid API key")

    return record
```

- [ ] **Step 6: Run the tests and confirm they pass**

```bash
pytest tests/backend/test_require_api_key.py -v
```

Expected: 7 passed (6 if you dropped the envelope test in Step 2).

- [ ] **Step 7: Commit**

```bash
git add src/api/dependencies tests/backend/test_require_api_key.py
git commit -m "feat: Add require_api_key authentication dependency"
```

---

### Task 4: Key management endpoints

**Files:**
- Modify: `src/api/routers/settings.py` (append at the end)
- Test: `tests/backend/test_api_keys.py`

**Interfaces:**
- Consumes: `get_api_key_service` from Task 2.
- Produces:
  `GET /api/v1/settings/api-keys` → `{status, data: {keys: [...]}}`,
  `POST /api/v1/settings/api-keys` body `{"name": str}` → 201 `{status, data: {key: "<plaintext>", ...}}`,
  `DELETE /api/v1/settings/api-keys/{key_id}` → 200, or 404 when unknown.
  Pydantic models `ApiKeyResponse`, `CreateApiKeyRequest`, `CreatedApiKeyResponse`.

These endpoints are **not** key-protected — they are managed from the local web UI, consistent with the rest of the settings API (spec §8.1).

- [ ] **Step 1: Write the failing endpoint test**

`tests/backend/test_api_keys.py`:

```python
"""Tests for API key management endpoints."""
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.utils.dependencies import get_api_key_service

RECORD = {"id": "key1", "name": "My laptop",
          "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None}


@pytest.fixture
def service(test_app):
    """Stub the API key service on the shared test app."""
    stub = AsyncMock()
    stub.list_keys = AsyncMock(return_value=[])
    stub.create_key = AsyncMock(return_value=("pk_plaintext_value", RECORD))
    stub.delete_key = AsyncMock(return_value=True)
    test_app.dependency_overrides[get_api_key_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_api_key_service, None)


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestListApiKeys:
    def test_returns_empty_list_initially(self, client, service):
        response = client.get("/api/v1/settings/api-keys")
        assert response.status_code == 200
        assert response.json()["data"]["keys"] == []

    def test_returns_keys_without_hashes(self, client, service):
        service.list_keys.return_value = [RECORD]
        keys = client.get("/api/v1/settings/api-keys").json()["data"]["keys"]
        assert keys[0]["id"] == "key1"
        assert "key_hash" not in keys[0]


class TestCreateApiKey:
    def test_returns_the_plaintext_key_once(self, client, service):
        response = client.post("/api/v1/settings/api-keys",
                               json={"name": "My laptop"})
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["key"] == "pk_plaintext_value"
        assert data["name"] == "My laptop"
        service.create_key.assert_awaited_once_with("My laptop")

    def test_rejects_empty_name(self, client, service):
        response = client.post("/api/v1/settings/api-keys", json={"name": ""})
        assert response.status_code == 422
        service.create_key.assert_not_awaited()

    def test_rejects_missing_name(self, client, service):
        assert client.post("/api/v1/settings/api-keys", json={}).status_code == 422


class TestDeleteApiKey:
    def test_deletes_an_existing_key(self, client, service):
        response = client.delete("/api/v1/settings/api-keys/key1")
        assert response.status_code == 200
        service.delete_key.assert_awaited_once_with("key1")

    def test_returns_404_for_unknown_key(self, client, service):
        service.delete_key.return_value = False
        assert client.delete("/api/v1/settings/api-keys/ghost").status_code == 404
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
pytest tests/backend/test_api_keys.py -v
```

Expected: 404s on every route — the endpoints do not exist yet.

- [ ] **Step 3: Implement the endpoints**

Append to `src/api/routers/settings.py`. Add to the existing imports at the top:

```python
from fastapi import status
from pydantic import Field
from src.services.api_key_service import ApiKeyService
from src.utils.dependencies import get_api_key_service
from src.utils.errors import ResourceConflictError
```

then at the end of the file:

```python
# =============================================================================
# API Keys — used by Printernizer Connect (the PrusaSlicer companion)
# =============================================================================


class ApiKeyResponse(BaseModel):
    """An API key, without its hash."""
    id: str
    name: str
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None


class CreateApiKeyRequest(BaseModel):
    """Request body for creating an API key."""
    name: str = Field(..., min_length=1, max_length=100)


@router.get("/api-keys")
async def list_api_keys(
    api_key_service: ApiKeyService = Depends(get_api_key_service)
):
    """
    List all API keys.

    Key values themselves are never returned — only the metadata. A key's
    plaintext is shown exactly once, when it is created.
    """
    keys = await api_key_service.list_keys()
    return success_response(data={"keys": keys})


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateApiKeyRequest,
    api_key_service: ApiKeyService = Depends(get_api_key_service)
):
    """
    Create a new API key.

    The returned `key` is the only time the plaintext is available; it cannot
    be recovered afterwards.
    """
    plaintext, record = await api_key_service.create_key(request.name)
    logger.info("API key created", key_id=record.get("id"), name=request.name)

    return success_response(
        data={**record, "key": plaintext},
        status_code=status.HTTP_201_CREATED,
        message="Store this key now — it will not be shown again",
    )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    api_key_service: ApiKeyService = Depends(get_api_key_service)
):
    """Revoke an API key. Any companion using it stops working immediately."""
    deleted = await api_key_service.delete_key(key_id)
    if not deleted:
        raise PrinternizerValidationError(
            message=f"API key not found: {key_id}",
            field="key_id",
        )

    logger.info("API key deleted", key_id=key_id)
    return success_response(data={"id": key_id}, message="API key revoked")
```

- [ ] **Step 4: Make the not-found case return 404**

`PrinternizerValidationError` renders 422, not 404. Check what the codebase offers:

```bash
grep -n "status.HTTP_404" src/utils/errors.py | head
```

Use whichever existing error class maps to 404 (e.g. `LibraryItemNotFoundError`'s base pattern). If none is generic enough, add a small one next to the others in `src/utils/errors.py`:

```python
class ApiKeyNotFoundError(PrinternizerError):
    """API key not found."""

    def __init__(self, key_id: str):
        super().__init__(
            message=f"API key not found: {key_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="API_KEY_NOT_FOUND",
            details={"key_id": key_id},
        )
```

Match the constructor signature of the neighbouring classes — check whether they pass `error_code` explicitly or derive it. Then use it in `delete_api_key`.

- [ ] **Step 5: Run the tests and confirm they pass**

```bash
pytest tests/backend/test_api_keys.py -v
```

Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add src/api/routers/settings.py src/utils/errors.py tests/backend/test_api_keys.py
git commit -m "feat: Add API key management endpoints"
```

---

### Task 5: `connect` router — `GET /info`

**Files:**
- Create: `src/api/routers/connect.py`
- Modify: `src/main.py`
- Test: `tests/backend/test_api_connect.py`

**Interfaces:**
- Consumes: `require_api_key` (Task 3), `get_printer_service`, `APP_VERSION` from `src.main`.
- Produces: `GET /api/v1/connect/info` → `{status, data: {server_version, min_connect_version, capabilities: {exports, profiles, printhost}, printers: [{id, name, type, is_active}]}}`. Module constant `MIN_CONNECT_VERSION = "0.1.0"`.

**Note on printer fields:** spec §8.2 lists `printer_model` and `manufacturer`. The `Printer` model (`src/models/printer.py`) has **no such fields** — it has `type: PrinterType` (`bambu_lab` / `prusa`). Return `id`, `name`, `type`, `is_active` and correct the spec in Task 8.

- [ ] **Step 1: Write the failing test**

`tests/backend/test_api_connect.py`:

```python
"""Tests for the Printernizer Connect API (/api/v1/connect)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.utils.dependencies import get_api_key_service, get_printer_service

VALID_KEY = {"id": "key1", "name": "Laptop",
             "created_at": "2026-09-06T00:00:00+00:00", "last_used_at": None}
AUTH = {"X-Api-Key": "pk_valid"}


@pytest.fixture
def key_service(test_app):
    stub = AsyncMock()
    stub.verify = AsyncMock(return_value=VALID_KEY)
    test_app.dependency_overrides[get_api_key_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_api_key_service, None)


@pytest.fixture
def printer_service(test_app):
    stub = MagicMock()
    stub.list_printers = AsyncMock(return_value=[])
    test_app.dependency_overrides[get_printer_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_printer_service, None)


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestConnectInfoAuth:
    def test_requires_an_api_key(self, client, key_service, printer_service):
        assert client.get("/api/v1/connect/info").status_code == 401

    def test_rejects_an_invalid_api_key(self, client, key_service, printer_service):
        key_service.verify.return_value = None
        response = client.get("/api/v1/connect/info",
                              headers={"X-Api-Key": "pk_wrong"})
        assert response.status_code == 401


class TestConnectInfo:
    def test_reports_server_and_minimum_connect_version(
        self, client, key_service, printer_service
    ):
        data = client.get("/api/v1/connect/info", headers=AUTH).json()["data"]
        assert data["server_version"]
        assert data["min_connect_version"] == "0.1.0"

    def test_reports_capabilities(self, client, key_service, printer_service):
        caps = client.get("/api/v1/connect/info",
                          headers=AUTH).json()["data"]["capabilities"]
        assert caps["exports"] is True
        assert caps["profiles"] is False   # M4
        assert caps["printhost"] is False  # M5

    def test_lists_printers(self, client, key_service, printer_service):
        printer = MagicMock()
        printer.id = "printer-1"
        printer.name = "Core One"
        printer.type = MagicMock(value="prusa")
        printer.is_active = True
        printer_service.list_printers.return_value = [printer]

        printers = client.get("/api/v1/connect/info",
                              headers=AUTH).json()["data"]["printers"]
        assert printers == [{
            "id": "printer-1", "name": "Core One",
            "type": "prusa", "is_active": True,
        }]

    def test_returns_empty_printer_list_when_none_configured(
        self, client, key_service, printer_service
    ):
        data = client.get("/api/v1/connect/info", headers=AUTH).json()["data"]
        assert data["printers"] == []
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
pytest tests/backend/test_api_connect.py -v
```

Expected: 404 on every request — the router is not registered.

- [ ] **Step 3: Create the router**

`src/api/routers/connect.py`:

```python
"""
Printernizer Connect API.

Endpoints for the Printernizer Connect desktop companion, which links a
PrusaSlicer installation to this server. Every endpoint here requires an API
key; the rest of the API is unauthenticated (see spec section 8.1).
"""
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, Depends

from src.api.dependencies.auth import require_api_key
from src.services.printer_service import PrinterService
from src.utils.dependencies import get_printer_service
from src.utils.errors import success_response

logger = structlog.get_logger()
router = APIRouter()

# Oldest Printernizer Connect release this server will talk to.
MIN_CONNECT_VERSION = "0.1.0"


@router.get("/info")
async def get_connect_info(
    key=Depends(require_api_key),
    printer_service: PrinterService = Depends(get_printer_service),
):
    """
    Report server capabilities and the printer fleet.

    Connect calls this before every command to check version compatibility and
    to resolve printer ids.
    """
    from src.main import APP_VERSION

    printers: List[Dict[str, Any]] = []
    for printer in await printer_service.list_printers():
        printer_type = getattr(printer.type, "value", printer.type)
        printers.append({
            "id": printer.id,
            "name": printer.name,
            "type": printer_type,
            "is_active": printer.is_active,
        })

    return success_response(data={
        "server_version": APP_VERSION,
        "min_connect_version": MIN_CONNECT_VERSION,
        "capabilities": {
            "exports": True,
            "profiles": False,   # M4
            "printhost": False,  # M5
        },
        "printers": printers,
    })
```

The `APP_VERSION` import is inside the function deliberately: `src.main` imports the routers, so a module-level import would be circular.

- [ ] **Step 4: Register the router**

In `src/main.py`, add to the router imports (near line 63):

```python
from src.api.routers.connect import router as connect_router
```

and to the registrations (near line 775, after `slicing_router`):

```python
    app.include_router(connect_router, prefix="/api/v1/connect", tags=["Connect"])
```

- [ ] **Step 5: Run the tests and confirm they pass**

```bash
pytest tests/backend/test_api_connect.py -v
```

Expected: 6 passed.

- [ ] **Step 6: Verify the route has no trailing slash**

The project's routing rule exists because `redirect_slashes=False` turns a stray `/` into a 405.

```bash
python3 -c "
from src.main import create_application
paths = [r.path for r in create_application().routes if '/connect' in r.path]
print(paths)
assert paths == ['/api/v1/connect/info'], paths
print('routing OK')
"
```

Expected: `['/api/v1/connect/info']` then `routing OK`.

- [ ] **Step 7: Commit**

```bash
git add src/api/routers/connect.py src/main.py tests/backend/test_api_connect.py
git commit -m "feat: Add connect router with capability discovery endpoint"
```

---

### Task 6: `connect` router — `POST /exports`

**Files:**
- Modify: `src/api/routers/connect.py`
- Test: `tests/backend/test_api_connect.py` (append)

**Interfaces:**
- Consumes: `require_api_key`, `get_file_service`, `FileService.upload_files(files, is_business, notes) -> Dict`.
- Produces: `POST /api/v1/connect/exports`, multipart with `file` (single `UploadFile`) and `metadata` (a JSON string form field). Returns 201 with the uploaded file record. Pydantic model `ExportMetadata` with `extra = "forbid"`.

**Contract note:** M1 accepts only `is_business` and `notes`. Unknown fields are rejected with 422 rather than silently dropped, so the M3 hook cannot believe it stored something it did not. M3 widens this model together with the migration that backs the extra fields.

- [ ] **Step 1: Write the failing test**

Append to `tests/backend/test_api_connect.py`:

```python
import io
import json

from src.utils.dependencies import get_file_service

UPLOAD_OK = {
    "uploaded_files": [{"id": "file-1", "filename": "benchy.gcode",
                        "checksum": "abc123"}],
    "failed_files": [],
    "total_count": 1, "success_count": 1, "failure_count": 0,
}


@pytest.fixture
def file_service(test_app):
    stub = MagicMock()
    stub.settings = MagicMock(enable_upload=True)
    stub.upload_files = AsyncMock(return_value=UPLOAD_OK)
    test_app.dependency_overrides[get_file_service] = lambda: stub
    yield stub
    test_app.dependency_overrides.pop(get_file_service, None)


def _gcode(name="benchy.gcode"):
    return {"file": (name, io.BytesIO(b"; generated by PrusaSlicer\nG1 X0\n"),
                     "text/plain")}


class TestExportsAuth:
    def test_requires_an_api_key(self, client, key_service, file_service):
        response = client.post("/api/v1/connect/exports", files=_gcode(),
                               data={"metadata": "{}"})
        assert response.status_code == 401
        file_service.upload_files.assert_not_awaited()


class TestExports:
    def test_uploads_the_file_and_returns_the_record(
        self, client, key_service, file_service
    ):
        response = client.post("/api/v1/connect/exports", headers=AUTH,
                               files=_gcode(), data={"metadata": "{}"})

        assert response.status_code == 201
        assert response.json()["data"]["file"]["checksum"] == "abc123"
        file_service.upload_files.assert_awaited_once()

    def test_passes_is_business_and_notes_through(
        self, client, key_service, file_service
    ):
        metadata = json.dumps({"is_business": True, "notes": "Order 42"})
        client.post("/api/v1/connect/exports", headers=AUTH,
                    files=_gcode(), data={"metadata": metadata})

        kwargs = file_service.upload_files.await_args.kwargs
        assert kwargs["is_business"] is True
        assert kwargs["notes"] == "Order 42"

    def test_defaults_metadata_when_field_is_absent(
        self, client, key_service, file_service
    ):
        response = client.post("/api/v1/connect/exports", headers=AUTH,
                               files=_gcode())
        assert response.status_code == 201
        assert file_service.upload_files.await_args.kwargs["is_business"] is False

    def test_rejects_unknown_metadata_fields(
        self, client, key_service, file_service
    ):
        metadata = json.dumps({"is_business": True, "print_on": "printer-1"})
        response = client.post("/api/v1/connect/exports", headers=AUTH,
                               files=_gcode(), data={"metadata": metadata})

        assert response.status_code == 422
        file_service.upload_files.assert_not_awaited()

    def test_rejects_malformed_metadata_json(
        self, client, key_service, file_service
    ):
        response = client.post("/api/v1/connect/exports", headers=AUTH,
                               files=_gcode(), data={"metadata": "{not json"})
        assert response.status_code == 422
        file_service.upload_files.assert_not_awaited()

    def test_rejects_an_unsupported_file_type(
        self, client, key_service, file_service
    ):
        response = client.post(
            "/api/v1/connect/exports", headers=AUTH,
            files={"file": ("notes.txt", io.BytesIO(b"hello"), "text/plain")},
            data={"metadata": "{}"},
        )
        assert response.status_code == 422
        file_service.upload_files.assert_not_awaited()

    def test_accepts_bgcode(self, client, key_service, file_service):
        response = client.post(
            "/api/v1/connect/exports", headers=AUTH,
            files={"file": ("benchy.bgcode", io.BytesIO(b"\x00bgcode"),
                            "application/octet-stream")},
            data={"metadata": "{}"},
        )
        assert response.status_code == 201

    def test_returns_400_when_the_upload_fails(
        self, client, key_service, file_service
    ):
        file_service.upload_files.return_value = {
            "uploaded_files": [], "failed_files": [{"filename": "benchy.gcode",
                                                    "error": "duplicate"}],
            "total_count": 1, "success_count": 0, "failure_count": 1,
        }
        response = client.post("/api/v1/connect/exports", headers=AUTH,
                               files=_gcode(), data={"metadata": "{}"})
        assert response.status_code == 400

    def test_returns_403_when_uploads_are_disabled(
        self, client, key_service, file_service
    ):
        file_service.settings.enable_upload = False
        response = client.post("/api/v1/connect/exports", headers=AUTH,
                               files=_gcode(), data={"metadata": "{}"})
        assert response.status_code == 403
```

- [ ] **Step 2: Run it and confirm it fails**

```bash
pytest tests/backend/test_api_connect.py -k Exports -v
```

Expected: 404s — the endpoint does not exist.

- [ ] **Step 3: Implement the endpoint**

Add to the imports at the top of `src/api/routers/connect.py`:

```python
import json
from typing import Optional

from fastapi import File as FastAPIFile, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ValidationError

from src.services.file_service import FileService
from src.utils.dependencies import get_file_service
```

then append:

```python
# Formats a slicer can hand us. `.bgcode` is Prusa's binary G-code, the Core
# One's default export.
ALLOWED_EXPORT_EXTENSIONS = (".gcode", ".bgcode", ".3mf")


class ExportMetadata(BaseModel):
    """
    Metadata accompanying an export.

    Deliberately narrow: unknown fields are rejected rather than dropped, so a
    client is never told something was stored when it was not. M3 widens this
    alongside the migration that backs the extra fields.
    """
    is_business: bool = False
    notes: Optional[str] = None

    class Config:
        extra = "forbid"


@router.post("/exports", status_code=status.HTTP_201_CREATED)
async def create_export(
    file: UploadFile = FastAPIFile(..., description="Exported G-code or project"),
    metadata: str = Form("{}", description="JSON metadata for the export"),
    key=Depends(require_api_key),
    file_service: FileService = Depends(get_file_service),
):
    """
    Receive an export from Printernizer Connect and add it to the library.

    Delegates to the shared upload path, so thumbnails, metadata extraction and
    deduplication all behave exactly as they do for a browser upload.
    """
    if not file_service.settings.enable_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File uploads are disabled on this server",
        )

    filename = file.filename or ""
    if not filename.lower().endswith(ALLOWED_EXPORT_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(f"Unsupported export type: {filename}. "
                    f"Expected one of {', '.join(ALLOWED_EXPORT_EXTENSIONS)}"),
        )

    try:
        parsed = ExportMetadata(**json.loads(metadata))
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed metadata JSON: {exc}",
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid metadata: {exc}",
        )

    logger.info("Connect export received", filename=filename,
                key_id=key["id"], is_business=parsed.is_business)

    result = await file_service.upload_files(
        files=[file],
        is_business=parsed.is_business,
        notes=parsed.notes,
    )

    if result["success_count"] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Export upload failed",
                    "failed_files": result["failed_files"]},
        )

    return success_response(
        data={"file": result["uploaded_files"][0]},
        status_code=status.HTTP_201_CREATED,
        message="Export added to library",
    )
```

- [ ] **Step 4: Run the tests and confirm they pass**

```bash
pytest tests/backend/test_api_connect.py -v
```

Expected: 16 passed.

- [ ] **Step 5: Run the whole backend suite for regressions**

```bash
pytest tests/backend -q
```

Expected: no new failures. If `tests/backend` has pre-existing failures, capture the baseline first with `git stash && pytest tests/backend -q; git stash pop` and compare — do not claim a clean run you did not get.

- [ ] **Step 6: Commit**

```bash
git add src/api/routers/connect.py tests/backend/test_api_connect.py
git commit -m "feat: Add authenticated export upload endpoint"
```

---

### Task 7: API key management UI

**Files:**
- Modify: `frontend/index.html`
- Create: `frontend/js/api-keys.js`
- Modify: `frontend/locales/en.json`, `frontend/locales/de.json`

**Interfaces:**
- Consumes: the endpoints from Task 4, and the global `api` client (`frontend/js/api.js`, `const api = new ApiClient()`), `showToast(type, title, message)`, and `settingsManager.switchTab(name)`.
- Produces: an **Integrations** settings tab listing keys with a create form and per-row revoke.

- [ ] **Step 1: Add the tab button**

In `frontend/index.html`, after the `orders` settings tab button (near line 1166):

```html
                    <button class="settings-tab" data-tab="integrations" onclick="settingsManager.switchTab('integrations')">
                        <span class="tab-icon">🔌</span>
                        <span class="tab-label" data-i18n="settings.tabIntegrations">Integrations</span>
                    </button>
```

- [ ] **Step 2: Add the tab pane**

Inside `<div class="settings-tab-content">`, as a sibling of the other `.tab-pane` divs. The id must be `<tab-name>-tab` to match `switchTab`:

```html
                    <!-- Integrations Tab -->
                    <div class="tab-pane" id="integrations-tab">
                        <div class="card settings-section">
                            <div class="card-header">
                                <h3 data-i18n="settings.apiKeysHeading">🔑 API Keys</h3>
                            </div>
                            <div class="card-body">
                                <p class="form-text text-muted" data-i18n="settings.apiKeysDescription">
                                    API keys let Printernizer Connect upload from PrusaSlicer. A key is shown once, when you create it.
                                </p>

                                <div class="form-group">
                                    <label for="apiKeyName" data-i18n="settings.apiKeyNameLabel">Name</label>
                                    <input type="text" id="apiKeyName" class="form-control" maxlength="100"
                                           data-i18n-placeholder="settings.apiKeyNamePlaceholder"
                                           placeholder="e.g. Workshop laptop">
                                    <button class="btn btn-primary" style="margin-top:0.5rem;" onclick="createApiKey()">
                                        <span class="btn-icon">➕</span>
                                        <span data-i18n="settings.apiKeyCreate">Create key</span>
                                    </button>
                                </div>

                                <div id="apiKeyReveal" style="display:none;" class="alert alert-warning">
                                    <strong data-i18n="settings.apiKeyRevealTitle">Copy this key now</strong>
                                    <p data-i18n="settings.apiKeyRevealBody">It will not be shown again.</p>
                                    <code id="apiKeyRevealValue" style="word-break:break-all;"></code>
                                </div>

                                <div id="apiKeyList"></div>
                            </div>
                        </div>
                    </div>
```

- [ ] **Step 3: Write the UI script**

`frontend/js/api-keys.js`:

```javascript
/**
 * API key management for the Integrations settings tab.
 *
 * Keys authenticate Printernizer Connect, the PrusaSlicer companion. The
 * plaintext of a key is available only in the create response, so it is shown
 * once and never re-fetched.
 */

async function loadApiKeys() {
    const container = document.getElementById('apiKeyList');
    if (!container) return;

    try {
        const response = await api.request('/api/v1/settings/api-keys');
        const keys = response.data.keys || [];

        if (keys.length === 0) {
            container.innerHTML =
                `<p class="form-text text-muted" data-i18n="settings.apiKeysEmpty">No API keys yet.</p>`;
            return;
        }

        container.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th data-i18n="settings.apiKeyNameLabel">Name</th>
                        <th data-i18n="settings.apiKeyCreated">Created</th>
                        <th data-i18n="settings.apiKeyLastUsed">Last used</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${keys.map(key => `
                        <tr>
                            <td>${escapeHtml(key.name)}</td>
                            <td>${formatKeyDate(key.created_at)}</td>
                            <td>${formatKeyDate(key.last_used_at)}</td>
                            <td>
                                <button class="btn btn-danger btn-sm"
                                        onclick="revokeApiKey('${escapeHtml(key.id)}')">
                                    <span data-i18n="settings.apiKeyRevoke">Revoke</span>
                                </button>
                            </td>
                        </tr>`).join('')}
                </tbody>
            </table>`;
    } catch (error) {
        Logger.error('Failed to load API keys:', error);
        showToast('error', t('common.error'), t('settings.apiKeysLoadFailed'));
    }
}

async function createApiKey() {
    const input = document.getElementById('apiKeyName');
    const name = (input?.value || '').trim();

    if (!name) {
        showToast('warning', t('common.error'), t('settings.apiKeyNameRequired'));
        return;
    }

    try {
        const response = await api.request('/api/v1/settings/api-keys', {
            method: 'POST',
            body: JSON.stringify({ name })
        });

        document.getElementById('apiKeyRevealValue').textContent = response.data.key;
        document.getElementById('apiKeyReveal').style.display = 'block';
        input.value = '';

        showToast('success', t('common.success'), t('settings.apiKeyCreated'));
        await loadApiKeys();
    } catch (error) {
        Logger.error('Failed to create API key:', error);
        showToast('error', t('common.error'), t('settings.apiKeyCreateFailed'));
    }
}

async function revokeApiKey(keyId) {
    if (!confirm(t('settings.apiKeyRevokeConfirm'))) return;

    try {
        await api.request(`/api/v1/settings/api-keys/${encodeURIComponent(keyId)}`,
                          { method: 'DELETE' });
        showToast('success', t('common.success'), t('settings.apiKeyRevoked'));
        await loadApiKeys();
    } catch (error) {
        Logger.error('Failed to revoke API key:', error);
        showToast('error', t('common.error'), t('settings.apiKeyRevokeFailed'));
    }
}

function formatKeyDate(value) {
    if (!value) return '—';
    try {
        return new Date(value).toLocaleString();
    } catch {
        return value;
    }
}

function escapeHtml(value) {
    const div = document.createElement('div');
    div.textContent = String(value ?? '');
    return div.innerHTML;
}
```

- [ ] **Step 4: Check the helper names actually exist before wiring it up**

`escapeHtml`, `t`, `showToast` and `Logger` may already be defined globally; a duplicate `escapeHtml` would shadow or clash.

```bash
cd /Users/sebastianseubert/Developer/printernizer
grep -rn "function escapeHtml\|const escapeHtml" frontend/js/ | head
grep -rn "function t(\|window.t =" frontend/js/i18n.js | head -3
grep -rn "function showToast" frontend/js/ | head -3
```

If `escapeHtml` already exists globally, delete the local copy from `api-keys.js` and use the existing one. If `t` is not a global function, use the accessor the codebase actually provides.

- [ ] **Step 5: Load the script**

In `frontend/index.html`, next to the other `settings`-related script tags:

```html
    <script src="js/api-keys.js"></script>
```

Then make the tab load its data. In `frontend/js/settings.js`, inside `switchTab(tabName)` after the pane is activated:

```javascript
            if (tabName === 'integrations' && typeof loadApiKeys === 'function') {
                loadApiKeys();
            }
```

- [ ] **Step 6: Add the translation strings**

Add to the `settings` object in **both** `frontend/locales/en.json` and `frontend/locales/de.json`. English:

```json
"tabIntegrations": "Integrations",
"apiKeysHeading": "🔑 API Keys",
"apiKeysDescription": "API keys let Printernizer Connect upload from PrusaSlicer. A key is shown once, when you create it.",
"apiKeysEmpty": "No API keys yet.",
"apiKeysLoadFailed": "Could not load API keys",
"apiKeyNameLabel": "Name",
"apiKeyNamePlaceholder": "e.g. Workshop laptop",
"apiKeyNameRequired": "Give the key a name first",
"apiKeyCreate": "Create key",
"apiKeyCreated": "API key created",
"apiKeyCreateFailed": "Could not create the API key",
"apiKeyRevealTitle": "Copy this key now",
"apiKeyRevealBody": "It will not be shown again.",
"apiKeyCreatedCol": "Created",
"apiKeyLastUsed": "Last used",
"apiKeyRevoke": "Revoke",
"apiKeyRevokeConfirm": "Revoke this key? Any companion using it stops working immediately.",
"apiKeyRevoked": "API key revoked",
"apiKeyRevokeFailed": "Could not revoke the API key"
```

German equivalents go in `de.json` under the same keys. Note the HTML uses `data-i18n="settings.apiKeyCreated"` for the table column — rename that attribute to `settings.apiKeyCreatedCol` so it does not collide with the toast message key.

- [ ] **Step 7: Verify both locale files are still valid JSON and have matching keys**

```bash
cd /Users/sebastianseubert/Developer/printernizer
python3 -c "
import json
en=json.load(open('frontend/locales/en.json'))['settings']
de=json.load(open('frontend/locales/de.json'))['settings']
new=[k for k in en if k.startswith('apiKey') or k=='tabIntegrations']
missing=[k for k in new if k not in de]
print('new keys:', len(new))
assert not missing, f'missing in de.json: {missing}'
print('locales OK')
"
```

Expected: `locales OK`

- [ ] **Step 8: Verify the UI by hand**

Start the server, open Settings → Integrations, create a key, confirm the plaintext appears once and the row shows up, then revoke it.

```bash
python src/main.py
```

Check: the key value is shown exactly once; reloading the page does not show it again; the list shows name/created/last-used; revoke removes the row.

- [ ] **Step 9: Commit**

```bash
git add frontend/index.html frontend/js/api-keys.js frontend/js/settings.js \
        frontend/locales/en.json frontend/locales/de.json
git commit -m "feat: Add API key management UI to settings"
```

---

### Task 8: Documentation and spec correction

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md` (§8.2 printer fields)
- Create: `docs/api/connect.md`

**Interfaces:**
- Consumes: the endpoints built in Tasks 4–6.
- Produces: user-facing documentation of the Connect API and a corrected spec.

- [ ] **Step 1: Correct the spec's printer fields**

Spec §8.2 says `/connect/info` returns `printers: [{id, name, printer_model, manufacturer}]`. The `Printer` model has no `printer_model` or `manufacturer` — those live on library *files*, not printers. Change that line to:

```
| `GET /info` | `{server_version, min_connect_version, capabilities: {exports, profiles, printhost}, printers: [{id, name, type, is_active}]}` — `type` is the `PrinterType` value (`bambu_lab`, `prusa`). The `Printer` model carries no `printer_model`/`manufacturer` fields. |
```

Also note in §8.2 that M1's `/exports` accepts only `is_business` and `notes`, rejecting unknown fields, and that order/customer linking and `print_on` arrive in M3.

- [ ] **Step 2: Write the API documentation**

`docs/api/connect.md`, covering: what Connect is, how to create a key in the UI, both auth header forms, and each endpoint with a `curl` example. Include this working example:

```bash
# Discover capabilities
curl -s -H "X-Api-Key: pk_your_key_here" \
  http://printernizer.local:8000/api/v1/connect/info | jq

# Upload an export
curl -s -X POST \
  -H "X-Api-Key: pk_your_key_here" \
  -F "file=@benchy.gcode" \
  -F 'metadata={"is_business":true,"notes":"Order 42"}' \
  http://printernizer.local:8000/api/v1/connect/exports | jq
```

State plainly that only `/api/v1/connect/*` requires a key and the rest of the API does not, so nobody mistakes this for site-wide authentication.

- [ ] **Step 3: Add the changelog entry**

Under a new `## [Unreleased]` section in `CHANGELOG.md` (or the current unreleased section if one exists):

```markdown
### Added
- API keys for authenticating external tools, managed under Settings → Integrations
- `GET /api/v1/connect/info` — server capability and printer discovery
- `POST /api/v1/connect/exports` — authenticated upload of slicer exports into the library

### Notes
- API keys protect only `/api/v1/connect/*`. The rest of the API and the web UI remain unauthenticated.
```

- [ ] **Step 4: Run the full test suite one more time**

```bash
pytest tests/backend -q
```

Expected: no new failures relative to the baseline captured in Task 6 Step 5.

- [ ] **Step 5: Commit and push**

```bash
git add CHANGELOG.md docs/api/connect.md \
        docs/superpowers/specs/2026-09-06-printernizer-connect-design.md
git commit -m "docs: Document the Connect API and correct spec printer fields"
git push -u origin feature/connect-m1-server
```

- [ ] **Step 6: Open the pull request**

```bash
gh pr create --base master \
  --title "feat: API keys and Connect router (M1)" \
  --body "$(cat <<'BODY'
Implements M1 of the Printernizer Connect design: authenticated endpoints for
the PrusaSlicer desktop companion.

- `api_keys` table (migration 040), repository and service; only SHA-256 hashes
  are stored and a key's plaintext is shown exactly once
- `require_api_key` dependency accepting `X-Api-Key` or `Authorization: Bearer`
- `GET /api/v1/connect/info` — server version, capabilities, printer fleet
- `POST /api/v1/connect/exports` — authenticated upload, delegating to the
  existing library upload path
- Key management under Settings → Integrations

Scope: API keys protect only `/api/v1/connect/*`. The rest of the API and the
web UI stay unauthenticated, as agreed in the design (§8.1). Order/customer
linking and `print_on` land in M3 with the provenance stamps that feed them.

Spec: `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md`
Plan: `docs/superpowers/plans/2026-09-06-connect-m1-server.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"
```
