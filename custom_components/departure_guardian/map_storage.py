from __future__ import annotations

from pathlib import Path

from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.core import HomeAssistant


async def async_save_map_upload(hass: HomeAssistant, entry_id: str, file_id: str) -> str:
    """Persist an uploaded floor-plan PNG under www/ and return its /local/ URL."""

    def _write() -> str:
        dest_dir = Path(hass.config.path("www", "departure_guardian"))
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{entry_id}.png"
        with process_uploaded_file(hass, file_id) as uploaded_path:
            dest_path.write_bytes(uploaded_path.read_bytes())
        return f"/local/departure_guardian/{entry_id}.png"

    return await hass.async_add_executor_job(_write)
