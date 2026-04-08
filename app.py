"""
LegalLens AI — FastAPI Server
HuggingFace Spaces compatible REST API.
OpenEnv compliant endpoints.
"""

from __future__ import annotations
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "laws"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tasks"))

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from environment import LegalLensEnv
from models import (
    Action, ActionType, LegalDomain, LegalAction,
    Jurisdiction, LawReference
)
from tasks.task_definitions import ALL_TASKS

app = FastAPI(
    title="LegalLens AI",
    description="Indian Legal Problem Analyzer — OpenEnv API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: Dict[str, LegalLensEnv] = {}


@app.get("/")
def root():
    return {
        "name":      "LegalLens AI",
        "version":   "1.0.0",
        "tasks":     list(ALL_TASKS.keys()),
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return {
        tid: {
            "name":        c["name"],
            "difficulty":  c["difficulty"],
            "description": c["description"],
        }
        for tid, c in ALL_TASKS.items()
    }


@app.post("/reset")
async def reset(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}

    task_id = body.get("task_id", "task_1_easy")
    if task_id not in ALL_TASKS:
        task_id = "task_1_easy"

    try:
        sid = str(uuid.uuid4())
        env = LegalLensEnv(task_id=task_id)
        obs = env.reset()
        SESSIONS[sid] = env

        if len(SESSIONS) > 100:
            oldest = list(SESSIONS.keys())[0]
            del SESSIONS[oldest]

        return JSONResponse(content={
            "session_id":  sid,
            "task_id":     task_id,
            "observation": obs.model_dump(),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
async def step(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    session_id = body.get("session_id", "")
    if not session_id or session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")

    env = SESSIONS[session_id]

    def se(cls, v):
        try:
            return cls(v) if v else None
        except Exception:
            return None

    laws = []
    for l in (body.get("laws") or []):
        try:
            laws.append(LawReference(
                act=l.get("act", ""),
                section=str(l.get("section", "")),
                description=l.get("description", ""),
                punishment=l.get("punishment", ""),
                strength=float(l.get("strength", 0.5)),
            ))
        except Exception:
            pass

    try:
        action = Action(
            action_type=se(ActionType, body.get("action_type")) or ActionType.ASK_CLARIFICATION,
            problem_id=body.get("problem_id", "PROB_001"),
            domain=se(LegalDomain,   body.get("domain")),
            laws=laws,
            ranked_laws=body.get("ranked_laws", []),
            legal_action=se(LegalAction,  body.get("legal_action")),
            jurisdiction=se(Jurisdiction, body.get("jurisdiction")),
            evidence_items=body.get("evidence_items", []),
            question=body.get("question"),
            reasoning=body.get("reasoning", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid action: {e}")

    obs, reward, done, info = env.step(action)

    return JSONResponse(content={
        "observation": obs.model_dump(),
        "reward":      reward.model_dump(),
        "done":        done,
        "info":        info,
    })


@app.get("/state/{session_id}")
def get_state(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"state": SESSIONS[session_id].state().model_dump()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
