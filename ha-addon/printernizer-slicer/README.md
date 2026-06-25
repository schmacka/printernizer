# Printernizer Slicer — Home Assistant companion add-on

This directory holds the **companion HA add-on** for the standalone Printernizer
Slicer Service. A Home Assistant add-on is a single container, so the slicer
cannot run as a sidecar inside the main Printernizer add-on — it ships as a
**second add-on** that runs alongside it.

## Where these files belong

These files are meant to live in the **[printernizer-ha](https://github.com/schmacka/printernizer-ha)**
add-on repository as a second add-on directory (`printernizer-slicer/`), next to
the existing Printernizer add-on. They are kept here in the main repo for review
and version control; copy/sync them into printernizer-ha to publish the add-on.

## Wiring

1. Install and start **both** add-ons (Printernizer + Printernizer Slicer).
2. In the Printernizer add-on options, set the slicer service URL to the slicer
   add-on's hostname, e.g. `http://a0d7b954-printernizer-slicer:8001`
   (Home Assistant exposes add-ons on the internal Docker network by their slug
   hostname). Printernizer reads this via `SLICER_SERVICE_URL` and auto-registers
   the remote slicer on startup.

## Image

The add-on simply runs the published multi-arch slicer image
(`ghcr.io/schmacka/printernizer-slicer:latest`, `aarch64` + `amd64`). It is
self-contained (Ubuntu 24.04 base) and does not use the HA base image.
