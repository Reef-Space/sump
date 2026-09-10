import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import db
from devices.apex import ApexDriver

log = logging.getLogger("sump.ingestion")

DRIVERS = [ApexDriver()]


async def run_daily_ingestion():
    today = datetime.now(timezone.utc).date().isoformat()
    for driver in DRIVERS:
        try:
            readings = await driver.collect_daily_averages()
        except Exception:
            log.exception("Driver %s failed during daily ingestion", driver.name)
            continue

        for reading in readings:
            db.add_entry(
                parameter=reading["parameter"],
                value=reading["value"],
                unit=reading.get("unit"),
                source="apex_daily_avg",
                notes=f"Daily average computed by Sump for {today}",
                timestamp=f"{today}T23:55:00+00:00",
            )
        if readings:
            log.info("Ingested %d daily-average readings from %s", len(readings), driver.name)


def start_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    # Runs once a day just before midnight UTC, averaging that day's readings.
    scheduler.add_job(run_daily_ingestion, "cron", hour=23, minute=55, id="daily_ingestion")
    scheduler.start()
    return scheduler
