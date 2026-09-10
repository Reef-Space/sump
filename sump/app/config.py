"""
Reads Home Assistant addon options and environment.

Addon options are written by the Supervisor to /data/options.json.
When running outside of HA (e.g. local dev), falls back to a local
options.json in the app directory and a plain SQLite file in ./data.
"""
import json
import os

OPTIONS_PATH = "/data/options.json" if os.path.exists("/data") else "options.dev.json"
DATA_DIR = "/data" if os.path.exists("/data") else "./data"
DB_PATH = os.path.join(DATA_DIR, "sump.db")

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
SUPERVISOR_API = "http://supervisor/core/api"


def load_options() -> dict:
    try:
        with open(OPTIONS_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"apex_entities": []}


def apex_entities() -> list[dict]:
    """List of {entity_id, parameter, unit} mappings configured by the user."""
    return load_options().get("apex_entities", [])


os.makedirs(DATA_DIR, exist_ok=True)
