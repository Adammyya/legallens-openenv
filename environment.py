"""
LegalLens AI — Core Environment
OpenEnv-compliant: step() / reset() / state()
"""

from __future__ import annotations
import copy
import sys
import os

# Ensure local imports work
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "laws"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tasks"))

from typing import Any, Dict, List, Optional, Tuple

from models import (
    Action, ActionType, EpisodeState, LegalDomain,
    LawReference, Observation, Reward
)

from tasks.task_definitions import ALL_TASKS
from grader import compute_step_reward, grade_episode
from laws.knowledge_base import (
    LAW_DATABASE, EVIDENCE_CHECKLISTS,
    JURISDICTION_MAP, LIMITATION_PERIODS
)


class LegalLensEnv:
    def __init__(self, task_id: str = "task_1_easy"):
        if task_id not in ALL_TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'")

        self.task_id = task_id
        self._task_cfg = ALL_TASKS[task_id]
        self._state: Optional[EpisodeState] = None
        self.reset()

    def reset(self) -> Observation:
        cfg = self._task_cfg
        self._state = EpisodeState(
            task_id=cfg["task_id"],
            task_name=cfg["name"],
            task_difficulty=cfg["difficulty"],
            problem=cfg["problem"],
            action_history=[],
            step_count=0,
            total_reward=0.0,
            done=False,
        )

        return self._build_observation(
            f"New case received.\n\nProblem:\n{cfg['problem'].statement}"
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        s = self._state
        gold = self._task_cfg["gold"]

        s.step_count += 1

        feedback = self._apply_action(action, s)

        reward = compute_step_reward(action, gold, self._state_dict(s))
        s.total_reward += reward.total

        self._record(s, action)

        done = self._is_complete(s) or s.step_count >= self._task_cfg["max_steps"]
        s.done = done

        info = {}

        if done:
            grade = grade_episode(
                gold=gold,
                action_history=s.action_history,
                final_state=self._state_dict(s),
                total_steps=s.step_count,
                max_steps=self._task_cfg["max_steps"],
            )
            info["final_score"] = grade["final_score"]
            feedback += f"\nFinal Score: {grade['final_score']}"

        return self._build_observation(feedback), reward, done, info

    def state(self) -> EpisodeState:
        return self._state

    # ───────── helpers ─────────

    def _apply_action(self, action: Action, s: EpisodeState) -> str:
        atype = action.action_type

        if atype == ActionType.CLASSIFY_DOMAIN:
            s.classified_domain = action.domain
            return f"Domain classified: {action.domain}"

        elif atype == ActionType.IDENTIFY_LAW:
            s.identified_laws = [l.model_dump() for l in action.laws]
            return "Laws identified."

        elif atype == ActionType.RECOMMEND_ACTION:
            s.recommended_actions.append(action.legal_action)
            return f"Action: {action.legal_action}"

        elif atype == ActionType.FIND_JURISDICTION:
            s.jurisdiction = action.jurisdiction
            return f"Jurisdiction: {action.jurisdiction}"

        elif atype == ActionType.LIST_EVIDENCE:
            s.evidence_checklist = action.evidence_items
            return "Evidence listed."

        return "Action applied."

    def _is_complete(self, s: EpisodeState) -> bool:
        return (
            s.classified_domain is not None and
            len(s.identified_laws) > 0 and
            len(s.recommended_actions) > 0 and
            len(s.evidence_checklist) > 0
        )

    def _state_dict(self, s: EpisodeState) -> Dict[str, Any]:
        return {
            "classified_domain": s.classified_domain,
            "identified_laws": s.identified_laws,
            "recommended_actions": s.recommended_actions,
            "jurisdiction": s.jurisdiction,
            "evidence_checklist": s.evidence_checklist,
        }

    def _record(self, s: EpisodeState, action: Action) -> None:
        s.action_history.append({
            "step": s.step_count,
            "action_type": action.action_type,
            "problem_id": action.problem_id,
        })

    def _build_observation(self, feedback: str) -> Observation:
        s = self._state
        return Observation(
            problem=s.problem,
            classified_domain=s.classified_domain,
            identified_laws=s.identified_laws,
            ranked_violations=s.ranked_violations,
            recommended_actions=s.recommended_actions,
            jurisdiction=s.jurisdiction,
            evidence_checklist=s.evidence_checklist,
            limitation_status=s.limitation_status,
            last_action_feedback=feedback,
            step_number=s.step_count,
            steps_remaining=self._task_cfg["max_steps"] - s.step_count,
            episode_complete=s.done,
        )