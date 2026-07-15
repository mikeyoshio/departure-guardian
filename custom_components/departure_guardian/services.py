from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv

from .const import CONF_POSITIONS, CONF_X, CONF_Y, DOMAIN

SERVICE_SET_POSITION = "set_position"

SET_POSITION_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry_id"): str,
        vol.Required("entity_id"): cv.entity_id,
        vol.Required(CONF_X): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
        vol.Required(CONF_Y): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
    }
)


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SET_POSITION):
        return

    async def _handle_set_position(call: ServiceCall) -> None:
        entry = hass.config_entries.async_get_entry(call.data["config_entry_id"])
        if entry is None:
            return

        positions = dict(entry.options.get(CONF_POSITIONS, {}))
        positions[call.data["entity_id"]] = {
            CONF_X: call.data[CONF_X],
            CONF_Y: call.data[CONF_Y],
        }
        hass.config_entries.async_update_entry(
            entry, options={**entry.options, CONF_POSITIONS: positions}
        )

    hass.services.async_register(
        DOMAIN, SERVICE_SET_POSITION, _handle_set_position, schema=SET_POSITION_SCHEMA
    )
