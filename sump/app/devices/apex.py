from datetime import datetime, timezone

import httpx

import config
from devices.base import DeviceDriver


class ApexDriver(DeviceDriver):
    """
    Doesn't talk to the Apex unit directly - rides on top of the existing
    apex-ha HA integration (itchannel/apex-ha), which already exposes the
    Apex's probes as HA sensor entities. This driver just reads today's
    history for whichever entities the user maps in the addon options and
    computes a daily average per parameter.
    """
    name = "apex"

    def __init__(self):
        self.entities = config.apex_entities()

    async def collect_daily_averages(self) -> list[dict]:
        if not self.entities or not config.SUPERVISOR_TOKEN:
            return []

        start_of_day = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()

        headers = {
            "Authorization": f"Bearer {config.SUPERVISOR_TOKEN}",
            "Content-Type": "application/json",
        }

        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            for mapping in self.entities:
                entity_id = mapping.get("entity_id")
                parameter = mapping.get("parameter")
                unit = mapping.get("unit")
                if not entity_id or not parameter:
                    continue

                url = f"{config.SUPERVISOR_API}/history/period/{start_of_day}"
                try:
                    resp = await client.get(
                        url,
                        params={"filter_entity_id": entity_id, "minimal_response": "true"},
                        headers=headers,
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                except (httpx.HTTPError, ValueError):
                    continue

                if not payload or not payload[0]:
                    continue

                values = []
                for state in payload[0]:
                    raw = state.get("state")
                    try:
                        values.append(float(raw))
                    except (TypeError, ValueError):
                        continue

                if not values:
                    continue

                average = sum(values) / len(values)
                results.append({"parameter": parameter, "value": round(average, 3), "unit": unit})

        return results
