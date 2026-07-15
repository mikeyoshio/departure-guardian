from __future__ import annotations

from homeassistant.core import HomeAssistant

RELEVANT_BINARY_DEVICE_CLASSES = {
    "door",
    "window",
    "opening",
    "garage_door",
    "moisture",
}


def discover_candidates(
    hass: HomeAssistant, exclude: set[str]
) -> tuple[list[str], list[str]]:
    """Find entities already exposed by installed integrations that look
    like good departure-guardian candidates, based on domain/device_class
    only (no hardcoded integration names)."""
    binary_candidates: list[str] = []
    power_candidates: list[str] = []

    for state in hass.states.async_all():
        if state.entity_id in exclude:
            continue

        domain = state.entity_id.split(".", 1)[0]
        device_class = state.attributes.get("device_class")

        if domain == "binary_sensor" and device_class in RELEVANT_BINARY_DEVICE_CLASSES:
            binary_candidates.append(state.entity_id)
        elif domain == "sensor" and device_class == "power":
            power_candidates.append(state.entity_id)

    return binary_candidates, power_candidates
