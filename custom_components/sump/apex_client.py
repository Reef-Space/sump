"""Local network client for Neptune Apex controllers.

Talks to the unauthenticated, read-only status endpoint that has shipped
on every Apex controller for well over a decade::

    http://<apex-ip>/cgi-bin/status.xml

This endpoint doesn't require a login and can't change outlet states --
it's monitoring only. Outlet/program control needs Apex's authenticated
API, which is intentionally left for a future release (see README).

Apex firmware has drifted a little over the years in exactly how it tags
probes and outputs in this XML, so parsing here is deliberately
defensive: we look for a couple of known tag-name variants rather than
assuming one exact schema. If your Apex doesn't populate sensors after
setup, open ``http://<apex-ip>/cgi-bin/status.xml`` directly in a browser
and compare it against the tag names below -- that's the fastest way to
extend the parser, and a great first pull request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import xml.etree.ElementTree as ET

import aiohttp

_LOGGER = logging.getLogger(__name__)

STATUS_PATH = "/cgi-bin/status.xml"
REQUEST_TIMEOUT = 10


class ApexConnectionError(Exception):
    """Raised when the Apex can't be reached or returns unusable data."""


@dataclass
class ApexProbe:
    """A single probe reading (temperature, pH, ORP, ...)."""

    name: str
    probe_type: str | None
    value: float | str


@dataclass
class ApexOutput:
    """A single output/outlet's reported state (read-only in v1)."""

    name: str
    device_id: str | None
    state: str | None


@dataclass
class ApexStatus:
    """A full snapshot of one Apex controller."""

    hostname: str | None
    software: str | None
    hardware: str | None
    probes: list[ApexProbe] = field(default_factory=list)
    outputs: list[ApexOutput] = field(default_factory=list)


class ApexLocalClient:
    """Minimal read-only client for the Apex local status.xml endpoint."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._host = host.rstrip("/")

    @property
    def url(self) -> str:
        """Full status.xml URL, tolerating a host with or without a scheme."""
        if self._host.startswith(("http://", "https://")):
            return f"{self._host}{STATUS_PATH}"
        return f"http://{self._host}{STATUS_PATH}"

    async def async_get_status(self) -> ApexStatus:
        """Fetch and parse status.xml. Raises ApexConnectionError on failure."""
        try:
            async with self._session.get(
                self.url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as resp:
                resp.raise_for_status()
                raw = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ApexConnectionError(
                f"Could not reach an Apex at {self._host}: {err}"
            ) from err

        try:
            root = ET.fromstring(raw)
        except ET.ParseError as err:
            raise ApexConnectionError(
                f"Apex at {self._host} returned unparseable XML: {err}"
            ) from err

        return self._parse(root)

    def _parse(self, root: ET.Element) -> ApexStatus:
        hostname = self._find_text(root, ["hostname", "source"])
        software = self._find_text(root, ["software"])
        hardware = self._find_text(root, ["hardware"])

        probes: list[ApexProbe] = []
        # Different firmware generations nest probes under <inputs><input>
        # or <probes><probe>. Try both, first match wins.
        for container_tag, item_tag in (("inputs", "input"), ("probes", "probe")):
            container = root.find(container_tag)
            if container is None:
                continue
            for item in container.findall(item_tag):
                name = self._find_text(item, ["name"])
                if not name:
                    continue
                probe_type = self._find_text(item, ["type", "probe_type"])
                raw_value = self._find_text(item, ["value"])
                value: float | str = raw_value or ""
                try:
                    value = float(raw_value)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    pass  # keep it as a string (e.g. status text)
                probes.append(ApexProbe(name=name, probe_type=probe_type, value=value))
            if probes:
                break

        outputs: list[ApexOutput] = []
        container = root.find("outputs")
        if container is not None:
            for item in container.findall("output"):
                name = self._find_text(item, ["name"])
                if not name:
                    continue
                device_id = self._find_text(item, ["did", "device_id"])
                state = self._find_text(item, ["status", "state"])
                # Older firmware packs "AON 34 0.3" (state watt amp) into
                # a single field -- keep just the leading state token.
                if state and " " in state:
                    state = state.split()[0]
                outputs.append(ApexOutput(name=name, device_id=device_id, state=state))

        if not probes and not outputs:
            _LOGGER.warning(
                "Connected to %s but found no recognisable probes or outputs "
                "in status.xml -- your firmware may use a different XML "
                "layout than this integration expects. Please open an issue "
                "with a copy of http://%s/cgi-bin/status.xml so we can add "
                "support for it",
                self._host,
                self._host,
            )

        return ApexStatus(
            hostname=hostname,
            software=software,
            hardware=hardware,
            probes=probes,
            outputs=outputs,
        )

    @staticmethod
    def _find_text(element: ET.Element, tags: list[str]) -> str | None:
        """Return the first matching child element's text, or attribute value."""
        for tag in tags:
            child = element.find(tag)
            if child is not None and child.text:
                return child.text.strip()
            if tag in element.attrib:
                return element.attrib[tag]
        return None
