/**
 * Sump - custom sidebar panel.
 *
 * Renders live probe and outlet-state data pulled from every configured
 * Sump device via the `sump/get_status` WebSocket command. Deliberately
 * plain vanilla JS + Shadow DOM (no build step, no framework) so
 * installing this from HACS gets you working code with nothing else to
 * compile.
 *
 * Colors and fonts are pulled from Home Assistant's own CSS variables
 * throughout, so the panel automatically matches whatever theme
 * (light, dark, or custom) the person already has -- it should never
 * look like a foreign app bolted onto the side of Home Assistant.
 */

const POLL_INTERVAL_MS = 10000;

class SumpPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._devices = null; // null = still loading
    this._error = null;
    this._pollHandle = null;
  }

  set hass(hass) {
    const firstTime = !this._hass;
    this._hass = hass;
    if (firstTime) {
      this._start();
    }
  }

  set panel(panel) {
    this._config = panel.config;
  }

  connectedCallback() {
    this._render();
    if (this._hass && !this._pollHandle) {
      this._start();
    }
  }

  disconnectedCallback() {
    if (this._pollHandle) {
      clearInterval(this._pollHandle);
      this._pollHandle = null;
    }
  }

  _start() {
    this._fetchStatus();
    this._pollHandle = setInterval(() => this._fetchStatus(), POLL_INTERVAL_MS);
  }

  async _fetchStatus() {
    try {
      const result = await this._hass.callWS({ type: "sump/get_status" });
      this._devices = result.devices || [];
      this._error = null;
    } catch (err) {
      this._error = (err && err.message) || "Couldn't load Sump data.";
    }
    this._render();
  }

  _render() {
    const tankCount = this._devices ? this._devices.length : 0;

    let body;
    if (this._error) {
      body = `<div class="state state-error">${this._escape(this._error)}</div>`;
    } else if (this._devices === null) {
      body = `<div class="state">Loading tank data&hellip;</div>`;
    } else if (this._devices.length === 0) {
      body = `<div class="state">No aquarium devices yet.<br>Add one from Settings&nbsp;&rarr;&nbsp;Devices&nbsp;&amp;&nbsp;services&nbsp;&rarr;&nbsp;Add integration&nbsp;&rarr;&nbsp;Sump.</div>`;
    } else {
      body = this._devices.map((d) => this._renderDevice(d)).join("");
    }

    this.shadowRoot.innerHTML = `
      <style>${this._css()}</style>
      <div class="toolbar">
        <button class="menu-btn" id="menu-btn" title="Menu" aria-label="Open menu">
          <svg viewBox="0 0 24 24"><path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z"/></svg>
        </button>
        <h1>Sump</h1>
        <span class="tag">${tankCount} tank${tankCount === 1 ? "" : "s"}</span>
      </div>
      <div class="content">${body}</div>
    `;

    const menuBtn = this.shadowRoot.querySelector("#menu-btn");
    if (menuBtn) {
      menuBtn.addEventListener("click", () => {
        this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
      });
    }
  }

  _renderDevice(device) {
    const readings = (device.probes || [])
      .map(
        (p) => `
        <div class="reading">
          <div class="reading-label">${this._escape(p.name)}</div>
          <div class="reading-value-row">
            <span class="reading-value">${this._formatValue(p.value)}</span>
            <span class="reading-unit">${this._escape(p.unit || "")}</span>
          </div>
        </div>`
      )
      .join("");

    const outputs = (device.outputs || [])
      .map(
        (o) => `
        <div class="output-row">
          <span>${this._escape(o.name)}</span>
          <span class="output-state">${this._escape(o.state || "?")}</span>
        </div>`
      )
      .join("");

    return `
      <section class="device">
        <div class="device-header">
          <h2>${this._escape(device.name)}</h2>
          ${!device.available ? '<span class="badge-offline">Not responding</span>' : ""}
        </div>
        <div class="readings">
          ${readings || '<div class="state">No probes reported yet.</div>'}
        </div>
        ${outputs ? `<div class="outputs">${outputs}</div>` : ""}
      </section>
    `;
  }

  _formatValue(value) {
    if (typeof value === "number") {
      // Round to at most 2 decimals without padding whole numbers
      // (78.1 stays "78.1", 78 stays "78", 7.9299999 becomes "7.93").
      return String(Math.round(value * 100) / 100);
    }
    return this._escape(value === undefined || value === null || value === "" ? "—" : String(value));
  }

  _escape(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  _css() {
    return `
      :host {
        display: block;
        height: 100%;
        overflow-y: auto;
        background: var(--primary-background-color);
        color: var(--primary-text-color);
        font-family: inherit;
        box-sizing: border-box;
      }
      *, *::before, *::after { box-sizing: border-box; }

      .toolbar {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 0 16px;
        height: 56px;
        border-bottom: 1px solid var(--divider-color);
      }
      .toolbar h1 {
        font-size: 20px;
        font-weight: 500;
        margin: 0;
      }
      .toolbar .tag {
        font-size: 12px;
        color: var(--secondary-text-color);
        border: 1px solid var(--divider-color);
        border-radius: 999px;
        padding: 2px 10px;
      }

      .menu-btn {
        display: none;
        width: 40px;
        height: 40px;
        border-radius: 8px;
        border: none;
        background: transparent;
        color: var(--primary-text-color);
        cursor: pointer;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        padding: 0;
      }
      .menu-btn svg { width: 24px; height: 24px; fill: currentColor; }
      .menu-btn:hover { background: rgba(127, 127, 127, 0.15); }
      .menu-btn:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }
      @media (max-width: 870px) {
        .menu-btn { display: flex; }
      }

      .content {
        max-width: 900px;
        margin: 0 auto;
        padding: 8px 16px 48px;
      }

      .device { margin-top: 32px; }
      .device-header {
        display: flex;
        align-items: baseline;
        gap: 10px;
      }
      .device-header h2 {
        font-size: 15px;
        font-weight: 500;
        color: var(--secondary-text-color);
        margin: 0;
      }
      .badge-offline {
        font-size: 12px;
        color: var(--error-color, #db4437);
      }

      .readings {
        display: flex;
        flex-wrap: wrap;
        border-top: 1px solid var(--divider-color);
        margin-top: 12px;
      }
      .reading {
        flex: 1 1 130px;
        padding: 16px 20px 16px 0;
        border-bottom: 1px solid var(--divider-color);
      }
      .reading-label {
        font-size: 13px;
        color: var(--secondary-text-color);
        margin-bottom: 6px;
      }
      .reading-value-row {
        display: flex;
        align-items: baseline;
      }
      .reading-value {
        font-variant-numeric: tabular-nums;
        font-size: 28px;
        line-height: 1;
      }
      .reading-unit {
        font-size: 13px;
        color: var(--secondary-text-color);
        margin-left: 5px;
      }

      .outputs { margin-top: 4px; }
      .output-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid var(--divider-color);
        font-size: 14px;
      }
      .output-state {
        font-size: 12px;
        padding: 2px 10px;
        border-radius: 999px;
        background: var(--secondary-background-color, rgba(127, 127, 127, 0.15));
        color: var(--secondary-text-color);
      }

      .state {
        padding: 48px 16px;
        text-align: center;
        color: var(--secondary-text-color);
      }
      .state-error { color: var(--error-color, #db4437); }

      @media (prefers-reduced-motion: no-preference) {
        .reading-value { transition: opacity 0.15s ease; }
      }
    `;
  }
}

customElements.define("sump-panel", SumpPanel);
