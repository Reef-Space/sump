"""HTTP API for the Sump App.

Exposes ``GET /api/sump/status``, returning the same snapshot the
sensor entities are built from. The Sump App (a Home Assistant App,
formerly called an Add-on) calls this through the Supervisor's Home
Assistant Core proxy -- ``http://supervisor/core/api/sump/status`` --
to build its dashboard. Keeping this here means the actual
Apex-talking and XML-parsing logic lives in exactly one place: this
integration, not duplicated inside the App's own container.
"""

from __future__ import annotations

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PROBE_UNITS
from .coordinator import SumpCoordinator


class SumpStatusView(HomeAssistantView):
    """Read-only status endpoint consumed by the Sump App."""

    url = "/api/sump/status"
    name = "api:sump:status"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        """Return the latest known status for every configured device."""
        coordinators: dict[str, SumpCoordinator] = self.hass.data.get(DOMAIN, {})

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

        return self.json({"devices": devices})
