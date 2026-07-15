from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
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
    CONF_MAP_CAMERA,
    CONF_MAP_IMAGE,
    CONF_NOTIFY_SERVICE,
    CONF_POSITIONS,
    CONF_PROBLEM_STATE,
    CONF_THRESHOLD,
    CONF_WATCHED_ENTITIES,
    DOMAIN,
    KIND_BINARY,
    KIND_POWER,
    MAP_CARD_FILENAME,
    STATIC_URL_BASE,
)
from .services import async_setup_services

PLATFORMS = ["binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    await _async_register_frontend_resources(hass)

    coordinator = DepartureGuardianCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    coordinator.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = hass.data[DOMAIN].pop(entry.entry_id)
    coordinator.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_frontend_resources(hass: HomeAssistant) -> None:
    if hass.data[DOMAIN].get("_frontend_registered"):
        return
    hass.data[DOMAIN]["_frontend_registered"] = True

    www_path = Path(__file__).parent / "www"
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL_BASE, str(www_path), False)]
        )
    except ImportError:
        hass.http.register_static_path(STATIC_URL_BASE, str(www_path), False)

    add_extra_js_url(hass, f"{STATIC_URL_BASE}/{MAP_CARD_FILENAME}")


class DepartureGuardianCoordinator:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.statuses: list[dict] = []
        self._unsub_alarm = None
        self._unsub_watched = None
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

    @property
    def map_camera(self) -> str | None:
        return self.entry.options.get(CONF_MAP_CAMERA)

    @property
    def map_image(self) -> str | None:
        return self.entry.options.get(CONF_MAP_IMAGE)

    @property
    def positions(self) -> dict:
        return self.entry.options.get(CONF_POSITIONS, {})

    @property
    def last_issues(self) -> list[str]:
        return [s["detail"] for s in self.statuses if s["problem"]]

    def async_add_listener(self, callback_fn) -> None:
        self._listeners.append(callback_fn)

    def async_remove_listener(self, callback_fn) -> None:
        self._listeners.remove(callback_fn)

    def _notify_listeners(self) -> None:
        for listener in self._listeners:
            listener()

    def async_start(self) -> None:
        self._unsub_alarm = async_track_state_change_event(
            self.hass, [self.alarm_entity], self._handle_alarm_change
        )
        watched_ids = [w[CONF_ENTITY_ID] for w in self.watched_entities]
        if watched_ids:
            self._unsub_watched = async_track_state_change_event(
                self.hass, watched_ids, self._handle_watched_change
            )
        self._refresh_statuses()

    def async_stop(self) -> None:
        if self._unsub_alarm:
            self._unsub_alarm()
        if self._unsub_watched:
            self._unsub_watched()

    @callback
    def _handle_watched_change(self, event: Event[EventStateChangedData]) -> None:
        self._refresh_statuses()
        self._notify_listeners()

    def _refresh_statuses(self) -> None:
        self.statuses = self._evaluate()

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
        self._refresh_statuses()
        self._notify_listeners()
        issues = self.last_issues
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

    def _evaluate(self) -> list[dict]:
        statuses = []
        for watched in self.watched_entities:
            entity_id = watched[CONF_ENTITY_ID]
            state = self.hass.states.get(entity_id)
            label = watched.get(CONF_LABEL, entity_id)
            problem = False
            detail = None

            if state is not None:
                if watched[CONF_KIND] == KIND_BINARY:
                    problem_state = watched.get(CONF_PROBLEM_STATE, "on")
                    if state.state == problem_state:
                        problem = True
                        detail = f"{label} sigue en estado '{state.state}'"
                elif watched[CONF_KIND] == KIND_POWER:
                    threshold = float(watched.get(CONF_THRESHOLD, 5.0))
                    try:
                        value = float(state.state)
                    except (TypeError, ValueError):
                        value = None
                    if value is not None and value > threshold:
                        problem = True
                        detail = f"{label} consumiendo {value:.0f} W"

            statuses.append(
                {
                    "entity_id": entity_id,
                    "label": label,
                    "problem": problem,
                    "detail": detail,
                }
            )
        return statuses
