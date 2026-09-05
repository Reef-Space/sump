"""Config flow for Sump -- point-and-click setup, no YAML.

Settings > Devices & services > Add integration > "Sump" walks
the user through this one screen: enter the controller's IP address (or
apex.local-style hostname), and we try a live connection before letting
setup finish, so mistakes are caught immediately instead of producing a
silently-broken device.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .apex_client import ApexConnectionError, ApexLocalClient
from .const import CONF_HOST, DEFAULT_NAME, DOMAIN

STEP_USER_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class SumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sump."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """First (and currently only) setup step."""
        errors: dict[str, str] = {}

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

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
