"""FastAPI service for the MirAI fraud scoring pipeline."""

from __future__ import annotations

import json
from queue import Queue
from threading import Thread
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from app.db_neo4j import test_connection as test_neo4j_connection
from app.db_postgres import test_connection as test_postgres_connection
from app.db_redis import test_connection as test_redis_connection
from app.agent import get_persisted_trace, investigate
from app.lookup import (
    get_card_history,
    get_flagged_queue,
    get_transaction_by_card_id,
    update_decision,
)
from app.layer3_model import get_holdout_metrics
from app.pipeline import ProgressCallback, generate_plain_summary, run_pipeline
from app.seed_database import seed_card_history
from app.time_utils import format_dataset_date, format_dataset_time


class DecisionRequest(BaseModel):
    transaction_id: int = Field(gt=0)
    analyst_decision: str
    override_reason: str | None = None


app = FastAPI(title="MirAI Fraud Detection API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8502",
        "http://127.0.0.1:8502",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_log() -> None:
    """Log a concise startup confirmation."""
    print("MirAI Fraud Detection API is ready.")


@app.get("/queue")
def queue() -> list[dict[str, Any]]:
    """Return the highest-risk pre-scored transactions for analyst review."""
    try:
        return get_flagged_queue()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


class ProgressAbort(RuntimeError):
    """Stop a streamed investigation after a stage reports a failure."""


def _report_progress(
    progress_callback: ProgressCallback | None,
    stage: str,
    status: str,
    error: str | None = None,
) -> None:
    if progress_callback is not None:
        progress_callback(stage, status, error)


def _investigate_transaction(
    card_id: str,
    progress_callback: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Run the existing investigation workflow, optionally reporting its stages."""
    _report_progress(progress_callback, "initializing", "running")
    card_id = card_id.strip()
    print(f"[api.transaction_by_card] card_id={card_id!r} as_of=None")
    try:
        transaction = get_transaction_by_card_id(card_id)
        if transaction is None:
            inserted = seed_card_history(card_id)
            print(
                f"[api.transaction_by_card] card_id={card_id!r} "
                f"database_miss on_demand_seed_rows={inserted}"
            )
            transaction = get_transaction_by_card_id(card_id)
        if transaction is None:
            raise HTTPException(status_code=404, detail="Card ID was not found.")
        _report_progress(progress_callback, "initializing", "completed")
    except Exception as error:
        _report_progress(progress_callback, "initializing", "failed", str(error))
        raise

    _report_progress(progress_callback, "signals", "running")
    try:
        card_history = get_card_history(card_id, limit=1000)
        card_history = [
            {
                **row,
                "display_date": format_dataset_date(row["time"]),
                "display_time": format_dataset_time(row["time"]),
            }
            for row in card_history
        ]
        print(
            f"[api.transaction_by_card] card_id={card_id!r} "
            f"current_time={transaction['time']!r} as_of=None "
            f"history_rows={len(card_history)}"
        )
        pipeline_input = {
            "card_id": transaction["card_id"],
            "device_id": transaction["device_id"],
            "time": transaction["time"],
            "display_date": format_dataset_date(transaction["time"]),
            "display_time": format_dataset_time(transaction["time"]),
            "amount": transaction["amount"],
            "v_features": transaction["v_features"],
            "purchaser_email_domain": transaction["purchaser_email_domain"],
            "recipient_email_domain": transaction["recipient_email_domain"],
            "card_history": card_history,
        }
        _report_progress(progress_callback, "signals", "completed")
    except Exception as error:
        _report_progress(progress_callback, "signals", "failed", str(error))
        raise

    result = run_pipeline(pipeline_input, progress_callback=progress_callback)
    _report_progress(progress_callback, "final", "running")
    result["plain_summary"] = generate_plain_summary(result)
    result["card_history"] = card_history
    try:
        agent_result = investigate(
            pipeline_input,
            float(result.get("gbt_score", 0.0)),
            result.get("top_features", []),
            transaction_id=transaction["transaction_id"],
        )
        result["agent_decision"] = {
            key: agent_result.get(key)
            for key in (
                "recommended_action",
                "confidence",
                "evidence_summary",
                "escalation_reason",
            )
        }
        result["agent_trace"] = agent_result.get("trace")
    except Exception as error:
        result["agent_decision"] = {
            "recommended_action": "escalate",
            "confidence": 0.0,
            "evidence_summary": "Investigation agent unavailable.",
            "escalation_reason": str(error),
        }
    # Keep model internals out of the analyst response.
    result["model_risk_score"] = (
        result.get("gbt_score") if result.get("model_score_available") else None
    )
    result.pop("top_features", None)
    result.pop("gbt_score", None)
    result.pop("anomaly_score", None)
    result.pop("reason", None)
    result.pop("model_input_available", None)
    result.pop("model_score_available", None)
    response = {
        **result,
        "transaction_id": transaction["transaction_id"],
        "card_id": transaction["card_id"],
        "device_id": transaction["device_id"],
        "time": transaction["time"],
        "display_date": format_dataset_date(transaction["time"]),
        "display_time": format_dataset_time(transaction["time"]),
        "amount": transaction["amount"],
        "purchaser_email_domain": transaction["purchaser_email_domain"],
        "recipient_email_domain": transaction["recipient_email_domain"],
        "rules_flag": result.get("rules_flag", False),
        "graph_flag": result.get("graph_flag", False),
    }
    _report_progress(progress_callback, "final", "completed")
    return response


@app.get("/transaction/{card_id}")
def transaction_by_card(card_id: str) -> dict[str, Any]:
    """Fetch a transaction by card ID and run the full pipeline."""
    try:
        return _investigate_transaction(card_id)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/transaction/{card_id}/progress")
def transaction_progress(card_id: str) -> StreamingResponse:
    """Stream real investigation stage events, followed by the normal case payload."""
    events: Queue[dict[str, Any] | None] = Queue()

    def report(stage: str, status: str, error: str | None = None) -> None:
        events.put({"type": "stage", "stage": stage, "status": status, "error": error})
        if status == "failed":
            raise ProgressAbort(error or f"{stage} failed")

    def run() -> None:
        try:
            result = _investigate_transaction(card_id, report)
            events.put({"type": "result", "case": result})
        except HTTPException as error:
            events.put({"type": "error", "message": str(error.detail)})
        except Exception as error:
            events.put({"type": "error", "message": str(error)})
        finally:
            events.put(None)

    Thread(target=run, daemon=True).start()

    def stream():
        while True:
            event = events.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, default=str)}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/decision")
def save_decision(decision_request: DecisionRequest) -> dict[str, Any]:
    """Record the analyst's final decision."""
    try:
        update_decision(
            decision_request.transaction_id,
            decision_request.analyst_decision,
            reviewed_by_human=True,
        )
        return {
            "status": "saved",
            "transaction_id": decision_request.transaction_id,
            "decision": decision_request.analyst_decision,
            "override_reason": decision_request.override_reason,
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/health")
def health() -> dict[str, Any]:
    """Return independent live connectivity status for each database."""
    checks = {
        "postgres": test_postgres_connection,
        "redis": test_redis_connection,
        "neo4j": test_neo4j_connection,
    }
    status = {}
    for name, check in checks.items():
        try:
            status[name] = {"connected": bool(check())}
        except Exception as error:
            status[name] = {"connected": False, "error": str(error)}
    return {"databases": status}


@app.get("/model-metrics")
def model_metrics() -> dict[str, float]:
    """Return current ROC-AUC and recall on the time-based holdout set."""
    try:
        return get_holdout_metrics()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/investigation/{transaction_id}/trace")
def investigation_trace(transaction_id: int) -> dict[str, Any]:
    """Return the persisted, viewable agent trace for a transaction."""
    try:
        trace = get_persisted_trace(transaction_id)
        if trace is None:
            raise HTTPException(status_code=404, detail="Investigation trace was not found.")
        return trace
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
