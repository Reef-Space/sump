# Sump

# If you've stumbled across this page, please don't try to use it. It's entirely vibe coded and in very early stages and not worth the time or risk to your system

A free, open-source Home Assistant Add-on that acts as a central hub for
home aquariums — starting with a long-term water quality logbook (the
thing most UK zoos/aquariums currently keep in an Excel spreadsheet), and
designed to grow into a multi-brand equipment dashboard.

## What's in this first version

- **Manual water test logging** — parameter, value, unit, timestamp, notes.
- **Automatic daily averages from your Apex** — riding on top of the
  existing [apex-ha](https://github.com/itchannel/apex-ha) integration.
  You map whichever Apex entities you want tracked (temp, pH, alkalinity,
  NO3, PO4, or anything else it exposes) to a parameter name in the addon
  options, and once a day Sump averages that day's readings and logs them
  alongside your manual entries.
- **Target ranges** — set a high/low per parameter; out-of-range readings
  are flagged on the chart, in the log table, and counted in the stats panel.
- **Graphs & stats** — trend chart with the target range shaded, plus
  latest/average/min/max/days-out-of-range for whatever date range you pick.
- **CSV import/export** — export your log, or bulk-import your existing
  Excel/CSV records to migrate off the spreadsheet.
- **Its own sidebar page**, via Home Assistant ingress — no separate login,
  no extra port to expose.

All data lives in a local SQLite database in the addon's persistent
`/data` storage, so it survives HA database purges and reboots.

## Installing

1. In Home Assistant, go to **Settings → Add-ons → Add-on Store**.
2. Click the **⋮** menu (top right) → **Repositories**, and add:
   `https://github.com/Reef-Space/sump`
3. "Sump" should appear in the store — install it, then start it.
4. A "Sump" entry will appear in your sidebar.

## Configuring the Apex daily-average ingestion

In the addon's **Configuration** tab, add an entry per Apex sensor you want
tracked, e.g.:

```yaml
apex_entities:
  - entity_id: sensor.apex_temp
    parameter: temperature
    unit: "°C"
  - entity_id: sensor.apex_ph
    parameter: pH
    unit: ""
  - entity_id: sensor.apex_alk
    parameter: alkalinity
    unit: "dKH"
  - entity_id: sensor.apex_no3
    parameter: NO3
    unit: "ppm"
  - entity_id: sensor.apex_po4
    parameter: PO4
    unit: "ppm"
```

These `entity_id`s come from whatever apex-ha names your probes — check
**Developer Tools → States** in HA to confirm the exact entity IDs.

The ingestion job runs once daily at 23:55 UTC. To test it immediately
without waiting, call the addon's API directly (e.g. from HA's ingress
URL, or via `curl` from inside your network):

```
POST /api/ingest/run-now
```

## Local development (without Home Assistant)

```bash
cd sump/app
pip install -r requirements.txt --break-system-packages
python main.py
```

The app falls back to `./data/sump.db` and `options.dev.json` when
`/data` doesn't exist, so you can develop the dashboard/API without an
HA instance. The Apex ingestion job will simply find no `SUPERVISOR_TOKEN`
and skip itself in this mode — test it by POSTing entries manually instead.

## Architecture, and where this is going

```
sump/
├── config.yaml       # HA addon manifest (ingress, sidebar panel, options schema)
├── build.yaml        # base image per architecture
├── Dockerfile
└── app/
    ├── main.py        # FastAPI app: REST API + serves the dashboard
    ├── db.py           # SQLite schema/queries for water_tests + targets
    ├── ingestion.py    # daily scheduler that pulls in device driver readings
    ├── devices/
    │   ├── base.py     # DeviceDriver interface
    │   └── apex.py     # first driver: reads apex-ha entities via HA's history API
    └── static/         # dashboard frontend (vanilla JS + canvas charts, no CDN deps)
```

The `devices/` folder is the extension point for the original multi-brand
goal: any other aquarium equipment (wifi/zigbee/bluetooth, other brands'
controllers) becomes a new `DeviceDriver` implementation that turns its
readings into the same `water_tests` rows, without touching the storage
layer or dashboard. Apex (via apex-ha) is the first driver; more brands
can be added as separate drivers without anyone needing to touch the
logging/graphing code.

Ideas for next steps:
- More device drivers (other controller brands, dosers, ATO)
- Per-parameter trend alerts (HA notification when N days out of range)
- Multiple tanks/systems in one install
- PDF export of the logbook for compliance records
