"""
LegalLens AI — inference.py
OpenEnv Hackathon compliant inference script.

Environment Variables:
    API_BASE_URL     = os.getenv("API_BASE_URL", "<your-active-endpoint>")
    MODEL_NAME       = os.getenv("MODEL_NAME", "<your-active-model>")
    HF_TOKEN         = os.getenv("HF_TOKEN")
    LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")
"""

import os
import sys
import json
from typing import List, Optional
from openai import OpenAI

# ─────────────────────────────────────────────
# Environment Variables — MANDATORY
# API_BASE_URL and MODEL_NAME have defaults
# HF_TOKEN does NOT have a default
# ─────────────────────────────────────────────
API_BASE_URL     = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME       = os.getenv("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# ─────────────────────────────────────────────
# OpenAI Client — configured via env variables
# ─────────────────────────────────────────────
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or "dummy-key",
)

# ─────────────────────────────────────────────
# Structured stdout logs — START / STEP / END
# ─────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val  = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ─────────────────────────────────────────────
# System prompt for legal agent
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior Indian legal analyst.
Analyze the appellant's legal problem. Respond with ONE JSON action at a time.

Available action_types:
- classify_domain: domain = criminal/civil/consumer/labour/cyber/property
- identify_law: laws = [{act, section, description, punishment, strength}]
- recommend_action: legal_action = file_fir/consumer_forum/cyber_portal/rera_complaint/internal_complaint/labour_court
- find_jurisdiction: jurisdiction = local_police/cyber_cell/consumer_district_forum/rera_authority/internal_complaints_committee/labour_court
- list_evidence: evidence_items = [list of documents]
- check_limitation: check filing deadline

Respond ONLY with JSON. Example:
{
  "action_type": "classify_domain",
  "problem_id": "PROB_001",
  "domain": "cyber",
  "reasoning": "Online payment fraud"
}"""


def get_llm_action(messages: list) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
        max_tokens=500,
    )
    return json.loads(response.choices[0].message.content)


# ─────────────────────────────────────────────
# Run one task episode
# ─────────────────────────────────────────────

def run_task(task_id: str) -> dict:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from environment import LegalLensEnv
    from models import (
        Action, ActionType, LegalDomain, LegalAction,
        Jurisdiction, LawReference
    )
    from tasks.task_definitions import ALL_TASKS

    task_cfg = ALL_TASKS[task_id]
    env      = LegalLensEnv(task_id=task_id)
    obs      = env.reset()

    log_start(
        task=task_id,
        env="legallens-openenv",
        model=MODEL_NAME,
    )

    history      = []
    rewards      = []
    steps_taken  = 0
    score        = 0.0
    success      = False

    def se(cls, v):
        try:
            return cls(v) if v else None
        except Exception:
            return None

    try:
        for step in range(1, task_cfg["max_steps"] + 1):
            if obs.episode_complete:
                break

            # Build observation text
            remaining = []
            if not obs.classified_domain:   remaining.append("classify_domain")
            if not obs.identified_laws:     remaining.append("identify_law")
            if not obs.recommended_actions: remaining.append("recommend_action")
            if not obs.jurisdiction:        remaining.append("find_jurisdiction")
            if not obs.evidence_checklist:  remaining.append("list_evidence")

            obs_text = (
                f"Step {step} | Task: {task_cfg['name']}\n"
                f"Problem: {obs.problem.problem_id}\n"
                f"Statement: {obs.problem.statement[:300]}\n"
                f"Keywords: {', '.join(obs.problem.keywords)}\n"
                f"Still needed: {', '.join(remaining) if remaining else 'done'}\n"
                f"Last feedback: {obs.last_action_feedback[:150]}\n"
                f"Respond with JSON action."
            )

            history.append({"role": "user", "content": obs_text})

            try:
                decision = get_llm_action(
                    [{"role": "system", "content": SYSTEM_PROMPT}] + history[-8:]
                )
            except Exception as e:
                log_step(step, "error", 0.00, False, str(e)[:50])
                break

            history.append({"role": "assistant", "content": json.dumps(decision)})

            # Parse laws
            laws = []
            for l in decision.get("laws", []):
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
                action_type=se(ActionType, decision.get("action_type")) or ActionType.ASK_CLARIFICATION,
                problem_id=decision.get("problem_id", obs.problem.problem_id),
                domain=se(LegalDomain,   decision.get("domain")),
                laws=laws,
                ranked_laws=decision.get("ranked_laws", []),
                legal_action=se(LegalAction, decision.get("legal_action")),
                jurisdiction=se(Jurisdiction, decision.get("jurisdiction")),
                evidence_items=decision.get("evidence_items", []),
                question=decision.get("question"),
                reasoning=decision.get("reasoning", ""),
            )

            obs, reward, done, info = env.step(action)

            rewards.append(reward.total)
            steps_taken = step

            action_str = f"{action.action_type}({action.problem_id})"

            log_step(
                step=step,
                action=action_str,
                reward=reward.total,
                done=done,
                error=None,
            )

            if done:
                score   = info.get("final_score", 0.0)
                success = score >= 0.5
                break

    except Exception as e:
        print(f"[DEBUG] Episode error: {e}", flush=True)

    finally:
        log_end(
            success=success,
            steps=steps_taken,
            score=score,
            rewards=rewards,
        )

    return {
        "task_id": task_id,
        "score":   score,
        "steps":   steps_taken,
        "success": success,
    }


# ─────────────────────────────────────────────
# Main — runs all 3 tasks
# ─────────────────────────────────────────────

if __name__ == "__main__":
    task_ids = ["task_1_easy", "task_2_medium", "task_3_hard"]

    for task_id in task_ids:
        try:
            run_task(task_id)
        except Exception as e:
            print(f"[END] success=false steps=0 score=0.00 rewards=", flush=True)