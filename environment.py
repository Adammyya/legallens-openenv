"""
LegalLens AI — Core Environment
OpenEnv-compliant: step() / reset() / state()
"""

from __future__ import annotations
import copy
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "laws"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tasks"))

from typing import Any, Dict, List, Optional, Tuple

from models import import (
    Action, ActionType, EpisodeState, LegalDomain,
    LawReference, Observation, Reward
)
from tasks.task_definitions import ALL_TASKS
from legallens_openenv.grader import compute_step_reward, grade_episode
from laws.knowledge_base import (
    LAW_DATABASE, EVIDENCE_CHECKLISTS,
    JURISDICTION_MAP, LIMITATION_PERIODS
)


class LegalLensEnv:
    """
    LegalLens AI — Legal Problem Analysis Environment.

    An AI agent listens to a common person's legal problem,
    identifies applicable laws, and recommends correct action.

    OpenEnv API:
        reset()  → Observation
        step()   → (Observation, Reward, done: bool, info: dict)
        state()  → EpisodeState
    """

    def __init__(self, task_id: str = "task_1_easy"):
        if task_id not in ALL_TASKS:
            raise ValueError(
                f"Unknown task_id '{task_id}'. Valid: {list(ALL_TASKS.keys())}"
            )
        self.task_id   = task_id
        self._task_cfg = ALL_TASKS[task_id]
        self._state: Optional[EpisodeState] = None
        self.reset()

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────

    def reset(self) -> Observation:
        """Reset to initial state. Returns first observation."""
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
            f"📋 New case received. Read the appellant's statement carefully.\n\n"
            f"PROBLEM STATEMENT:\n\"{cfg['problem'].statement}\"\n\n"
            f"Begin your legal analysis."
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """Take one analysis step."""
        if self._state is None:
            raise RuntimeError("Call reset() first.")
        if self._state.done:
            raise RuntimeError("Episode complete. Call reset().")

        s    = self._state
        gold = self._task_cfg["gold"]
        info: Dict[str, Any] = {}

        s.step_count += 1

        # Validate problem_id
        if action.problem_id != s.problem.problem_id:
            reward = Reward(total=-0.1, penalty=-0.1)
            s.total_reward += reward.total
            self._record(s, action)
            return self._build_observation(
                f"⚠️ Wrong problem ID. Active problem: {s.problem.problem_id}"
            ), reward, False, {"error": "wrong_problem_id"}

        # Apply action & get feedback
        feedback = self._apply_action(action, s)

        # Compute step reward
        reward = compute_step_reward(action, gold, self._state_dict(s))
        s.total_reward += reward.total
        self._record(s, action)

        # Check completion
        analysis_complete = self._is_complete(s)
        max_steps_hit     = s.step_count >= self._task_cfg["max_steps"]

        if analysis_complete or max_steps_hit:
            s.done = True
            grade  = grade_episode(
                gold=gold,
                action_history=s.action_history,
                final_state=self._state_dict(s),
                total_steps=s.step_count,
                max_steps=self._task_cfg["max_steps"],
            )
            info["episode_grade"] = grade
            info["final_score"]   = grade["final_score"]
            feedback += (
                f"\n\n{'='*50}\n"
                f"✅ ANALYSIS COMPLETE\n"
                f"Final Score: {grade['final_score']:.4f} / 1.0000\n"
                f"Breakdown: {grade['breakdown']}\n"
                f"{'='*50}"
            )

        return self._build_observation(feedback), reward, s.done, info

    def state(self) -> EpisodeState:
        """Return full internal state."""
        if self._state is None:
            raise RuntimeError("Call reset() first.")
        return self._state.model_copy(deep=True)

    # ─────────────────────────────────────────
    # Action application
    # ─────────────────────────────────────────

    def _apply_action(self, action: Action, s: EpisodeState) -> str:
        atype = action.action_type

        if atype == ActionType.CLASSIFY_DOMAIN:
            domain = action.domain
            if domain:
                s.classified_domain = domain.value if hasattr(domain, "value") else domain
                domain_info = JURISDICTION_MAP.get(s.classified_domain, {})
                return (
                    f"✅ Domain classified: **{s.classified_domain.upper()}**\n"
                    f"📌 {domain_info.get('note', 'Domain identified.')}\n"
                    f"Applicable forums: {', '.join(str(v) for k,v in domain_info.items() if k != 'note')}"
                )
            return "❌ No domain specified."

        elif atype == ActionType.IDENTIFY_LAW:
            if not action.laws:
                return "❌ No laws identified."
            s.identified_laws = [l.model_dump() for l in action.laws]
            result_lines = ["📚 Laws Identified:"]
            for law in action.laws:
                result_lines.append(
                    f"  • {law.act} — Section {law.section}\n"
                    f"    ↳ {law.description}\n"
                    f"    ↳ Punishment: {law.punishment}\n"
                    f"    ↳ Applicability strength: {law.strength:.0%}"
                )
            return "\n".join(result_lines)

        elif atype == ActionType.RANK_VIOLATION:
            if not action.ranked_laws:
                return "❌ No ranking provided."
            s.ranked_violations = [{"rank": i+1, "law": l}
                                   for i, l in enumerate(action.ranked_laws)]
            ranked_str = "\n".join(
                f"  {i+1}. {law}" for i, law in enumerate(action.ranked_laws)
            )
            return f"📊 Violations ranked by strength:\n{ranked_str}"

        elif atype == ActionType.RECOMMEND_ACTION:
            if not action.legal_action:
                return "❌ No action recommended."
            act_val = action.legal_action.value \
                if hasattr(action.legal_action, "value") else action.legal_action
            s.recommended_actions.append(act_val)
            action_guide = self._get_action_guide(act_val, s.classified_domain)
            return (
                f"🎯 Recommended Action: **{act_val.upper()}**\n"
                f"{action_guide}"
            )

        elif atype == ActionType.FIND_JURISDICTION:
            if not action.jurisdiction:
                return "❌ No jurisdiction specified."
            jur_val = action.jurisdiction.value \
                if hasattr(action.jurisdiction, "value") else action.jurisdiction
            s.jurisdiction = jur_val
            guide = self._get_jurisdiction_guide(jur_val)
            return (
                f"🏛️ Jurisdiction: **{jur_val.upper()}**\n"
                f"{guide}"
            )

        elif atype == ActionType.LIST_EVIDENCE:
            if not action.evidence_items:
                return "❌ No evidence items listed."
            s.evidence_checklist = action.evidence_items
            items_str = "\n".join(f"  ☐ {item}" for item in action.evidence_items)
            return f"📁 Evidence Checklist:\n{items_str}"

        elif atype == ActionType.CHECK_LIMITATION:
            domain = s.classified_domain or "civil"
            lim    = LIMITATION_PERIODS.get(domain, {})
            days   = lim.get("days")
            note   = lim.get("note", "")
            s.limitation_status = f"{days} days" if days else "No strict limit"
            if days:
                return (
                    f"⏰ Limitation Period: **{days} days ({days//365} year(s))**\n"
                    f"📌 {note}\n"
                    f"⚠️ Act before deadline — courts rarely grant extensions."
                )
            return (
                f"⏰ No strict limitation period for {domain} cases.\n"
                f"📌 {note}\n"
                f"💡 However, act quickly — evidence becomes harder to gather over time."
            )

        elif atype == ActionType.ASK_CLARIFICATION:
            q = action.question or "Can you provide more details?"
            s.clarifications.append(q)
            # Simulate appellant response based on problem data
            response = self._simulate_clarification(q, s.problem)
            return (
                f"❓ Clarification asked: {q}\n"
                f"👤 Appellant's response: {response}"
            )

        elif atype == ActionType.ESCALATE:
            domain = s.classified_domain or "civil"
            jur_info = JURISDICTION_MAP.get(domain, {})
            escalation = jur_info.get("escalation", "High Court")
            return (
                f"⬆️ Escalation Path: If {domain} forum does not resolve issue,\n"
                f"   Next step → **{escalation.upper()}**\n"
                f"   Note: Exhaust lower forums first — High Court prefers this."
            )

        return f"Action {atype} applied."

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────

    def _build_observation(self, feedback: str) -> Observation:
        s = self._state
        return Observation(
            problem=s.problem,
            classified_domain=s.classified_domain,
            identified_laws=[LawReference(**l) if isinstance(l, dict) else l
                             for l in s.identified_laws],
            ranked_violations=s.ranked_violations,
            recommended_actions=s.recommended_actions,
            jurisdiction=s.jurisdiction,
            evidence_checklist=s.evidence_checklist,
            limitation_status=s.limitation_status,
            last_action_feedback=feedback,
            step_number=s.step_count,
            steps_remaining=self._task_cfg["max_steps"] - s.step_count,
            episode_complete=s.done,
            task_hint=self._task_cfg.get("hint", ""),
            clarifications_asked=s.clarifications,
        )

    def _is_complete(self, s: EpisodeState) -> bool:
        """Episode is complete when agent has covered all major analysis steps."""
        has_domain   = s.classified_domain is not None
        has_laws     = len(s.identified_laws) > 0
        has_action   = len(s.recommended_actions) > 0
        has_evidence = len(s.evidence_checklist) > 0
        return has_domain and has_laws and has_action and has_evidence

    def _state_dict(self, s: EpisodeState) -> Dict[str, Any]:
        return {
            "classified_domain":   s.classified_domain,
            "identified_laws":     s.identified_laws,
            "ranked_violations":   s.ranked_violations,
            "recommended_actions": s.recommended_actions,
            "jurisdiction":        s.jurisdiction,
            "evidence_checklist":  s.evidence_checklist,
            "limitation_status":   s.limitation_status,
        }

    def _record(self, s: EpisodeState, action: Action) -> None:
        s.action_history.append({
            "step":        s.step_count,
            "action_type": action.action_type,
            "problem_id":  action.problem_id,
            "reasoning":   action.reasoning,
            "details": {
                "domain":     action.domain,
                "laws":       [l.model_dump() for l in action.laws],
                "legal_action": action.legal_action,
                "jurisdiction": action.jurisdiction,
                "evidence":   action.evidence_items,
            }
        })

    def _get_action_guide(self, action: str, domain: Optional[str]) -> str:
        guides = {
            "file_fir": (
                "📍 How to file FIR:\n"
                "  1. Go to nearest police station\n"
                "  2. Write complaint in detail, get acknowledgment copy\n"
                "  3. If police refuses → approach Area Magistrate\n"
                "  4. Online: many states have e-FIR portals"
            ),
            "consumer_forum": (
                "📍 Consumer Forum Process:\n"
                "  1. Send legal notice to company first (30 days)\n"
                "  2. File complaint at District Consumer Forum\n"
                "  3. Under ₹1 crore → District Forum (filing fee: ₹100–₹4000)\n"
                "  4. Online: edaakhil.nic.in"
            ),
            "cyber_portal": (
                "📍 Cyber Crime Complaint:\n"
                "  1. File at: cybercrime.gov.in (24x7)\n"
                "  2. Also visit local Cyber Cell\n"
                "  3. Keep all screenshots, transaction IDs ready\n"
                "  4. For bank fraud: call bank helpline IMMEDIATELY"
            ),
            "rera_complaint": (
                "📍 RERA Complaint Process:\n"
                "  1. Check builder's RERA registration on state RERA portal\n"
                "  2. File complaint online on state RERA website\n"
                "  3. No lawyer needed for basic complaints\n"
                "  4. Relief: full refund + interest OR possession + compensation"
            ),
            "internal_complaint": (
                "📍 Internal Complaint Committee (POSH):\n"
                "  1. Submit written complaint to ICC within 3 months\n"
                "  2. If company has no ICC → Local Complaints Committee (District)\n"
                "  3. ICC must complete inquiry in 90 days\n"
                "  4. Keep all evidence — messages, emails, witness names"
            ),
            "labour_court": (
                "📍 Labour Court Process:\n"
                "  1. File complaint with Labour Commissioner first\n"
                "  2. Conciliation attempted first (free)\n"
                "  3. If no resolution → Labour Court\n"
                "  4. Limitation: usually 1 year from date of dispute"
            ),
        }
        return guides.get(action, f"📍 Proceed with {action} as appropriate.")

    def _get_jurisdiction_guide(self, jur: str) -> str:
        guides = {
            "cyber_cell": "Visit local police cyber cell OR file at cybercrime.gov.in",
            "consumer_district_forum": "File at District Consumer Disputes Redressal Commission",
            "rera_authority": "File at State RERA Authority — search your state's RERA portal",
            "internal_complaints_committee": "Submit to ICC within your organization",
            "labour_court": "Approach Labour Commissioner → then Labour Court if needed",
            "local_police": "Nearest police station. If refused, approach Magistrate u/s 156(3) CrPC",
            "district_court": "File civil suit in District Court of appropriate jurisdiction",
            "high_court": "Approach High Court if lower forums fail or urgent relief needed",
        }
        return guides.get(jur, f"Approach: {jur}")

    def _simulate_clarification(self, question: str, problem) -> str:
        """Simulate appellant answering clarification question."""
        q_lower = question.lower()
        if "payment" in q_lower or "receipt" in q_lower or "proof" in q_lower:
            return "Haan, mere paas UPI screenshot hai aur bank statement bhi hai."
        if "when" in q_lower or "kab" in q_lower or "date" in q_lower:
            return f"Incident approximately {problem.time_of_incident} hua tha."
        if "amount" in q_lower or "paisa" in q_lower or "money" in q_lower:
            amt = problem.amount_involved
            return f"Total ₹{amt:,.0f} involved." if amt else "Exact amount abhi yaad nahi."
        if "police" in q_lower or "complaint" in q_lower:
            return "Abhi tak koi official complaint nahi ki — isliye aapke paas aaya/aayi."
        if "witness" in q_lower or "gawah" in q_lower:
            return "Kuch colleagues ne dekha hai, lekin official witness nahi hai."
        return "Haan, main woh information provide kar sakta/sakti hoon."
