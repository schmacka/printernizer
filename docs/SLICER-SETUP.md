# Enabling slicing (the slicer service)

Printernizer does **not** slice inside the main app — slicing runs in a **separate
slicer service** (OrcaSlicer). If `GET /api/v1/slicing` returns `{"slicers": []}`,
the app can't reach a slicer yet, and the model detail view's **Slice** panel will
say *"No slicer/profile available."* Here's how to connect one.

The slicer image is published, multi-arch (amd64 + arm64):
`ghcr.io/schmacka/printernizer-slicer:latest`

## Option A — Docker Compose (standalone)

Already wired in `docker/docker-compose.yml` (the `slicer` service +
`SLICER_SERVICE_URL=http://slicer:8001`). Just:

```bash
docker compose -f docker/docker-compose.yml up -d
```

The app auto-registers the slicer on startup and seeds built-in profiles
(Bambu A1, Prusa CORE One).

## Option B — Home Assistant add-on

The HA add-on is a single container and can't run a sidecar, so the slicer runs as
a **second container** the add-on points at. Two ways:

1. **Run the slicer image anywhere on your network** (a NAS, a mini-PC, `docker run -d -p 8001:8001 ghcr.io/schmacka/printernizer-slicer:latest`), then in the **Printernizer add-on → Configuration**, set the slicer service URL to `http://<that-host>:8001`.
2. **Companion add-on** (`ha-addon/printernizer-slicer/` in this repo) — publish it into the `printernizer-ha` add-on repo as a second add-on, install it, and point `SLICER_SERVICE_URL` at it (`http://<addon-host>:8001`).

> Note: the slicer image needs glibc ≥ 2.38 (Ubuntu 24.04 base) and runs headless;
> it works on amd64 and arm64 (Raspberry Pi 4/5 class).

## Verify

```bash
curl http://<your-printernizer>:8000/api/v1/slicing      # should list 1 slicer
```

Once a slicer is registered, the **Slice** panel in a model's detail view will show
the curated profiles and let you Slice / Slice & Print.
