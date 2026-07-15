from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ALARM_ENTITY,
    CONF_ENTITY_ID,
    CONF_KIND,
    CONF_LABEL,
    CONF_NOTIFY_SERVICE,
    CONF_PROBLEM_STATE,
    CONF_THRESHOLD,
    CONF_WATCHED_ENTITIES,
    DEFAULT_PROBLEM_STATE,
    DEFAULT_THRESHOLD,
    DOMAIN,
    KIND_BINARY,
    KIND_POWER,
)
from .discovery import discover_candidates


class DepartureGuardianConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Departure Guardian",
                data={},
                options={
                    CONF_ALARM_ENTITY: user_input[CONF_ALARM_ENTITY],
                    CONF_NOTIFY_SERVICE: user_input[CONF_NOTIFY_SERVICE],
                    CONF_WATCHED_ENTITIES: [],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_ALARM_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="alarm_control_panel")
                ),
                vol.Required(CONF_NOTIFY_SERVICE): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DepartureGuardianOptionsFlow(config_entry)


class DepartureGuardianOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self._entry = config_entry
        self._watched = list(config_entry.options.get(CONF_WATCHED_ENTITIES, []))

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["discover", "add_entity", "remove_entity", "finish"],
        )

    async def async_step_discover(self, user_input=None):
        watched_ids = {w[CONF_ENTITY_ID] for w in self._watched}
        binary_candidates, power_candidates = discover_candidates(
            self.hass, watched_ids
        )

        if user_input is not None:
            for entity_id in user_input.get("binary_entities", []):
                state = self.hass.states.get(entity_id)
                label = state.attributes.get("friendly_name", entity_id) if state else entity_id
                self._watched.append(
                    {
                        CONF_ENTITY_ID: entity_id,
                        CONF_KIND: KIND_BINARY,
                        CONF_LABEL: label,
                        CONF_PROBLEM_STATE: DEFAULT_PROBLEM_STATE,
                    }
                )
            for entity_id in user_input.get("power_entities", []):
                state = self.hass.states.get(entity_id)
                label = state.attributes.get("friendly_name", entity_id) if state else entity_id
                self._watched.append(
                    {
                        CONF_ENTITY_ID: entity_id,
                        CONF_KIND: KIND_POWER,
                        CONF_LABEL: label,
                        CONF_THRESHOLD: DEFAULT_THRESHOLD,
                    }
                )
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Optional("binary_entities"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        include_entities=binary_candidates, multiple=True
                    )
                ),
                vol.Optional("power_entities"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        include_entities=power_candidates, multiple=True
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="discover",
            data_schema=schema,
            description_placeholders={
                "count": str(len(binary_candidates) + len(power_candidates))
            },
        )

    async def async_step_add_entity(self, user_input=None):
        if user_input is not None:
            kind = user_input[CONF_KIND]
            watched = {
                CONF_ENTITY_ID: user_input[CONF_ENTITY_ID],
                CONF_KIND: kind,
                CONF_LABEL: user_input.get(CONF_LABEL) or user_input[CONF_ENTITY_ID],
            }
            if kind == KIND_BINARY:
                watched[CONF_PROBLEM_STATE] = user_input.get(
                    CONF_PROBLEM_STATE, DEFAULT_PROBLEM_STATE
                )
            else:
                watched[CONF_THRESHOLD] = user_input.get(
                    CONF_THRESHOLD, DEFAULT_THRESHOLD
                )
            self._watched.append(watched)
            return await self.async_step_init()

        schema = vol.Schema(
            {
                vol.Required(CONF_ENTITY_ID): selector.EntitySelector(),
                vol.Required(CONF_KIND, default=KIND_BINARY): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=[KIND_BINARY, KIND_POWER])
                ),
                vol.Optional(CONF_LABEL): selector.TextSelector(),
                vol.Optional(
                    CONF_PROBLEM_STATE, default=DEFAULT_PROBLEM_STATE
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_THRESHOLD, default=DEFAULT_THRESHOLD
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(mode="box", unit_of_measurement="W")
                ),
            }
        )
        return self.async_show_form(step_id="add_entity", data_schema=schema)

    async def async_step_remove_entity(self, user_input=None):
        if not self._watched:
            return await self.async_step_init()

        if user_input is not None:
            index = int(user_input["entity"])
            self._watched.pop(index)
            return await self.async_step_init()

        options = [
            selector.SelectOptionDict(
                value=str(i), label=f"{e[CONF_LABEL]} ({e[CONF_ENTITY_ID]})"
            )
            for i, e in enumerate(self._watched)
        ]
        schema = vol.Schema(
            {
                vol.Required("entity"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options)
                )
            }
        )
        return self.async_show_form(step_id="remove_entity", data_schema=schema)

    async def async_step_finish(self, user_input=None):
        return self.async_create_entry(
            title="",
            data={
                CONF_ALARM_ENTITY: self._entry.options[CONF_ALARM_ENTITY],
                CONF_NOTIFY_SERVICE: self._entry.options[CONF_NOTIFY_SERVICE],
                CONF_WATCHED_ENTITIES: self._watched,
            },
        )
