"""
LegalLens AI — Server Entry Point
OpenEnv compliant API - server/app.py
"""

from __future__ import annotations
import sys
import os
import uuid

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from environment import LegalLensEnv
from models import (
    Action, ActionType, LegalDomain, LegalAction,
    Jurisdiction, LawReference
)
from tasks.task_definitions import ALL_TASKS


app = FastAPI(
    title="LegalLens AI",
    version="1.0.0"
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
        "name": "LegalLens AI",
        "version": "1.0.0",
        "tasks": list(ALL_TASKS.keys()),
        "endpoints": ["/reset", "/step", "/state", "/tasks", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return {
        tid: {
            "name": c["name"],
            "difficulty": c["difficulty"],
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

    sid = str(uuid.uuid4())
    env = LegalLensEnv(task_id=task_id)
    obs = env.reset()
    SESSIONS[sid] = env

    return JSONResponse(content={
        "session_id": sid,
        "task_id": task_id,
        "observation": obs.model_dump(),
    })


@app.post("/step")
async def step(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    session_id = body.get("session_id", "")
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    env = SESSIONS[session_id]

    def safe_enum(enum_cls, value):
        try:
            return enum_cls(value) if value else None
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

    action = Action(
        action_type=safe_enum(ActionType, body.get("action_type")) or ActionType.ASK_CLARIFICATION,
        problem_id=body.get("problem_id", "PROB_001"),
        domain=safe_enum(LegalDomain, body.get("domain")),
        laws=laws,
        ranked_laws=body.get("ranked_laws", []),
        legal_action=safe_enum(LegalAction, body.get("legal_action")),
        jurisdiction=safe_enum(Jurisdiction, body.get("jurisdiction")),
        evidence_items=body.get("evidence_items", []),
        question=body.get("question"),
        reasoning=body.get("reasoning", ""),
    )

    obs, reward, done, info = env.step(action)

    return JSONResponse(content={
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
    })


@app.get("/state/{session_id}")
def get_state(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"state": SESSIONS[session_id].state().model_dump()}


# REQUIRED ENTRY POINT — openenv-server = "server.app:main"
def main():
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=7860,
        reload=False
    )


if __name__ == "__main__":
    main()
