#!/usr/bin/env python3
"""
LegalLens AI — Baseline Inference Script
Runs a GPT-4o agent as a legal analyst on all 3 tasks.

Usage:
    export OPENAI_API_KEY=sk-...
    python baseline_agent.py [--task task_1_easy] [--model gpt-4o]
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "laws"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tasks"))

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: pip install openai")
    sys.exit(1)

from legallens_openenv.environment import LegalLensEnv
from legallens_openenv.models import (
    Action, ActionType, LegalDomain, LegalAction,
    Jurisdiction, LawReference
)
from tasks.task_definitions import ALL_TASKS


# ─────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior Indian legal analyst with 20 years of experience.
Your job is to analyze a common person's legal problem and:
1. Identify the correct legal domain
2. Map it to specific Indian laws and sections
3. Recommend the correct legal action and forum

You must respond with a single JSON action at each step.

Available action_types:
- "classify_domain": Identify domain (criminal/civil/consumer/labour/cyber/family/property)
- "identify_law": List applicable laws with sections
- "rank_violation": Rank violations by legal strength
- "recommend_action": Suggest legal action (file_fir/consumer_forum/cyber_portal/rera_complaint/internal_complaint/labour_court/civil_suit/send_legal_notice)
- "find_jurisdiction": Identify correct court/forum (local_police/cyber_cell/consumer_district_forum/rera_authority/internal_complaints_committee/labour_court/district_court/high_court)
- "list_evidence": List documents appellant needs to collect
- "check_limitation": Check filing deadline
- "ask_clarification": Ask appellant for more info

Indian Laws to use:
- IPC 420: Cheating/Fraud
- IPC 406: Breach of Trust  
- IPC 506: Criminal Threat/Intimidation
- IPC 498A: Domestic violence/cruelty
- IPC 354: Molestation/outrage modesty
- IPC 500: Defamation
- Consumer Protection Act 2019: Deficiency of service, unfair trade
- IT Act 66D: Online fraud/cyber cheating
- IT Act 66C: Identity theft
- IT Act 67: Obscene content online
- POSH Act S.3: Workplace sexual harassment
- Payment of Wages Act S.15: Salary not paid
- RERA S.18: Builder not giving possession
- RERA S.12: Builder misrepresentation

Response format (JSON only):
{
  "action_type": "classify_domain",
  "problem_id": "PROB_001",
  "domain": "cyber",
  "reasoning": "Brief legal reasoning"
}

For identify_law:
{
  "action_type": "identify_law",
  "problem_id": "PROB_001",
  "laws": [
    {"act": "Information Technology Act 2000", "section": "66D", "description": "Online cheating", "punishment": "3 years + fine", "strength": 0.9}
  ],
  "reasoning": "..."
}

For list_evidence:
{
  "action_type": "list_evidence", 
  "problem_id": "PROB_001",
  "evidence_items": ["UPI payment screenshot", "Order confirmation SMS"],
  "reasoning": "..."
}

Always check allergy to wrong laws — e.g., don't apply POSH to non-workplace cases.
Respond ONLY with JSON."""


# ─────────────────────────────────────────────
# Agent
# ─────────────────────────────────────────────

class LegalAgent:
    def __init__(self, model: str = "gpt-4o"):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set.")
        self.client = OpenAI(api_key=api_key)
        self.model  = model

    def decide(self, obs_text: str, history: List[Dict]) -> Dict[str, Any]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-8:])
        messages.append({"role": "user", "content": obs_text})
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=600,
        )
        raw = resp.choices[0].message.content
        try:
            return json.loads(raw)
        except Exception:
            return {"action_type": "ask_clarification",
                    "problem_id": "PROB_001", "question": "Can you elaborate?"}

    def parse_action(self, d: Dict[str, Any]) -> Action:
        def se(cls, v):
            try: return cls(v) if v else None
            except: return None

        laws = []
        for l in d.get("laws", []):
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

        return Action(
            action_type=se(ActionType, d.get("action_type")) or ActionType.ASK_CLARIFICATION,
            problem_id=d.get("problem_id", "PROB_001"),
            domain=se(LegalDomain,  d.get("domain")),
            laws=laws,
            ranked_laws=d.get("ranked_laws", []),
            legal_action=se(LegalAction, d.get("legal_action") or d.get("action")),
            jurisdiction=se(Jurisdiction, d.get("jurisdiction")),
            evidence_items=d.get("evidence_items", []),
            question=d.get("question"),
            reasoning=d.get("reasoning", ""),
        )


# ─────────────────────────────────────────────
# Observation formatter
# ─────────────────────────────────────────────

def format_obs(obs, task_cfg: Dict) -> str:
    lines = []
    lines.append(f"=== STEP {obs.step_number} | {task_cfg['name']} [{task_cfg['difficulty'].upper()}] ===")
    lines.append(f"Steps remaining: {obs.steps_remaining}")
    lines.append("")
    lines.append("APPELLANT'S STATEMENT:")
    lines.append(f'"{obs.problem.statement}"')
    lines.append("")
    lines.append(f"Key facts: {', '.join(obs.problem.keywords)}")
    if obs.problem.amount_involved:
        lines.append(f"Amount involved: ₹{obs.problem.amount_involved:,.0f}")
    lines.append(f"Urgency: {obs.problem.urgency.upper()}")
    lines.append(f"Prior action by appellant: {obs.problem.prior_action or 'None'}")
    lines.append("")

    if obs.classified_domain:
        lines.append(f"✅ Domain classified: {obs.classified_domain}")
    if obs.identified_laws:
        lines.append(f"✅ Laws identified: {len(obs.identified_laws)}")
    if obs.recommended_actions:
        lines.append(f"✅ Actions recommended: {', '.join(obs.recommended_actions)}")
    if obs.jurisdiction:
        lines.append(f"✅ Jurisdiction: {obs.jurisdiction}")
    if obs.evidence_checklist:
        lines.append(f"✅ Evidence items listed: {len(obs.evidence_checklist)}")

    lines.append("")
    lines.append(f"Last feedback: {obs.last_action_feedback[:300]}...")

    if obs.task_hint:
        lines.append(f"\n[HINT] {obs.task_hint}")

    remaining = []
    if not obs.classified_domain:     remaining.append("classify_domain")
    if not obs.identified_laws:        remaining.append("identify_law")
    if not obs.recommended_actions:    remaining.append("recommend_action")
    if not obs.jurisdiction:           remaining.append("find_jurisdiction")
    if not obs.evidence_checklist:     remaining.append("list_evidence")

    if remaining:
        lines.append(f"\nStill needed: {', '.join(remaining)}")
    lines.append("\nWhat is your next action? (JSON only)")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Episode runner
# ─────────────────────────────────────────────

def run_episode(task_id: str, agent: LegalAgent, verbose: bool = True) -> Dict:
    env      = LegalLensEnv(task_id=task_id)
    task_cfg = ALL_TASKS[task_id]
    obs      = env.reset()
    history: List[Dict] = []
    total_reward = 0.0
    steps = 0
    final_info = {}

    if verbose:
        print(f"\n{'='*60}")
        print(f"  TASK: {task_cfg['name']} [{task_cfg['difficulty'].upper()}]")
        print(f"{'='*60}")

    while not obs.episode_complete:
        obs_text = format_obs(obs, task_cfg)
        try:
            decision = agent.decide(obs_text, history)
            action   = agent.parse_action(decision)
        except Exception as e:
            print(f"  [ERROR] {e}")
            break

        if verbose:
            print(f"  Step {steps+1:02d} | {action.action_type} | {action.reasoning[:60]}...")

        history.append({"role": "user",      "content": obs_text})
        history.append({"role": "assistant", "content": json.dumps(decision)})

        obs, reward, done, info = env.step(action)
        total_reward += reward.total
        steps += 1
        final_info = info

        if done:
            break

    score = final_info.get("final_score", 0.0)
    grade = final_info.get("episode_grade", {})

    if verbose:
        print(f"\n  ── RESULT ──────────────────────────")
        print(f"  Steps: {steps} | Reward: {total_reward:.3f} | Score: {score:.4f}")
        if grade.get("breakdown"):
            for k, v in grade["breakdown"].items():
                print(f"    {k}: {v:.3f}")

    return {
        "task_id":      task_id,
        "task_name":    task_cfg["name"],
        "difficulty":   task_cfg["difficulty"],
        "steps":        steps,
        "total_reward": round(total_reward, 4),
        "final_score":  score,
        "breakdown":    grade.get("breakdown", {}),
    }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task",  default="all")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    print("\n⚖️  LegalLens AI — Baseline Inference")
    print(f"   Model: {args.model}")

    agent = LegalAgent(model=args.model)
    tasks = list(ALL_TASKS.keys()) if args.task == "all" else [args.task]

    results = []
    for task_id in tasks:
        result = run_episode(task_id, agent, verbose=not args.quiet)
        results.append(result)
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"  {'Task':<35} {'Diff':<8} {'Score':>7}")
    print(f"  {'-'*52}")
    for r in results:
        print(f"  {r['task_name']:<35} {r['difficulty']:<8} {r['final_score']:>7.4f}")
    print(f"{'='*60}\n")

    with open("baseline_results.json", "w") as f:
        json.dump({"model": args.model, "results": results}, f, indent=2)
    print("Results saved → baseline_results.json")


if __name__ == "__main__":
    main()
