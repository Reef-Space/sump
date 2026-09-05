# Sump

Two things that work together, both free and open source:

1. **The Sump integration** — connects Home Assistant to your aquarium
   equipment (Neptune Apex to start) and creates normal sensors, so you
   get history and automations from Home Assistant's own tools. Works
   on every Home Assistant install type.
2. **The Sump App** — a dedicated "Sump" entry in your sidebar with a
   live, Fusion-style dashboard of everything the integration is
   reading. Requires Home Assistant OS or Supervised, since Apps
   (formerly called Add-ons) are a Supervisor feature.

No cloud account. No subscription. Everything talks to your equipment
over your own local network.

> **Status: early v1.** Monitoring only for now (temperature, pH, ORP,
> salinity, outlet states) — no outlet control yet, and Apex is the
> only supported brand so far. See [Roadmap](#roadmap) and the known
> issue below.
>
> Not affiliated with or endorsed by Neptune Systems. Apex and Trident
> are trademarks of Neptune Systems, LLC.

> **Known issue:** some probe readings can come back wrong on certain
> Apex firmware versions (a temperature probe reading a small negative
> number instead of the real value, for example). This means the XML
> parser is picking up the wrong field for that firmware version. If
> you hit this, please open an issue with a copy of your
> `http://<apex-ip>/cgi-bin/status.xml` — that's the fastest way to
> get it fixed correctly rather than guessed at again.

## Install the integration

### What you need

- A working Home Assistant installation (any install type).
- [HACS](https://hacs.xyz/) installed.
- A Neptune Apex controller on the same local network as Home Assistant.

### HACS (recommended)

1. In Home Assistant, open **HACS**.
2. Click the **⋮** menu (top right) → **Custom repositories**.
3. Add this repository's URL, category **Integration**, click **Add**.
4. Search HACS for **Sump** and click **Download**.
5. Restart Home Assistant when prompted.

### Manual

1. Copy `custom_components/sump` into your Home Assistant
   `config/custom_components/` folder.
2. Restart Home Assistant.

### Set up your Apex

1. **Settings → Devices & services → Add integration → Sump**.
2. Enter your Apex's IP address or hostname (for example
   `192.168.1.50` or `apex.local`). No username or password needed for
   monitoring.
3. Home Assistant tests the connection before finishing setup.

A new device appears with one sensor per probe and outlet, already
recording history.

## Install the App (the sidebar dashboard)

Requires **Home Assistant OS or Supervised**. If you're on Container
or Core, the App can't be installed (Apps need the Supervisor) — the
integration and its sensors still work fully, you just won't get the
dedicated sidebar page; a normal Lovelace dashboard using the Sump
entities is the alternative until this project has another option for
non-Supervisor installs.

1. **Settings → Add-ons** (may show as **Apps** in newer versions) →
   the store icon (bottom right) → **Repositories**.
2. Add this repository's URL and close the dialog.
3. Find **Sump** in the store and click **Install**.
4. Start it. A **Sump** icon appears in your sidebar.

The App has nothing to show until the integration above is installed
*and* has at least one device configured — it's a dashboard over the
integration's data, not a separate way of connecting to your Apex.

### If the App doesn't show anything

Check the App's **Log** tab. The most common causes are the Sump
integration not being installed, or not having a device configured
yet.

## Why two separate things?

Home Assistant integrations and Apps are genuinely different
mechanisms — different install flow, different settings page, and
Apps need the Supervisor while integrations don't. Splitting it this
way means the sensors/history/automations work everywhere, while
Supervisor/OS installs (the majority of setups) also get a proper
standalone dashboard experience, without forcing every Sump user
through Docker just to get a temperature reading into Home Assistant.

## Roadmap

- **Fix the known parsing issue above** for the Apex firmware
  versions it affects.
- **Trend graphs in the App dashboard** — small history sparklines per
  reading, not just the current value.
- **Outlet control** — turn outlets/outputs on, off, or back to auto,
  using Apex's authenticated API.
- **More manufacturers** — Red Sea ReefBeat, GHL, ESPHome-based DIY
  probes, and Zigbee/Bluetooth sensors as a first tier.
- **A non-Supervisor dashboard option**, so Container/Core installs
  get something closer to the App experience too.

## Contributing

Pull requests welcome, especially:

- `status.xml` samples from Apex hardware/firmware combinations that
  parse incorrectly today (see the known issue above).
- Support for other controllers/probes/dosers.
- Dashboard design ideas.

## License

MIT — see [LICENSE](LICENSE).
