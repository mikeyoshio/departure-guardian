from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ARMED_STATES,
    ARMING_STATES,
    CONF_ALARM_ENTITY,
    CONF_ENTITY_ID,
    CONF_KIND,
    CONF_LABEL,
    CONF_NOTIFY_SERVICE,
    CONF_PROBLEM_STATE,
    CONF_THRESHOLD,
    CONF_WATCHED_ENTITIES,
    DOMAIN,
    KIND_BINARY,
    KIND_POWER,
)

PLATFORMS = ["binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = DepartureGuardianCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    coordinator.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


class DepartureGuardianCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.last_issues: list[str] = []
        self._unsub = None
        self._listeners: list[callback] = []

    @property
    def alarm_entity(self) -> str:
        return self.entry.options[CONF_ALARM_ENTITY]

    @property
    def notify_service(self) -> str:
        return self.entry.options[CONF_NOTIFY_SERVICE]

    @property
    def watched_entities(self) -> list[dict]:
        return self.entry.options.get(CONF_WATCHED_ENTITIES, [])

    def async_add_listener(self, callback_fn) -> None:
        self._listeners.append(callback_fn)

    def async_remove_listener(self, callback_fn) -> None:
        self._listeners.remove(callback_fn)

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()

    def async_start(self) -> None:
        self._unsub = async_track_state_change_event(
            self.hass, [self.alarm_entity], self._handle_alarm_change
        )

    def async_stop(self) -> None:
        if self._unsub:
            self._unsub()

    @callback
    def _handle_alarm_change(self, event: Event[EventStateChangedData]) -> None:
        new_state = event.data["new_state"]
        old_state = event.data["old_state"]
        if new_state is None or new_state.state not in ARMING_STATES + ARMED_STATES:
            return
        if old_state is not None and old_state.state in ARMING_STATES + ARMED_STATES:
            return

        self.hass.async_create_task(self._check_and_notify())

    async def _check_and_notify(self) -> None:
        issues = self._find_issues()
        self.last_issues = issues
        self._notify_listeners()
        if not issues:
            return

        message = "No se pudo verificar antes de armar:\n" + "\n".join(
            f"- {issue}" for issue in issues
        )
        await self.hass.services.async_call(
            "notify",
            self.notify_service,
            {"message": message, "title": "Departure Guardian"},
            blocking=False,
        )

    def _find_issues(self) -> list[str]:
        issues = []
        for watched in self.watched_entities:
            state = self.hass.states.get(watched[CONF_ENTITY_ID])
            if state is None:
                continue
            label = watched.get(CONF_LABEL, watched[CONF_ENTITY_ID])

            if watched[CONF_KIND] == KIND_BINARY:
                problem_state = watched.get(CONF_PROBLEM_STATE, "on")
                if state.state == problem_state:
                    issues.append(f"{label} sigue en estado '{state.state}'")
            elif watched[CONF_KIND] == KIND_POWER:
                threshold = float(watched.get(CONF_THRESHOLD, 5.0))
                try:
                    value = float(state.state)
                except (TypeError, ValueError):
                    continue
                if value > threshold:
                    issues.append(f"{label} consumiendo {value:.0f} W")
        return issues
