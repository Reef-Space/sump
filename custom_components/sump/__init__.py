"""The Sump integration.

v1 scope: local, read-only monitoring of a Neptune Apex controller,
exposed two ways:

1. Home Assistant sensors, so you get history/graphing and automations
   for free from Home Assistant's own tools (see sensor.py).
2. A REST endpoint (see http_api.py) that the separate Sump App reads
   through the Supervisor's Core API proxy, to build its Fusion-style
   sidebar dashboard. The App lives in this same repo under sump_app/,
   but is installed separately (Settings > Add-ons/Apps), since apps
   and integrations are different Home Assistant mechanisms. The App
   requires Home Assistant OS or Supervised; this integration and its
   sensors work on every install type.

See README.md for the roadmap (outlet control, additional
manufacturers).
"""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SumpCoordinator
from .http_api import SumpStatusView

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sump from a config entry."""
    coordinator = SumpCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # The REST view is shared across every configured device, so only
    # register it once, on the first entry.
    is_first_entry = DOMAIN not in hass.data

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if is_first_entry:
        hass.http.register_view(SumpStatusView(hass))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
