"""
Repository for model-generator data (parameter presets).

Geometry is generated client-side, so there are no server render records — only
named parameter presets persist. (The legacy ``generator_renders`` table from
migration 033 is left in place but unused.)
"""
import json
from typing import Any, Dict, List, Optional

from .base_repository import BaseRepository


class GeneratorRepository(BaseRepository):
    """Data access for generator parameter presets."""

    async def create_preset(self, preset: Dict[str, Any]) -> None:
        await self._execute_write(
            """
            INSERT INTO generator_presets (id, template_id, name, parameters)
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
                "SELECT * FROM generator_presets WHERE template_id = ? ORDER BY created_at DESC",
                [template_id],
            )
        else:
            rows = await self._fetch_all(
                "SELECT * FROM generator_presets ORDER BY created_at DESC"
            )
        for row in rows:
            if row.get("parameters"):
                row["parameters"] = json.loads(row["parameters"])
        return rows

    async def delete_preset(self, preset_id: str) -> None:
        await self._execute_write(
            "DELETE FROM generator_presets WHERE id = ?", (preset_id,)
        )
