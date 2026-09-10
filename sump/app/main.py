import csv
import io
import logging
from datetime import datetime, timedelta, timezone

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from ingestion import start_scheduler, run_daily_ingestion

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sump")

app = FastAPI(title="Sump")


# ---------- schemas ----------

class EntryIn(BaseModel):
    parameter: str
    value: float
    unit: str | None = None
    notes: str | None = None
    timestamp: str | None = None  # ISO 8601; defaults to now


class TargetIn(BaseModel):
    parameter: str
    target_low: float | None = None
    target_high: float | None = None
    unit: str | None = None


# ---------- lifecycle ----------

@app.on_event("startup")
def on_startup():
    db.init_db()
    start_scheduler()
    log.info("Sump started")


# ---------- entries ----------

@app.get("/api/entries")
def get_entries(parameter: str | None = None, days: int | None = None):
    return db.list_entries(parameter=parameter, days=days)


@app.post("/api/entries")
def post_entry(entry: EntryIn):
    entry_id = db.add_entry(
        parameter=entry.parameter,
        value=entry.value,
        unit=entry.unit,
        source="manual",
        notes=entry.notes,
        timestamp=entry.timestamp,
    )
    return {"id": entry_id}


@app.delete("/api/entries/{entry_id}")
def remove_entry(entry_id: int):
    db.delete_entry(entry_id)
    return {"ok": True}


@app.get("/api/parameters")
def get_parameters():
    return db.list_parameters()


# ---------- targets ----------

@app.get("/api/targets")
def get_targets():
    return db.get_targets()


@app.post("/api/targets")
def post_target(target: TargetIn):
    db.set_target(target.parameter, target.target_low, target.target_high, target.unit)
    return {"ok": True}


# ---------- stats ----------

@app.get("/api/stats")
def get_stats(parameter: str, days: int = 30):
    entries = db.list_entries(parameter=parameter, days=days)
    if not entries:
        return {
            "parameter": parameter, "count": 0, "average": None, "min": None,
            "max": None, "latest": None, "days_out_of_range": 0,
        }

    values = [e["value"] for e in entries]
    target = db.get_target(parameter)
    out_of_range_days = set()
    if target and (target["target_low"] is not None or target["target_high"] is not None):
        lo = target["target_low"]
        hi = target["target_high"]
        for e in entries:
            if (lo is not None and e["value"] < lo) or (hi is not None and e["value"] > hi):
                out_of_range_days.add(e["timestamp"][:10])

    return {
        "parameter": parameter,
        "count": len(values),
        "average": round(sum(values) / len(values), 3),
        "min": min(values),
        "max": max(values),
        "latest": entries[-1]["value"],
        "days_out_of_range": len(out_of_range_days),
        "target": target,
    }


# ---------- CSV import/export ----------

@app.get("/api/export.csv")
def export_csv():
    entries = db.list_entries()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["timestamp", "parameter", "value", "unit", "source", "notes"])
    writer.writeheader()
    for e in entries:
        writer.writerow({k: e.get(k, "") for k in writer.fieldnames})
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sump_water_tests.csv"},
    )


@app.post("/api/import")
async def import_csv(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    required = {"timestamp", "parameter", "value"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise HTTPException(400, f"CSV must contain columns: {', '.join(sorted(required))}")

    imported = 0
    for row in reader:
        try:
            db.add_entry(
                parameter=row["parameter"],
                value=float(row["value"]),
                unit=row.get("unit") or None,
                source=row.get("source") or "manual",
                notes=row.get("notes") or None,
                timestamp=row["timestamp"],
            )
            imported += 1
        except (ValueError, KeyError):
            continue
    return {"imported": imported}


# ---------- manual trigger, useful for testing the apex ingestion job ----------

@app.post("/api/ingest/run-now")
async def ingest_now():
    await run_daily_ingestion()
    return {"ok": True}


# ---------- static frontend (must be mounted last) ----------

app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8099)
