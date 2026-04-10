"""
LegalLens AI — inference.py
OpenEnv Hackathon compliant inference script.

Environment Variables:
    API_BASE_URL  - OpenAI-compatible API base URL (default provided)
    MODEL_NAME    - Model to use (default provided)
    HF_TOKEN      - HuggingFace token (NO default — must be set)
    LOCAL_IMAGE_NAME - Optional, for from_docker_image()
"""

import os
import json
import sys

from openai import OpenAI

# ─────────────────────────────────────────────
# Environment Variables (as required by hackathon)
# API_BASE_URL and MODEL_NAME have defaults
# HF_TOKEN does NOT have a default
# ─────────────────────────────────────────────

API_BASE_URL     = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME       = os.getenv("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")  # Optional

# ─────────────────────────────────────────────
# OpenAI client configured via env variables
# ─────────────────────────────────────────────

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or "dummy-key",  # HF_TOKEN used as API key
)

# ─────────────────────────────────────────────
# Structured logging — START / STEP / END format
# ─────────────────────────────────────────────

def log_start(task_id: str):
    print(json.dumps({
        "type":    "START",
        "task_id": task_id,
        "model":   MODEL_NAME,
        "api_base": API_BASE_URL,
    }), flush=True)


def log_step(step: int, action_type: str, patient_id: str, reward: float, feedback: str):
    print(json.dumps({
        "type":        "STEP",
        "step":        step,
        "action_type": action_type,
        "entity_id":   patient_id,
        "reward":      round(reward, 4),
        "feedback":    feedback[:120],
    }), flush=True)


def log_end(task_id: str, score: float, steps: int, breakdown: dict):
    print(json.dumps({
        "type":      "END",
        "task_id":   task_id,
        "score":     round(score, 4),
        "steps":     steps,
        "breakdown": breakdown,
    }), flush=True)


# ─────────────────────────────────────────────
# System prompt for legal agent
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior Indian legal analyst.
Analyze the appellant's problem and respond with ONE JSON action at a time.

Available action_types:
- classify_domain: domain = criminal/civil/consumer/labour/cyber/property
- identify_law: laws = [{act, section, description, punishment, strength}]
- recommend_action: legal_action = file_fir/consumer_forum/cyber_portal/rera_complaint/internal_complaint/labour_court
- find_jurisdiction: jurisdiction = local_police/cyber_cell/consumer_district_forum/rera_authority/internal_complaints_committee/labour_court/district_court
- list_evidence: evidence_items = [list of documents needed]
- check_limitation: check filing deadline

Respond ONLY with JSON. No prose. Example:
{
  "action_type": "classify_domain",
  "problem_id": "PROB_001",
  "domain": "cyber",
  "reasoning": "Online payment fraud via fake website"
}"""


def get_llm_action(messages: list) -> dict:
    """Call LLM and return parsed action dict."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
        max_tokens=500,
    )
    raw = response.choices[0].message.content
    return json.loads(raw)


# ─────────────────────────────────────────────
# Run one task episode
# ─────────────────────────────────────────────

def run_task(task_id: str) -> dict:
    """Run a full episode for one task. Returns result dict."""

    # Import here so env vars are set first
    sys.path.insert(0, os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "laws"))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tasks"))

    from legallens_openenv.environment import LegalLensEnv
    from legallens_openenv.models import (
        Action, ActionType, LegalDomain, LegalAction,
        Jurisdiction, LawReference
    )
    from tasks.task_definitions import ALL_TASKS

    env      = LegalLensEnv(task_id=task_id)
    task_cfg = ALL_TASKS[task_id]
    obs      = env.reset()

    log_start(task_id)

    history      = []
    total_reward = 0.0
    step_count   = 0
    final_info   = {}

    # Build initial message
    obs_text = (
        f"Task: {task_cfg['name']} [{task_cfg['difficulty'].upper()}]\n\n"
        f"APPELLANT STATEMENT:\n\"{obs.problem.statement}\"\n\n"
        f"Keywords: {', '.join(obs.problem.keywords)}\n"
        f"Amount: ₹{obs.problem.amount_involved:,.0f}" 
        if obs.problem.amount_involved else ""
    )

    def se(cls, v):
        try:
            return cls(v) if v else None
        except Exception:
            return None

    while not obs.episode_complete:
        # Build current observation text
        status_lines = []
        if obs.classified_domain:
            status_lines.append(f"Domain classified: {obs.classified_domain}")
        if obs.identified_laws:
            status_lines.append(f"Laws identified: {len(obs.identified_laws)}")
        if obs.recommended_actions:
            status_lines.append(f"Actions: {', '.join(obs.recommended_actions)}")
        if obs.jurisdiction:
            status_lines.append(f"Jurisdiction: {obs.jurisdiction}")
        if obs.evidence_checklist:
            status_lines.append(f"Evidence items: {len(obs.evidence_checklist)}")

        remaining = []
        if not obs.classified_domain:   remaining.append("classify_domain")
        if not obs.identified_laws:     remaining.append("identify_law")
        if not obs.recommended_actions: remaining.append("recommend_action")
        if not obs.jurisdiction:        remaining.append("find_jurisdiction")
        if not obs.evidence_checklist:  remaining.append("list_evidence")

        current_obs = (
            f"Step {obs.step_number} | Steps left: {obs.steps_remaining}\n"
            f"Problem ID: {obs.problem.problem_id}\n\n"
            f"APPELLANT: \"{obs.problem.statement[:300]}...\"\n\n"
            f"Progress: {'; '.join(status_lines) if status_lines else 'Nothing done yet'}\n"
            f"Still needed: {', '.join(remaining) if remaining else 'Analysis complete!'}\n\n"
            f"Last feedback: {obs.last_action_feedback[:200]}\n\n"
            f"What is your next action? (JSON only)"
        )

        # Get LLM decision
        history.append({"role": "user", "content": current_obs})
        try:
            decision = get_llm_action(
                [{"role": "system", "content": SYSTEM_PROMPT}] + history[-10:]
            )
        except Exception as e:
            print(f"LLM error: {e}", file=sys.stderr)
            break

        history.append({"role": "assistant", "content": json.dumps(decision)})

        # Parse action
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

        # Step environment
        obs, reward, done, info = env.step(action)
        total_reward += reward.total
        step_count   += 1
        final_info    = info

        log_step(
            step=step_count,
            action_type=str(action.action_type),
            patient_id=action.problem_id,
            reward=reward.total,
            feedback=obs.last_action_feedback,
        )

        if done:
            break

    score     = final_info.get("final_score", 0.0)
    breakdown = final_info.get("episode_grade", {}).get("breakdown", {})
    log_end(task_id, score, step_count, breakdown)

    return {
        "task_id":     task_id,
        "score":       score,
        "steps":       step_count,
        "total_reward": round(total_reward, 4),
        "breakdown":   breakdown,
    }


# ─────────────────────────────────────────────
# Main — runs all 3 tasks
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60, flush=True)
    print("LegalLens AI — OpenEnv Hackathon Inference", flush=True)
    print(f"Model: {MODEL_NAME} | API: {API_BASE_URL}", flush=True)
    print("=" * 60, flush=True)

    task_ids = ["task_1_easy", "task_2_medium", "task_3_hard"]
    all_results = []

    for task_id in task_ids:
        try:
            result = run_task(task_id)
            all_results.append(result)
        except Exception as e:
            print(json.dumps({"type": "END", "task_id": task_id,
                              "score": 0.0, "error": str(e)}), flush=True)

    # Final summary
    print("\n" + "=" * 60, flush=True)
    print("FINAL RESULTS", flush=True)
    print("=" * 60, flush=True)
    for r in all_results:
        print(f"  {r['task_id']:<20} Score: {r['score']:.4f} | Steps: {r['steps']}", flush=True)

    avg = sum(r["score"] for r in all_results) / max(len(all_results), 1)
    print(f"\n  Average Score: {avg:.4f}", flush=True)

    # Save results
    with open("baseline_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
