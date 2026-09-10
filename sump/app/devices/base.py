"""
Sump's device drivers turn "readings from some piece of aquarium equipment"
into water_tests rows. Each brand/protocol gets its own driver implementing
this interface, so new equipment support (wifi/zigbee/bluetooth controllers,
dosers, etc.) can be added without touching the storage or dashboard layer.

Today only ApexDriver (reading via the apex-ha HA integration's entities)
is implemented, but this is the extension point for multi-brand support.
"""
from abc import ABC, abstractmethod


class DeviceDriver(ABC):
    name: str = "base"

    @abstractmethod
    async def collect_daily_averages(self) -> list[dict]:
        """
        Return a list of {parameter, value, unit} dicts representing
        today's average reading for each configured sensor on this device.
        """
        raise NotImplementedError
