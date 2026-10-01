"""Local read-only reporting API. No language model is used in this increment."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from operations_assistant.generate import REGIONS
from operations_assistant.metrics import summary


def create_app(database: Path | None = None) -> FastAPI:
    database = database or Path(os.environ.get("OPERATIONS_DATABASE", "data/operations.duckdb"))
    app = FastAPI(title="Operations Intelligence", version="0.1.0")

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.get("/api/metadata")
    def metadata() -> dict:
        return {"regions": REGIONS, "mode": "deterministic metrics; AI not implemented"}

    @app.get("/api/metrics")
    def metrics(
        start: Annotated[date, Query()] = date(2026, 9, 21),
        end: Annotated[date, Query()] = date(2026, 9, 28),
        region: Annotated[str | None, Query()] = None,
    ) -> dict:
        try:
            return summary(database, start, end, region)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    return app
