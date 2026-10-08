"""Local read-only reporting API with narrow intent-model routing."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from operations_assistant.answers import render_answer
from operations_assistant.generate import REGIONS
from operations_assistant.intent import LocalIntentModel, QuestionRequest, UnsupportedQuestionError
from operations_assistant.metrics import summary
from operations_assistant.tools import ToolRequest, execute_tool


def create_app(database: Path | None = None) -> FastAPI:
    database = database or Path(os.environ.get("OPERATIONS_DATABASE", "data/operations.duckdb"))
    app = FastAPI(title="Operations Intelligence", version="0.1.0")
    intent_model = LocalIntentModel()

    @app.get("/api/tools")
    def tool_catalog() -> dict:
        return {
            "mode": "deterministic read-only tools; no model invocation",
            "request_schema": ToolRequest.model_json_schema(),
            "tools": ["delivery_summary", "compare_delivery_periods"],
        }

    @app.post("/api/tools/execute")
    def run_tool(request: ToolRequest) -> dict:
        try:
            return execute_tool(database, request)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.post("/api/answers")
    def answer(request: ToolRequest) -> dict:
        try:
            return render_answer(execute_tool(database, request))
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.post("/api/questions")
    def question(request: QuestionRequest) -> dict:
        try:
            tool_request, routing = intent_model.plan(request)
            answer_result = render_answer(execute_tool(database, tool_request))
            return {"routing": routing, **answer_result}
        except UnsupportedQuestionError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @app.get("/", include_in_schema=False)
    def dashboard() -> FileResponse:
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.get("/api/metadata")
    def metadata() -> dict:
        return {
            "regions": REGIONS,
            "mode": (
                "local intent inference; deterministic metrics and answers; "
                "no generative model"
            ),
        }

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
