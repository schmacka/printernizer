# Print Job Thumbnail Feature

Status: INITIAL IMPLEMENTATION COMPLETE (WebSocket + file endpoint). Frontend integration may still be pending.

## Goal
Display a preview image of the actively printing file on each printer dashboard tile to improve at-a-glance monitoring.

## Sources
- 3MF files often embed a PNG at Metadata/thumbnail.png (case variants)
- G-code: no embedded preview (use static placeholder or future layer renderer)
- Bambu A1 & Prusa Core One: rely on locally downloaded 3MF; device APIs do not stream thumbnails.

## Data Flow
1. File is downloaded (printer -> local) via `FileService.download_file`.
2. `process_file_thumbnails` parses the 3MF and stores a base64 thumbnail + metadata in DB.
3. When a printer status update maps a currently running job to a known file (by filename) it sets:
  - `current_job_file_id`
  - `current_job_has_thumbnail`
  - `current_job_thumbnail_url` (points to `/api/v1/files/{id}/thumbnail`)
4. WebSocket event `printer_status_update` now contains these new fields for live UI updates.
5. Frontend requests `/api/v1/files/{file_id}/thumbnail` only when displaying the tile image.

## Storage
No additional schema beyond existing file table fields (`has_thumbnail`, `thumbnail_data`, dimensions, format). Disk cache not yet implemented.

## API
Endpoint: `GET /api/v1/files/{id}/thumbnail` returns the primary (currently base64-stored) thumbnail as image (png/jpg) with caching headers.

Real-time WebSocket event payload fields added (event `printer_status_update`):
```
{
  "printer_id": "...",
  "status": "printing",
  "current_job": "example.3mf",
  "current_job_file_id": "printerid_example.3mf",
  "current_job_has_thumbnail": true,
  "current_job_thumbnail_url": "/api/v1/files/printerid_example.3mf/thumbnail",
  ...
}
```

## Configuration (Environment)
THUMBNAILS_ENABLED=true  
THUMBNAIL_CACHE_DIR=./data/thumbnails  
THUMBNAIL_MAX_EDGE=512  # (future: downscale large images)

## Caching & Performance
- Disk cache only; optional in-memory LRU later.
- Negative cache: set files.thumbnail_path = NULL; retry only on explicit invalidate.
- HTTP headers: Cache-Control: public, max-age=3600; ETag via file mtime/hash.

## Security
- Path safety: never extract arbitrary files; read only specific candidate paths.
- Authorization hook (future multi-user): verify access to file before serving.

## Frontend Behavior
State machine:
- loading → success (show img) | unavailable (placeholder).
Placeholder: lightweight SVG (printer icon).
CSS: fixed aspect-ratio (4/3) to prevent layout shift.

## Error Handling
Extraction failure logs warning only.
Return 404 for missing thumbnail; frontend keeps placeholder.

## Future Enhancements
- G-code layer preview renderer.
- Multiple resolution variants (e.g., 128px, 512px).
- Pre-warming during bulk file ingestion.

## Remaining Work
1. Frontend printer tile: display image if `current_job_thumbnail_url` present.
2. Optional: add disk-based thumbnail caching (convert base64 storage to files under `data/thumbnails/`).
3. Add tests covering: file download -> thumbnail extraction, WebSocket status includes URL when printing.
4. Optional future: generate preview for G-code (placeholder renderer).

## Frontend Integration Hint
When receiving a `printer_status_update` event:
```
if (data.current_job_has_thumbnail && data.current_job_thumbnail_url) {
  img.src = data.current_job_thumbnail_url;
} else {
  img.src = '/static/img/placeholder.svg';
}
```