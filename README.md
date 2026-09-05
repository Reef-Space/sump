# Sump

A free, open-source Home Assistant integration that turns your aquarium
equipment into normal Home Assistant devices — with its own dedicated
page in the sidebar for an at-a-glance, Fusion-style overview — so you
get graphing, history, alerts, and automations using the same tools you
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

## What you get

- **A "Sump" entry in your Home Assistant sidebar**, with its own
  full-page overview: every connected tank, every probe reading, and
  every outlet's state, laid out like an instrument panel. It builds
  itself from whatever your equipment actually reports — nothing to
  configure or lay out by hand.
- **Normal Home Assistant sensors** for the same data, so you
  automatically get history graphs, and can use any reading in an
  automation, script, or your own dashboard exactly like any other
  Home Assistant entity.

## Why this exists

There are some great aquarium controllers out there, and some great
apps for logging your tank's history. What's been missing is a free,
open way to bring equipment from *different* manufacturers into one
place, using the automation engine Home Assistant already gives you for
free. That's what this project is trying to be: the "many brands, one
dashboard" layer, built in the open so anyone can add support for the
hardware they own.

## What you need

- A working Home Assistant installation (Home Assistant OS, Container,
  Supervised, or Core all work — the sidebar panel is a normal
  integration feature, not an Add-on/App, so it doesn't require the
  Supervisor).
- [HACS](https://hacs.xyz/) installed (the easiest way to install and
  update this).
- A Neptune Apex controller on the same local network as Home Assistant.

## Install

### Option A — HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add this repository's URL, choose category **Integration**, click
   **Add**.
4. Search HACS for **Sump** and click **Download**.
5. Restart Home Assistant when prompted.

### Option B — Manual

1. Copy the `custom_components/sump` folder from this repo into your
   Home Assistant `config/custom_components/` folder, so you end up
   with `config/custom_components/sump/...`.
2. Restart Home Assistant.

## Set up your Apex

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Sump**.
3. Enter your Apex's IP address or hostname (for example `192.168.1.50`
   or `apex.local`). No username or password needed for monitoring.
4. Home Assistant tests the connection before finishing setup, so
   you'll know right away if something's wrong (wrong IP, Apex is
   powered off, different network, etc).

A **Sump** icon appears in your sidebar with a live overview, and a new
device appears under Settings → Devices & services with one sensor per
probe and outlet, already recording history.

### If sensors (or the panel) don't show up

Apex firmware has varied slightly over the years in how it labels
things internally. The parser handles the common variants, but if
almost nothing appears after setup:

1. Visit `http://<your-apex-ip>/cgi-bin/status.xml` directly in a
   browser — you should see raw XML.
2. Check the Home Assistant log for a warning from `sump`.
3. Please open a GitHub issue and paste your `status.xml` (remove
   any personal network info first) — that's the fastest way to get
   your model supported.

If sensors work but the sidebar panel doesn't appear, do a hard refresh
of the Home Assistant page in your browser (custom panels are loaded
once per page load) and check the browser console for errors.

## Roadmap

Roughly in priority order:

- **Trend graphs in the panel itself** — small history sparklines per
  reading, not just the current value.
- **Outlet control** — turn outlets/outputs on, off, or back to auto
  from Home Assistant, using Apex's authenticated API.
- **More manufacturers** — Red Sea ReefBeat, GHL, ESPHome-based DIY
  probes, and Zigbee/Bluetooth sensors as a first tier.
- **Multi-tank polish** — tabs in the panel once a few people are
  running more than one or two tanks through this.

## Contributing

Pull requests welcome, especially:

- `status.xml` samples from Apex hardware/firmware combinations that
  don't parse cleanly today.
- Support for other controllers/probes/dosers.
- Panel design ideas.

## License

MIT — see [LICENSE](LICENSE).
