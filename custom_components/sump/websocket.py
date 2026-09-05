"""WebSocket API for the Sump sidebar panel.

Exposes exactly one command, ``sump/get_status``, returning the latest
cached snapshot from every configured device's coordinator. This does
not trigger a new poll of the Apex -- it just serves whatever the
regular background refresh most recently fetched, the same data the
sensor entities are already showing.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, PROBE_UNITS
from .coordinator import SumpCoordinator


@callback
def async_setup_websocket(hass: HomeAssistant) -> None:
    """Register the panel's WebSocket command."""
    websocket_api.async_register_command(hass, websocket_get_status)


@websocket_api.websocket_command({"type": "sump/get_status"})
@websocket_api.async_response
async def websocket_get_status(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the latest known status for every configured device."""
    coordinators: dict[str, SumpCoordinator] = hass.data.get(DOMAIN, {})

    devices = []
    for coordinator in coordinators.values():
        status = coordinator.data
        entry = coordinator.entry
        devices.append(
            {
                "entry_id": entry.entry_id,
                "name": entry.title,
                "host": entry.data.get("host"),
                "available": coordinator.last_update_success,
                "probes": [
                    {
                        "name": probe.name,
                        "value": probe.value,
                        "unit": PROBE_UNITS.get(probe.probe_type),
                    }
                    for probe in (status.probes if status else [])
                ],
                "outputs": [
                    {"name": output.name, "state": output.state}
                    for output in (status.outputs if status else [])
                ],
            }
        )

    connection.send_result(msg["id"], {"devices": devices})
