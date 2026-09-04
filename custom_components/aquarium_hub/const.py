"""Constants for the Aquarium Hub integration."""

DOMAIN = "aquarium_hub"

CONF_HOST = "host"

DEFAULT_NAME = "Aquarium Hub"
DEFAULT_SCAN_INTERVAL = 30  # seconds

MANUFACTURER_APEX = "Neptune Systems"

# Maps the "type" / "probe_type" tag from status.xml to a display unit.
# Apex reports raw numbers with no explicit unit in the XML itself, so
# these are the hobby-standard units for each probe type.
#
# Temperature is the one worth double-checking: it comes through as
# whatever your controller is configured to display (F or C), with no
# flag in the XML saying which. This defaults to Fahrenheit. If your
# Apex is set to Celsius, override the unit on the entity from
# Settings > Devices & services > Entities in Home Assistant (click the
# entity > cog icon > Unit of measurement), or open an issue and we can
# add a proper config option.
PROBE_UNITS = {
    "Temp": "°F",
    "pH": "pH",
    "ORP": "mV",
    "Cond": "ppt",
    "PAR": "µmol/m²/s",
}
