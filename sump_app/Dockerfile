# Sump App
#
# A small aiohttp web server that serves the dashboard and proxies
# data from the Sump *integration's* own REST endpoint (which does the
# actual Apex polling/parsing) through the Supervisor's Home Assistant
# Core API proxy. All device-communication logic lives in the
# integration; this App is purely a presentation layer over it.
#
# Note: Supervisor no longer injects a default base image (as of
# Supervisor 2026.04.0), so the base image is pinned explicitly here
# rather than via the old build.yaml mechanism, per current Home
# Assistant App docs. Bump this tag occasionally; it doesn't need to
# track every release.
FROM ghcr.io/home-assistant/base:3.23-2026.05.0

# aiohttp from Alpine's own package repo -- avoids needing a C
# compiler toolchain just to install it. If this package name ever
# changes, `pip install aiohttp --break-system-packages` is the
# fallback.
RUN apk add --no-cache python3 py3-aiohttp

WORKDIR /app
COPY app/ /app/

LABEL \
    io.hass.version="0.1.2" \
    io.hass.type="app" \
    io.hass.arch="aarch64|amd64"

# The base image's own ENTRYPOINT launches s6-overlay's init system,
# which expects to be PID 1 and orchestrate service scripts under
# /etc/services.d/. Leaving that ENTRYPOINT in place while only
# setting CMD makes Docker run the base image's /init with our CMD as
# *its* arguments, instead of running our command directly -- that
# mismatch is what "s6-overlay-suexec: fatal: can only run as pid 1"
# actually means. This app is one simple process, so rather than
# adopting the full s6 service-script convention, we replace the
# entrypoint outright and run Python directly as PID 1.
ENTRYPOINT [ "python3", "/app/server.py" ]

# Defensive: some base images bake in a HEALTHCHECK that can invoke
# s6-overlay tooling independently of the main entrypoint. This app
# doesn't need Docker-level health checking (Supervisor handles that
# via the ingress port), so disable it outright rather than leave it
# to inherit whatever the base image set.
HEALTHCHECK NONE
