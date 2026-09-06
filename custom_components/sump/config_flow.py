"""Config flow for Sump -- point-and-click setup, no YAML.

Settings > Devices & services > Add integration > "Sump" walks the
user through one screen: the controller's IP address, and which
temperature unit it's configured to report in. That second question
matters more than it looks -- see the comment on PROBE_UNITS in
const.py for why guessing it wrong doesn't just mislabel the reading,
it corrupts it.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .apex_client import ApexConnectionError, ApexLocalClient
from .const import (
    CONF_HOST,
    CONF_TEMP_UNIT,
    DEFAULT_NAME,
    DOMAIN,
    TEMP_UNIT_CELSIUS,
    TEMP_UNIT_FAHRENHEIT,
)


class SumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sump."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """First (and currently only) setup step."""
        errors: dict[str, str] = {}

        # Default the temperature-unit choice to whatever unit system
        # this Home Assistant instance already uses -- right for most
        # people, and still overridable for the (rarer) case where an
        # Apex is set differently than the HA instance monitoring it.
        default_temp_unit = (
            TEMP_UNIT_FAHRENHEIT
            if self.hass.config.units.temperature_unit == UnitOfTemperature.FAHRENHEIT
            else TEMP_UNIT_CELSIUS
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TEMP_UNIT, default=default_temp_unit): vol.In(
                    [TEMP_UNIT_FAHRENHEIT, TEMP_UNIT_CELSIUS]
                ),
            }
        )

        if user_input is not None:
            host = user_input[CONF_HOST]
            client = ApexLocalClient(async_get_clientsession(self.hass), host)
            try:
                status = await client.async_get_status()
            except ApexConnectionError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(status.hostname or host)
                self._abort_if_unique_id_configured()
                title = status.hostname or DEFAULT_NAME
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
