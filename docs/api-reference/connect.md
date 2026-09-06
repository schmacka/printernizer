# Connect API

The Connect API is the interface used by **Printernizer Connect**, the desktop
companion that links a PrusaSlicer installation to a Printernizer server. It
lets a slicer discover what a server can do and push finished exports straight
into the library, instead of exporting to disk and uploading them by hand.

It is a normal REST API — anything that can send an HTTP request can use it.

Everything under `/api/v1/connect/` requires an API key. Nothing else does.

- Base URL: `http://<your-server>:8000/api/v1`
- Prefix: `/connect`
- Milestone: M1 (`info` and `exports`; profile sync and the print-host shim
  come later)

---

## What the API key is, and what it is not

Read this before you deploy anything that depends on it.

- **Only `/api/v1/connect/*` requires a key.** The rest of the API and the
  entire web UI are unauthenticated, exactly as before. Adding a key does not
  put a login in front of Printernizer.
- **Creating a key is itself unauthenticated.** `POST /settings/api-keys` sits
  in the open settings router, so anyone who can reach Printernizer over the
  network can mint a key for themselves. The key therefore identifies *which
  companion* is talking and gives Connect a credential to hold — it is **not**
  an access control boundary, and it does not secure the server.
- Treat Printernizer as what it is: a LAN application. If the machine is
  reachable from somewhere you do not trust, put a real reverse proxy with
  real authentication in front of the whole thing.

Keys are generated as `pk_` plus 32 random URL-safe bytes. Only a SHA-256 hash
is stored, so a key's plaintext is shown exactly once, at creation, and cannot
be recovered afterwards. Revoking a key takes effect immediately.

---

## Creating a key in the UI

1. Open Printernizer in a browser.
2. Go to **Settings → Integrations → API Keys**.
3. Enter a name that says which machine the key is for (e.g. `Workshop
   laptop`), and click **Create key**.
4. The plaintext key is revealed once, in a warning box. **Copy it now** — it
   will not be shown again.
5. Existing keys are listed below with their name, creation date and last-used
   time, each with a **Revoke** action.

Keys can also be managed over HTTP. These three endpoints are part of the
*settings* router and are **not** authenticated:

```bash
# Create a key (the plaintext appears only in this response)
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"name":"Workshop laptop"}' \
  http://printernizer.local:8000/api/v1/settings/api-keys | jq

# List key metadata (never the keys themselves)
curl -s http://printernizer.local:8000/api/v1/settings/api-keys | jq

# Revoke a key by id
curl -s -X DELETE \
  http://printernizer.local:8000/api/v1/settings/api-keys/<key_id> | jq
```

---

## Authentication

Send the key in **either** of these headers. If both are present, `X-Api-Key`
wins.

```http
X-Api-Key: pk_your_key_here
```

```http
Authorization: Bearer pk_your_key_here
```

A missing or unknown key returns **401** with the standard error envelope:

```json
{
  "status": "error",
  "message": "API key required",
  "error_code": "AUTHENTICATION",
  "details": { "reason": "API key required" },
  "timestamp": "2026-09-06T09:30:00.000000"
}
```

An unknown key reports `Invalid API key` in the same shape. The server does not
distinguish between "never existed" and "revoked".

---

## Home Assistant add-on users

The add-on is normally reached through Home Assistant **ingress**
(`/api/hassio_ingress/...`). Those URLs are session-authenticated in the
browser: they depend on a Home Assistant login cookie, and a CLI tool cannot
use them. Pointing Connect at an ingress URL will not work.

To use the Connect API with the add-on, **expose Printernizer's direct port**
in the add-on configuration and point Connect at
`http://<home-assistant-host>:8000` instead. See the design spec, section 9.

---

## Endpoints

### `GET /connect/info`

Reports the server version, the oldest companion release this server will talk
to, the feature flags a client should branch on, and the printer fleet. Connect
calls this before every command, both to check version compatibility and to
resolve printer ids.

```bash
# Discover capabilities
curl -s -H "X-Api-Key: pk_your_key_here" \
  http://printernizer.local:8000/api/v1/connect/info | jq
```

```json
{
  "status": "success",
  "data": {
    "server_version": "2.42.0",
    "min_connect_version": "0.1.0",
    "capabilities": {
      "exports": true,
      "profiles": false,
      "printhost": false
    },
    "printers": [
      {
        "id": "bambu_a1_01",
        "name": "Bambu Lab A1",
        "type": "bambu_lab",
        "is_active": true
      },
      {
        "id": "prusa_core_01",
        "name": "Prusa Core One",
        "type": "prusa_core",
        "is_active": true
      }
    ]
  }
}
```

Field notes:

| Field | Meaning |
|---|---|
| `server_version` | The running Printernizer version. |
| `min_connect_version` | Oldest Connect release accepted; currently `0.1.0`. A client older than this should refuse to run and tell the user to upgrade. |
| `capabilities.exports` | `true` in M1 — `POST /connect/exports` is available. |
| `capabilities.profiles` | Profile sync. `false` until M4. |
| `capabilities.printhost` | OctoPrint-compatible print-host shim. `false` until M5. |
| `printers[].type` | The `PrinterType` value: `bambu_lab`, `prusa_core`, `octoprint` or `unknown`. Printers carry no model/manufacturer fields — that information lives on library *files*. |
| `printers[].is_active` | Whether the printer is enabled for monitoring. |

Responses: `200` on success, `401` without a valid key.

### `POST /connect/exports`

Uploads a slicer export into the library. The request is `multipart/form-data`
with two parts:

| Part | Type | Required | Description |
|---|---|---|---|
| `file` | file | yes | The export. `.gcode`, `.bgcode` or `.3mf`. |
| `metadata` | text | no | A JSON object. Defaults to `{}`. |

The `metadata` object accepts exactly two keys in M1:

| Key | Type | Default | Description |
|---|---|---|---|
| `is_business` | boolean | `false` | Marks the file as a business order rather than a private model. |
| `notes` | string \| null | `null` | Free text stored with the library entry. |

**Unknown keys are rejected with a 422**, deliberately — the endpoint never
accepts a field it would silently drop, so a client is never told something was
stored when it was not. Order and customer linking, the source-checksum
provenance link and `print_on` (start the print immediately on a named printer)
arrive in **M3**.

The upload is handed to the same code path as a browser upload, so thumbnail
extraction, G-code metadata parsing and deduplication all behave identically.

```bash
# Upload an export
curl -s -X POST \
  -H "X-Api-Key: pk_your_key_here" \
  -F "file=@benchy.gcode" \
  -F 'metadata={"is_business":true,"notes":"Order 42"}' \
  http://printernizer.local:8000/api/v1/connect/exports | jq
```

```json
{
  "status": "success",
  "data": {
    "file": {
      "file_id": "6f1b0f2c-6f2b-4e1e-9a1c-1d2e3f4a5b6c",
      "filename": "benchy.gcode",
      "file_size": 2841923,
      "file_type": "gcode",
      "checksum": "9f2c…"
    }
  },
  "message": "Export added to library"
}
```

Field notes:

| Field | Meaning |
|---|---|
| `file_id` | Id of the row in the `files` table for this upload. |
| `filename` | The name the file was stored under. |
| `file_size` | Size in bytes. |
| `file_type` | Extension without the dot, e.g. `gcode`. |
| `checksum` | The library entry's primary key — use it with `/api/v1/library/*`. **May be `null`**: library ingestion is best-effort, so a server with the library system disabled, or one where ingestion failed, still stores the file and still returns `201`, but has no checksum to report. Clients that rely on the checksum for provenance must handle `null` rather than assume it is present. |

The response is a summary of the stored file, not the full library row. The
server-side filesystem path is deliberately not included.

Responses:

| Status | When |
|---|---|
| `201` | The file was added to the library. |
| `401` | Missing or invalid API key. |
| `403` | File uploads are disabled on this server (`enable_upload`). |
| `422` | Unsupported file extension, malformed `metadata` JSON, or an unknown metadata field. |
| `400` | The upload itself failed; `details.failed_files` says why. |

Library browsing and downloads use the existing, unauthenticated
`/api/v1/library/*` endpoints — they are unchanged and need no key.

---

## Troubleshooting

**401 on every request.** Check that the key is sent as `X-Api-Key` (or
`Authorization: Bearer`) and that it has not been revoked under Settings →
Integrations. A key's plaintext cannot be recovered — if it was not copied at
creation, revoke it and create a new one.

**422 "Invalid metadata".** Only `is_business` and `notes` are accepted in M1.
Anything else is a hard error rather than a silent drop.

**422 "Unsupported export type".** Only `.gcode`, `.bgcode` and `.3mf` are
accepted. `.bgcode` is Prusa's binary G-code, the Core One's default export.

**403 on upload.** Uploads are switched off server-side. Enable them in the
Printernizer configuration.

**Nothing reachable at all, on the Home Assistant add-on.** You are probably
using an ingress URL; see the section above.

---

## See also

- [API Reference index](index.md)
- Design spec: `docs/superpowers/specs/2026-09-06-printernizer-connect-design.md`
  (sections 8.1, 8.2 and 9)
