# Aquarium Hub

A free, open-source Home Assistant integration that turns your aquarium
equipment into normal Home Assistant devices — so you get graphing,
history, alerts, and automations for your tank using the same tools you
already use for the rest of your house.

No cloud account. No subscription. Everything talks to your equipment
over your own local network.

> **Status: early v1.** Right now this supports **monitoring** a Neptune
> Apex controller (temperature, pH, ORP, salinity, and outlet states).
> It does not yet turn outlets on/off, and it doesn't yet support other
> brands — both are next. See [Roadmap](#roadmap).
>
> Not affiliated with or endorsed by Neptune Systems. Apex and Trident
> are trademarks of Neptune Systems, LLC.

## Why this exists

There are some great aquarium controllers out there, and some great
apps for logging your tank's history. What's been missing is a free,
open way to bring equipment from *different* manufacturers into one
place, using the automation engine and dashboards Home Assistant
already gives you for free. That's what this project is trying to be:
the "many brands, one dashboard" layer, built in the open so anyone can
add support for the hardware they own.

## What you need

- A working Home Assistant installation (Home Assistant OS, Container,
  Supervised, or Core all work).
- [HACS](https://hacs.xyz/) installed (the easiest way to install and
  update this).
- A Neptune Apex controller on the same local network as Home Assistant.

## Install

### Option A — HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add this repository's URL, choose category **Integration**, click
   **Add**.
4. Search HACS for **Aquarium Hub** and click **Download**.
5. Restart Home Assistant when prompted.

### Option B — Manual

1. Copy the `custom_components/aquarium_hub` folder from this repo into
   your Home Assistant `config/custom_components/` folder, so you end
   up with `config/custom_components/aquarium_hub/...`.
2. Restart Home Assistant.

## Set up your Apex

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Aquarium Hub**.
3. Enter your Apex's IP address or hostname (for example `192.168.1.50`
   or `apex.local`). No username or password needed for monitoring.
4. Home Assistant tests the connection before finishing setup, so
   you'll know right away if something's wrong (wrong IP, Apex is
   powered off, different network, etc).

That's it — a new device appears with one sensor per probe your Apex
reports (temperature, pH, ORP, salinity, and so on) plus one sensor per
output showing its current state. Home Assistant automatically starts
recording history for all of them, so **Settings → Devices & services →
Aquarium Hub → (your device)** already gives you graphs with zero extra
setup, and you can drop any of these entities onto a dashboard or use
them as automation triggers exactly like any other sensor.

### If sensors don't show up

Apex firmware has varied slightly over the years in how it labels
things internally. The parser is written to handle the common
variants, but if you set up the integration and nothing (or almost
nothing) appears:

1. Visit `http://<your-apex-ip>/cgi-bin/status.xml` directly in a
   browser — you should see raw XML.
2. Check the Home Assistant log for a warning from `aquarium_hub`.
3. Please open a GitHub issue and paste your `status.xml` (remove
   your Wi-Fi credentials if the software version block includes
   them) — that's the fastest way to get your model supported.

## Roadmap

Roughly in priority order:

- **Outlet control** — turn outlets/outputs on, off, or back to auto
  from Home Assistant, using Apex's authenticated API.
- **More manufacturers** — Red Sea ReefBeat, GHL, ESPHome-based DIY
  probes, and Zigbee/Bluetooth sensors as a first tier.
- **A dedicated dashboard app** — an auto-generated, Fusion-style
  overview (packaged as a Home Assistant Add-on) that builds itself
  from whatever devices you've connected, so there's no manual
  dashboard/card editing required.
- **Multi-tank support** — grouping devices by tank/Area cleanly when
  you have more than one system.

## Contributing

Pull requests welcome, especially:

- `status.xml` samples from Apex hardware/firmware combinations that
  don't parse cleanly today.
- Support for other controllers/probes/dosers.
- Dashboard ideas.

## License

MIT — see [LICENSE](LICENSE).
