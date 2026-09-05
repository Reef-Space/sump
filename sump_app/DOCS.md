# Sump

A live, Fusion-style dashboard for every tank connected through the
**Sump** Home Assistant integration.

## Before you install this

This App needs the **Sump integration** installed and set up first
(Settings → Devices & services → Add integration → Sump). This App is
just the dashboard on top of it -- it doesn't talk to your Apex
directly, and has nothing to show until the integration has at least
one device configured.

## What it needs

- `homeassistant_api: true` (already set) -- lets this App read data
  from the Sump integration through Home Assistant's own API, rather
  than needing any network or credential setup of its own.

## After installing

Start the app, then look for **Sump** in your sidebar.

## Something wrong?

- **Sidebar icon never appears / dashboard is blank:** check the Log
  tab for this app. The most common cause is the Sump integration not
  being installed yet, or not having any device configured.
- **A reading looks wrong:** that's a bug in the Sump integration's
  Apex parsing, not this App -- please open an issue on the main
  repository with a copy of your Apex's `status.xml`.
