"""DataUpdateCoordinator for Sump.

One coordinator instance is created per configured Apex (per config
entry). It polls status.xml on a timer and hands the parsed snapshot to
every entity, so we make exactly one HTTP request per interval no matter
how many sensors exist.
"""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .apex_client import ApexConnectionError, ApexLocalClient, ApexStatus
from .const import CONF_HOST, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SumpCoordinator(DataUpdateCoordinator[ApexStatus]):
    """Polls one Apex controller and hands its status to entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.client = ApexLocalClient(
            async_get_clientsession(hass), entry.data[CONF_HOST]
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> ApexStatus:
        try:
            return await self.client.async_get_status()
        except ApexConnectionError as err:
            raise UpdateFailed(str(err)) from err
