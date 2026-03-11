import asyncio
import json
import threading
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from matcher import match_tier1, match_tier2, match_tier3
from utils import (
    export_results_to_excel,
    read_file_to_df,
    validate_salesforce_df,
)

app = FastAPI(title="STIM Client Matcher")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session state (single-user MVP)
# ---------------------------------------------------------------------------
state = {
    "sf_records": None,
    "sf_preview": None,
    "match_headers": None,
    "match_records": None,
    "match_filename": None,
    "results": None,
    "progress": {"processed": 0, "total": 0, "done": False},
    "matching_lock": threading.Lock(),
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/upload/salesforce")
async def upload_salesforce(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = read_file_to_df(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    missing = validate_salesforce_df(df)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns: {', '.join(missing)}",
        )

    state["sf_records"] = df.to_dict(orient="records")
    preview = df.head(5).to_dict(orient="records")
    state["sf_preview"] = preview
    return {
        "columns": list(df.columns),
        "row_count": len(df),
        "preview": preview,
    }


@app.post("/upload/matchfile")
async def upload_matchfile(file: UploadFile = File(...)):
    content = await file.read()
    try:
        df = read_file_to_df(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    state["match_headers"] = list(df.columns)
    state["match_records"] = df.to_dict(orient="records")
    state["match_filename"] = file.filename
    return {
        "columns": list(df.columns),
        "row_count": len(df),
        "preview": df.head(5).to_dict(orient="records"),
    }


@app.post("/match")
async def start_match(body: dict):
    if state["sf_records"] is None:
        raise HTTPException(status_code=400, detail="Salesforce file not uploaded")
    if state["match_records"] is None:
        raise HTTPException(status_code=400, detail="Match file not uploaded")

    tier = body.get("tier")
    mappings = body.get("mappings", {})

    sf_records = state["sf_records"]
    input_rows = state["match_records"]

    state["results"] = None
    state["progress"] = {"processed": 0, "total": len(input_rows), "done": False}

    def progress_cb(processed: int, total: int):
        state["progress"]["processed"] = processed
        state["progress"]["total"] = total

    def run():
        try:
            if tier == 1:
                col_org = mappings.get("org_nr")
                if not col_org:
                    state["progress"]["error"] = "Missing org_nr mapping"
                    state["progress"]["done"] = True
                    return
                results = match_tier1(input_rows, sf_records, col_org, progress_cb)
            elif tier == 2:
                col_name = mappings.get("company_name")
                col_city = mappings.get("city")
                col_org = mappings.get("org_nr")
                if not col_name or not col_city:
                    state["progress"]["error"] = "Missing name or city mapping"
                    state["progress"]["done"] = True
                    return
                results = match_tier2(
                    input_rows, sf_records, col_name, col_city, col_org, progress_cb
                )
            elif tier == 3:
                col_name = mappings.get("company_name")
                if not col_name:
                    state["progress"]["error"] = "Missing company_name mapping"
                    state["progress"]["done"] = True
                    return
                results = match_tier3(input_rows, sf_records, col_name, progress_cb)
            else:
                state["progress"]["error"] = f"Unknown tier: {tier}"
                state["progress"]["done"] = True
                return
            state["results"] = results
        except Exception as e:
            state["progress"]["error"] = str(e)
        finally:
            state["progress"]["done"] = True

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return {"status": "started", "total": len(input_rows)}


@app.get("/match/progress")
async def match_progress():
    async def event_stream():
        while True:
            p = state["progress"]
            data = json.dumps(
                {
                    "processed": p["processed"],
                    "total": p["total"],
                    "done": p.get("done", False),
                    "error": p.get("error"),
                }
            )
            yield f"data: {data}\n\n"
            if p.get("done"):
                break
            await asyncio.sleep(0.2)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/match/results")
async def get_results():
    if state["results"] is None:
        raise HTTPException(status_code=404, detail="No results available yet")
    return {"results": state["results"]}


@app.get("/export")
async def export_results():
    if state["results"] is None:
        raise HTTPException(status_code=404, detail="No results to export")
    xlsx_bytes = export_results_to_excel(state["results"])
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=match_results.xlsx"},
    )
