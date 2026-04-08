"""
LegalLens AI — FastAPI Server
HuggingFace Spaces compatible REST API.
"""

from __future__ import annotations
import sys, os, uuid
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "laws"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tasks"))

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

SESSIONS: Dict[str, LegalLensEnv] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = "task_1_easy"

class StepRequest(BaseModel):
    session_id:     str
    action_type:    str
    problem_id:     str
    domain:         Optional[str]       = None
    laws:           Optional[List[Dict[str, Any]]] = None
    ranked_laws:    Optional[List[str]] = None
    legal_action:   Optional[str]       = None
    jurisdiction:   Optional[str]       = None
    evidence_items: Optional[List[str]] = None
    question:       Optional[str]       = None
    reasoning:      str                 = ""


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "LegalLens AI", "version": "1.0.0",
            "tasks": list(ALL_TASKS.keys()),
            "endpoints": ["/reset", "/step", "/state", "/tasks", "/health"]}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def list_tasks():
    return {tid: {"name": c["name"], "difficulty": c["difficulty"],
                  "description": c["description"]}
            for tid, c in ALL_TASKS.items()}

@app.post("/reset")
def reset(req: ResetRequest):
    if req.task_id not in ALL_TASKS:
        raise HTTPException(400, f"Unknown task: {req.task_id}")
    sid = str(uuid.uuid4())
    env = LegalLensEnv(task_id=req.task_id)
    obs = env.reset()
    SESSIONS[sid] = env
    if len(SESSIONS) > 50:
        del SESSIONS[list(SESSIONS.keys())[0]]
    return {"session_id": sid, "task_id": req.task_id,
            "observation": obs.model_dump()}

@app.post("/step")
def step(req: StepRequest):
    if req.session_id not in SESSIONS:
        raise HTTPException(404, "Session not found. Call /reset first.")
    env = SESSIONS[req.session_id]

    def se(cls, v):
        try: return cls(v) if v else None
        except: return None

    laws = []
    for l in (req.laws or []):
        try:
            laws.append(LawReference(
                act=l.get("act",""), section=str(l.get("section","")),
                description=l.get("description",""),
                punishment=l.get("punishment",""),
                strength=float(l.get("strength", 0.5)),
            ))
        except: pass

    action = Action(
        action_type=se(ActionType, req.action_type) or ActionType.ASK_CLARIFICATION,
        problem_id=req.problem_id,
        domain=se(LegalDomain,  req.domain),
        laws=laws,
        ranked_laws=req.ranked_laws or [],
        legal_action=se(LegalAction, req.legal_action),
        jurisdiction=se(Jurisdiction, req.jurisdiction),
        evidence_items=req.evidence_items or [],
        question=req.question,
        reasoning=req.reasoning,
    )
    obs, reward, done, info = env.step(action)
    return {"observation": obs.model_dump(), "reward": reward.model_dump(),
            "done": done, "info": info}

@app.get("/state/{session_id}")
def get_state(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(404, "Session not found.")
    return {"state": SESSIONS[session_id].state().model_dump()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
