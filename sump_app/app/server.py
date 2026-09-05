"""Sump App backend.

Serves the dashboard (a single self-contained HTML page) and one JSON
endpoint, `/api/status`, that the dashboard's own JavaScript polls.
That endpoint, in turn, calls the Sump *integration's* REST API
through the Supervisor's Home Assistant Core proxy -- so this App
contains no Apex-specific logic at all, just presentation.

Requires `homeassistant_api: true` in config.yaml, which is what makes
the SUPERVISOR_TOKEN environment variable valid for calling
http://supervisor/core/api/.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import aiohttp
from aiohttp import web

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN", "")
CORE_API_BASE = "http://supervisor/core/api"
INDEX_HTML = (Path(__file__).parent / "index.html").read_text(encoding="utf-8")


async def handle_index(request: web.Request) -> web.Response:
    """Serve the (single-page) dashboard."""
    return web.Response(text=INDEX_HTML, content_type="text/html")


async def handle_status(request: web.Request) -> web.Response:
    """Proxy the Sump integration's own /api/sump/status endpoint."""
    if not SUPERVISOR_TOKEN:
        return web.json_response(
            {"error": "No SUPERVISOR_TOKEN available -- is homeassistant_api enabled in config.yaml?"},
            status=500,
        )

    headers = {"Authorization": f"Bearer {SUPERVISOR_TOKEN}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{CORE_API_BASE}/sump/status",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return web.json_response(
                        {
                            "error": (
                                f"The Sump integration returned HTTP {resp.status}. "
                                "Is it installed and set up with at least one device?"
                            ),
                            "detail": text[:200],
                        },
                        status=502,
                    )
                data = await resp.json()
                return web.json_response(data)
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        return web.json_response(
            {"error": f"Couldn't reach Home Assistant Core: {err}"}, status=502
        )


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/api/status", handle_status)
    app.router.add_get("/", handle_index)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8099)
