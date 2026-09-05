"""The Sump integration.

v1 scope: local, read-only monitoring of a Neptune Apex controller,
exposed two ways:

1. Home Assistant sensors, so you get history/graphing and automations
   for free from Home Assistant's own tools (see sensor.py).
2. A dedicated "Sump" sidebar panel with its own page -- an at-a-glance,
   Fusion-style overview that needs no dashboard editing (see
   frontend/sump-panel.js and websocket.py).

See README.md for the roadmap (outlet control, additional
manufacturers).
"""

from __future__ import annotations

import os

from homeassistant.components import panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SumpCoordinator
from .websocket import async_setup_websocket

PLATFORMS: list[str] = ["sensor"]

PANEL_URL_PATH = DOMAIN
PANEL_TITLE = "Sump"
# If mdi:fishbowl doesn't render on your Home Assistant/MDI version, any
# other Material Design Icon name works here -- mdi:fish is a safe swap.
PANEL_ICON = "mdi:fishbowl"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sump from a config entry."""
    coordinator = SumpCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # The panel and its WebSocket command are shared across every
    # configured device, so only register them once, on the first entry.
    is_first_entry = DOMAIN not in hass.data

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if is_first_entry:
        async_setup_websocket(hass)
        await _async_register_panel(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the Sump sidebar panel (once, the first time it's needed)."""
    if PANEL_URL_PATH in hass.data.get("frontend_panels", {}):
        return

    panel_dir = os.path.join(os.path.dirname(__file__), "frontend")
    static_url = f"/{DOMAIN}_static"

    await hass.http.async_register_static_paths(
        [StaticPathConfig(static_url, panel_dir, cache_headers=False)]
    )

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="sump-panel",
        frontend_url_path=PANEL_URL_PATH,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url=f"{static_url}/sump-panel.js",
        embed_iframe=False,
        require_admin=False,
    )
