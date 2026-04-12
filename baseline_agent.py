#!/usr/bin/env python3
"""
LegalLens AI — Baseline Inference Script
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: pip install openai")
    sys.exit(1)

from environment import LegalLensEnv
from models import Action, ActionType, LegalDomain, LegalAction, Jurisdiction, LawReference
from tasks.task_definitions import ALL_TASKS

SYSTEM_PROMPT = """You are a senior Indian legal analyst.
Analyze the appellant's legal problem and respond with ONE JSON action.

Available action_types:
- classify_domain: domain = criminal/civil/consumer/labour/cyber/property
- identify_law: laws = [{act, section, description, punishment, strength}]
- recommend_action: legal_action = file_fir/consumer_forum/cyber_portal/rera_complaint/internal_complaint/labour_court
- find_jurisdiction: jurisdiction = local_police/cyber_cell/consumer_district_forum/rera_authority/internal_complaints_committee/labour_court
- list_evidence: evidence_items = [list of documents]
- check_limitation: check filing deadline

Respond ONLY with JSON."""


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
        try:
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {"action_type": "ask_clarification", "problem_id": "PROB_001"}

    def parse_action(self, d: Dict[str, Any]) -> Action:
        def se(cls, v):
            try: return cls(v) if v else None
            except: return None
        laws = []
        for l in d.get("laws", []):
            try:
                laws.append(LawReference(
                    act=l.get("act", ""), section=str(l.get("section", "")),
                    description=l.get("description", ""), punishment=l.get("punishment", ""),
                    strength=float(l.get("strength", 0.5)),
                ))
            except Exception:
                pass
        return Action(
            action_type=se(ActionType, d.get("action_type")) or ActionType.ASK_CLARIFICATION,
            problem_id=d.get("problem_id", "PROB_001"),
            domain=se(LegalDomain, d.get("domain")),
            laws=laws,
            ranked_laws=d.get("ranked_laws", []),
            legal_action=se(LegalAction, d.get("legal_action")),
            jurisdiction=se(Jurisdiction, d.get("jurisdiction")),
            evidence_items=d.get("evidence_items", []),
            question=d.get("question"),
            reasoning=d.get("reasoning", ""),
        )


def run_episode(task_id: str, agent: LegalAgent, verbose: bool = True) -> Dict:
    env      = LegalLensEnv(task_id=task_id)
    task_cfg = ALL_TASKS[task_id]
    obs      = env.reset()
    history: List[Dict] = []
    total_reward = 0.0
    steps = 0
    final_info = {}

    while not obs.episode_complete:
        remaining = []
        if not obs.classified_domain:   remaining.append("classify_domain")
        if not obs.identified_laws:     remaining.append("identify_law")
        if not obs.recommended_actions: remaining.append("recommend_action")
        if not obs.jurisdiction:        remaining.append("find_jurisdiction")
        if not obs.evidence_checklist:  remaining.append("list_evidence")

        obs_text = (
            f"Task: {task_cfg['name']} | Step {obs.step_number}\n"
            f"Problem: {obs.problem.statement[:300]}\n"
            f"Still needed: {', '.join(remaining) if remaining else 'done'}\n"
            f"JSON action:"
        )
        try:
            decision = agent.decide(obs_text, history)
            action   = agent.parse_action(decision)
        except Exception as e:
            break

        history.append({"role": "user",      "content": obs_text})
        history.append({"role": "assistant", "content": json.dumps(decision)})

        obs, reward, done, info = env.step(action)
        total_reward += reward.total
        steps += 1
        final_info = info
        if done:
            break

    score = final_info.get("final_score", 0.0)
    return {
        "task_id":    task_id,
        "task_name":  task_cfg["name"],
        "difficulty": task_cfg["difficulty"],
        "steps":      steps,
        "total_reward": round(total_reward, 4),
        "final_score":  score,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task",  default="all")
    parser.add_argument("--model", default="gpt-4o")
    args = parser.parse_args()

    agent = LegalAgent(model=args.model)
    tasks = list(ALL_TASKS.keys()) if args.task == "all" else [args.task]
    results = []
    for task_id in tasks:
        result = run_episode(task_id, agent)
        results.append(result)
        time.sleep(1)

    with open("baseline_results.json", "w") as f:
        json.dump({"model": args.model, "results": results}, f, indent=2)
    print("Results saved → baseline_results.json")


if __name__ == "__main__":
    main()
