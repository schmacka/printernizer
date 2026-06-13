"""
Repository for OpenSCAD generator data (renders and parameter presets).
"""
import json
from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository


class OpenSCADRepository(BaseRepository):
    """Data access for OpenSCAD renders and presets."""

    # ---- Renders -----------------------------------------------------------

    async def create_render(self, render: Dict[str, Any]) -> None:
        """Persist a render record."""
        await self._execute_write(
            """
            INSERT INTO openscad_renders
                (id, source_ref, parameters, format, status, work_dir,
                 model_path, preview_path, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                render["id"],
                render["source_ref"],
                json.dumps(render.get("parameters", {})),
                render.get("format", "stl"),
                render.get("status", "pending"),
                render.get("work_dir"),
                render.get("model_path"),
                render.get("preview_path"),
                render.get("error"),
            ),
        )

    async def update_render(self, render_id: str, fields: Dict[str, Any]) -> None:
        """Update mutable fields of a render record."""
        if not fields:
            return
        columns = ", ".join(f"{key} = ?" for key in fields)
        values = list(fields.values())
        values.append(render_id)
        await self._execute_write(
            f"UPDATE openscad_renders SET {columns} WHERE id = ?", tuple(values)
        )

    async def get_render(self, render_id: str) -> Optional[Dict[str, Any]]:
        row = await self._fetch_one(
            "SELECT * FROM openscad_renders WHERE id = ?", [render_id]
        )
        if row and row.get("parameters"):
            row["parameters"] = json.loads(row["parameters"])
        return row

    # ---- Presets -----------------------------------------------------------

    async def create_preset(self, preset: Dict[str, Any]) -> None:
        await self._execute_write(
            """
            INSERT INTO openscad_presets (id, template_id, name, parameters)
            VALUES (?, ?, ?, ?)
            """,
            (
                preset["id"],
                preset["template_id"],
                preset["name"],
                json.dumps(preset.get("parameters", {})),
            ),
        )

    async def list_presets(self, template_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if template_id:
            rows = await self._fetch_all(
                "SELECT * FROM openscad_presets WHERE template_id = ? ORDER BY created_at DESC",
                [template_id],
            )
        else:
            rows = await self._fetch_all(
                "SELECT * FROM openscad_presets ORDER BY created_at DESC"
            )
        for row in rows:
            if row.get("parameters"):
                row["parameters"] = json.loads(row["parameters"])
        return rows

    async def delete_preset(self, preset_id: str) -> None:
        await self._execute_write(
            "DELETE FROM openscad_presets WHERE id = ?", (preset_id,)
        )
