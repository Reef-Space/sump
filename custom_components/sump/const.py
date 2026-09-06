"""Constants for the Sump integration."""

DOMAIN = "sump"

CONF_HOST = "host"
CONF_TEMP_UNIT = "temp_unit"

TEMP_UNIT_FAHRENHEIT = "fahrenheit"
TEMP_UNIT_CELSIUS = "celsius"

DEFAULT_NAME = "Sump"
DEFAULT_SCAN_INTERVAL = 30  # seconds

MANUFACTURER_APEX = "Neptune Systems"

# Maps the "type" / "probe_type" tag from status.xml to a display unit.
# Apex reports raw numbers with no explicit unit in the XML itself, so
# these are the hobby-standard units for each probe type.
#
# "Temp" is deliberately NOT listed here. status.xml never states
# whether a controller is configured for Fahrenheit or Celsius, and
# guessing wrong here doesn't just mislabel the reading -- Home
# Assistant automatically converts temperature-device-class sensors
# from their declared native unit to whatever unit the instance is
# configured for, so a wrong native unit runs a real F<->C conversion
# on a number that was never in that unit, producing a genuinely wrong
# value (this is exactly what caused a 25.7 reading to show as -3.5).
# So this is asked for explicitly during setup instead -- see
# CONF_TEMP_UNIT in config_flow.py and its use in sensor.py.
PROBE_UNITS = {
    "pH": "pH",
    "ORP": "mV",
    "Cond": "ppt",
    "PAR": "µmol/m²/s",
}
