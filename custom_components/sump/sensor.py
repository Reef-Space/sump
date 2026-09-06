"""Sensor entities for Sump (Neptune Apex, read-only in v1).

Entities are created dynamically from whatever status.xml actually
reports, rather than a fixed list -- so a Trident's Alk/Ca/Mg probes, a
Jr's simpler probe set, and a Classic's outputs all "just work" without
per-model code. New probes/outputs that appear after setup (e.g. you add
a module) are picked up automatically on the next successful poll.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_TEMP_UNIT, DOMAIN, MANUFACTURER_APEX, PROBE_UNITS, TEMP_UNIT_FAHRENHEIT
from .coordinator import SumpCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for a config entry, adding new ones as they appear."""
    coordinator: SumpCoordinator = hass.data[DOMAIN][entry.entry_id]

    known_probes: set[str] = set()
    known_outputs: set[str] = set()

    def _add_new_entities() -> None:
        status = coordinator.data
        if status is None:
            return

        new_entities: list[SensorEntity] = []
        for probe in status.probes:
            if probe.name in known_probes:
                continue
            known_probes.add(probe.name)
            new_entities.append(ApexProbeSensor(coordinator, entry, probe.name))
        for output in status.outputs:
            if output.name in known_outputs:
                continue
            known_outputs.add(output.name)
            new_entities.append(ApexOutputStateSensor(coordinator, entry, output.name))

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(_add_new_entities))


class _ApexEntityBase(CoordinatorEntity[SumpCoordinator], SensorEntity):
    """Shared device-grouping info so every entity lands under one device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SumpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        host = entry.data.get("host", entry.entry_id)
        self._device_key = f"{DOMAIN}_{entry.entry_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_key)},
            name=entry.title,
            manufacturer=MANUFACTURER_APEX,
            model="Apex",
            configuration_url=f"http://{host}",
        )


class ApexProbeSensor(_ApexEntityBase):
    """A single Apex probe reading (Temp, pH, ORP, Cond, ...)."""

    def __init__(
        self, coordinator: SumpCoordinator, entry: ConfigEntry, probe_name: str
    ) -> None:
        super().__init__(coordinator, entry)
        self._probe_name = probe_name
        self._attr_unique_id = f"{self._device_key}_probe_{probe_name}"
        self._attr_name = probe_name
        self._attr_state_class = SensorStateClass.MEASUREMENT

        # What the user told us during setup, not a guess: see the
        # PROBE_UNITS comment in const.py for why this matters more
        # than a cosmetic label. Declaring the wrong native unit here
        # makes Home Assistant's automatic F<->C conversion corrupt
        # the value, not just mislabel it.
        temp_unit_choice = entry.data.get(CONF_TEMP_UNIT, TEMP_UNIT_FAHRENHEIT)
        self._temp_native_unit = (
            UnitOfTemperature.FAHRENHEIT
            if temp_unit_choice == TEMP_UNIT_FAHRENHEIT
            else UnitOfTemperature.CELSIUS
        )

    def _probe(self) -> Any:
        status = self.coordinator.data
        if status is None:
            return None
        return next((p for p in status.probes if p.name == self._probe_name), None)

    @property
    def native_value(self) -> Any:
        probe = self._probe()
        return probe.value if probe else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        probe = self._probe()
        if not probe or not probe.probe_type:
            return None
        if probe.probe_type == "Temp":
            return self._temp_native_unit
        return PROBE_UNITS.get(probe.probe_type)

    @property
    def device_class(self) -> SensorDeviceClass | None:
        probe = self._probe()
        if probe and probe.probe_type == "Temp":
            return SensorDeviceClass.TEMPERATURE
        return None

    @property
    def available(self) -> bool:
        return super().available and self._probe() is not None


class ApexOutputStateSensor(_ApexEntityBase):
    """Read-only state of an Apex output/outlet.

    This is deliberately a sensor, not a switch: v1 can't actually turn
    anything on or off (see apex_client.py docstring), and a switch
    entity that can't be switched would be misleading. Toggle support is
    the natural v2 addition once the authenticated write API is in.
    """

    def __init__(
        self, coordinator: SumpCoordinator, entry: ConfigEntry, output_name: str
    ) -> None:
        super().__init__(coordinator, entry)
        self._output_name = output_name
        self._attr_unique_id = f"{self._device_key}_output_{output_name}"
        self._attr_name = f"{output_name} state"
        self._attr_icon = "mdi:power-socket-us"

    def _output(self) -> Any:
        status = self.coordinator.data
        if status is None:
            return None
        return next((o for o in status.outputs if o.name == self._output_name), None)

    @property
    def native_value(self) -> Any:
        output = self._output()
        return output.state if output else None

    @property
    def available(self) -> bool:
        return super().available and self._output() is not None
