"""
LegalLens AI — Grader
Deterministic scoring for each agent action and full episode.
Score range: 0.0 – 1.0
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from legallens_openenv.models import Action, ActionType, Reward


# ─────────────────────────────────────────────
# Weights
# ─────────────────────────────────────────────

EPISODE_WEIGHTS = {
    "domain_accuracy":    0.20,
    "law_identification": 0.35,
    "action_correctness": 0.25,
    "jurisdiction_match": 0.10,
    "evidence_quality":   0.10,
}


# ─────────────────────────────────────────────
# Domain scoring
# ─────────────────────────────────────────────

DOMAIN_ADJACENCY = {
    # (assigned, correct) → partial score
    ("cyber",    "criminal"): 0.6,
    ("criminal", "cyber"):    0.6,
    ("consumer", "criminal"): 0.5,
    ("criminal", "consumer"): 0.5,
    ("labour",   "criminal"): 0.5,
    ("civil",    "property"): 0.6,
    ("property", "civil"):    0.6,
}


def score_domain(assigned: Optional[str], correct: str) -> float:
    if not assigned:
        return 0.0
    if assigned == correct:
        return 1.0
    return DOMAIN_ADJACENCY.get((assigned, correct), 0.2)


# ─────────────────────────────────────────────
# Law identification scoring
# ─────────────────────────────────────────────

def score_law_identification(
    identified: List[str],
    gold_laws: List[str],
    primary_law: str,
) -> Tuple[float, float]:
    """
    Returns (law_score, penalty).
    - Full marks for identifying primary law
    - Partial for additional correct laws
    - Penalty for completely wrong laws
    """
    if not identified:
        return 0.0, 0.0

    identified_set = set(identified)
    gold_set       = set(gold_laws)

    correct   = identified_set & gold_set
    incorrect = identified_set - gold_set

    # Primary law carries 50% of law score
    primary_score = 0.5 if primary_law in identified_set else 0.0

    # Additional laws: each correct one adds proportional score
    other_gold    = gold_set - {primary_law}
    other_correct = correct  - {primary_law}
    other_score   = (len(other_correct) / max(len(other_gold), 1)) * 0.5 if other_gold else 0.5

    law_score = primary_score + other_score

    # Penalty for wrong laws (not too harsh — agent may over-identify)
    penalty = min(0.3, len(incorrect) * 0.08)

    return round(law_score, 4), round(-penalty, 4)


# ─────────────────────────────────────────────
# Action correctness scoring
# ─────────────────────────────────────────────

def score_action(
    recommended: List[str],
    correct_primary: str,
    correct_secondary: Optional[str],
) -> float:
    if not recommended:
        return 0.0

    recommended_set = set(recommended)

    primary_score   = 0.7 if correct_primary   in recommended_set else 0.0
    secondary_score = 0.3 if correct_secondary and correct_secondary in recommended_set else 0.0

    # If primary is wrong but secondary is right — partial
    if primary_score == 0.0 and secondary_score > 0.0:
        secondary_score = 0.2

    return round(min(1.0, primary_score + secondary_score), 4)


# ─────────────────────────────────────────────
# Jurisdiction scoring
# ─────────────────────────────────────────────

def score_jurisdiction(assigned: Optional[str], correct: str) -> float:
    if not assigned:
        return 0.0
    if assigned == correct:
        return 1.0
    # Partial — at least in right ballpark
    partial_matches = {
        ("district_court",             "local_police"):             0.5,
        ("local_police",               "cyber_cell"):               0.4,
        ("cyber_cell",                 "local_police"):             0.4,
        ("state_consumer_commission",  "consumer_district_forum"):  0.6,
        ("national_consumer_commission","consumer_district_forum"): 0.4,
        ("high_court",                 "labour_court"):             0.4,
    }
    return partial_matches.get((assigned, correct), 0.1)


# ─────────────────────────────────────────────
# Evidence quality scoring
# ─────────────────────────────────────────────

def score_evidence(provided: List[str], gold: List[str]) -> float:
    if not gold:
        return 1.0
    if not provided:
        return 0.0
    provided_lower = [e.lower() for e in provided]
    gold_lower     = [e.lower() for e in gold]

    matches = sum(
        any(g_word in p for p in provided_lower)
        for g_word in [g.split()[0].lower() for g in gold_lower]
    )
    return round(min(1.0, matches / len(gold_lower)), 4)


# ─────────────────────────────────────────────
# Step-level reward
# ─────────────────────────────────────────────

def compute_step_reward(
    action: Action,
    gold: Dict[str, Any],
    current_state: Dict[str, Any],
) -> Reward:
    """Compute reward for a single step."""

    domain_r     = 0.0
    law_r        = 0.0
    action_r     = 0.0
    jurisdiction_r = 0.0
    evidence_r   = 0.0
    penalty_r    = 0.0

    atype = action.action_type

    if atype == ActionType.CLASSIFY_DOMAIN:
        domain_r = score_domain(
            action.domain,
            gold["correct_domain"].value if hasattr(gold["correct_domain"], "value")
            else gold["correct_domain"]
        ) * 0.8  # partial credit at step level

    elif atype == ActionType.IDENTIFY_LAW:
        identified = [l.section.replace("Section ", "").strip() if "Section" in l.section
                     else l.act.split()[0] + "_" + l.section
                     for l in action.laws]
        # simpler: use short names
        identified_shorts = [l.act[:3].upper() + "_" + l.section.replace("Section ", "")
                             for l in action.laws]
        # Match against gold law keys
        gold_laws    = gold.get("correct_laws", [])
        primary_law  = gold.get("primary_law", "")

        # Try matching by short key presence
        matched = []
        for law in action.laws:
            for gold_key in gold_laws:
                if (gold_key.split("_")[0].upper() in law.act.upper() and
                        gold_key.split("_")[-1] in law.section):
                    matched.append(gold_key)

        law_s, law_p = score_law_identification(matched, gold_laws, primary_law)
        law_r    = law_s * 0.9
        penalty_r = law_p

    elif atype == ActionType.RECOMMEND_ACTION:
        acts = [action.legal_action] if action.legal_action else []
        action_r = score_action(
            [a.value if hasattr(a, "value") else a for a in acts],
            gold.get("correct_action", "").value
            if hasattr(gold.get("correct_action", ""), "value")
            else str(gold.get("correct_action", "")),
            gold.get("secondary_action", "").value
            if hasattr(gold.get("secondary_action", ""), "value")
            else str(gold.get("secondary_action", "")),
        ) * 0.9

    elif atype == ActionType.FIND_JURISDICTION:
        jurisdiction_r = score_jurisdiction(
            action.jurisdiction.value if action.jurisdiction else None,
            gold.get("correct_jurisdiction", "").value
            if hasattr(gold.get("correct_jurisdiction", ""), "value")
            else str(gold.get("correct_jurisdiction", "")),
        ) * 0.9

    elif atype == ActionType.LIST_EVIDENCE:
        evidence_r = score_evidence(
            action.evidence_items,
            gold.get("key_evidence", []),
        ) * 0.8

    elif atype == ActionType.ASK_CLARIFICATION:
        # Small reward for seeking info — especially useful in hard tasks
        law_r = 0.05

    elif atype == ActionType.CHECK_LIMITATION:
        # Reward for checking limitation — always good practice
        law_r = 0.08

    elif atype == ActionType.RANK_VIOLATION:
        # Check if primary law is ranked first
        if action.ranked_laws and gold.get("primary_law"):
            primary = gold["primary_law"]
            top_ranked = action.ranked_laws[0] if action.ranked_laws else ""
            if primary.split("_")[-1] in top_ranked or top_ranked in primary:
                law_r = 0.2

    total = domain_r + law_r + action_r + jurisdiction_r + evidence_r + penalty_r
    return Reward(
        total=round(total, 4),
        domain_accuracy=round(domain_r, 4),
        law_identification=round(law_r, 4),
        action_correctness=round(action_r, 4),
        jurisdiction_match=round(jurisdiction_r, 4),
        evidence_quality=round(evidence_r, 4),
        penalty=round(penalty_r, 4),
    )


# ─────────────────────────────────────────────
# Episode grader
# ─────────────────────────────────────────────

def grade_episode(
    gold: Dict[str, Any],
    action_history: List[Dict[str, Any]],
    final_state: Dict[str, Any],
    total_steps: int,
    max_steps: int,
) -> Dict[str, Any]:
    """Full episode grader. Returns score 0.0–1.0."""

    # Collect what the agent did across the episode
    domain_classified   = final_state.get("classified_domain")
    laws_identified     = final_state.get("identified_laws", [])
    actions_recommended = final_state.get("recommended_actions", [])
    jurisdiction_set    = final_state.get("jurisdiction")
    evidence_listed     = final_state.get("evidence_checklist", [])

    # ── Domain score ──────────────────────────────────────────────────────────
    correct_domain = gold["correct_domain"].value \
        if hasattr(gold["correct_domain"], "value") else gold["correct_domain"]
    d_score = score_domain(domain_classified, correct_domain)

    # ── Law score ─────────────────────────────────────────────────────────────
    gold_laws   = gold.get("correct_laws", [])
    primary_law = gold.get("primary_law", "")

    matched_laws = []
    for law_ref in laws_identified:
        for gold_key in gold_laws:
            parts = gold_key.split("_")
            act_abbr = parts[0]
            section  = "_".join(parts[1:])
            if (act_abbr.upper() in str(law_ref.get("act", "")).upper() and
                    section in str(law_ref.get("section", ""))):
                matched_laws.append(gold_key)

    l_score, l_penalty = score_law_identification(matched_laws, gold_laws, primary_law)

    # ── Action score ──────────────────────────────────────────────────────────
    correct_primary   = gold.get("correct_action",   "")
    correct_secondary = gold.get("secondary_action", "")
    if hasattr(correct_primary,   "value"): correct_primary   = correct_primary.value
    if hasattr(correct_secondary, "value"): correct_secondary = correct_secondary.value

    a_score = score_action(actions_recommended, correct_primary, correct_secondary)

    # ── Jurisdiction score ────────────────────────────────────────────────────
    correct_jur = gold.get("correct_jurisdiction", "")
    if hasattr(correct_jur, "value"): correct_jur = correct_jur.value
    j_score = score_jurisdiction(jurisdiction_set, correct_jur)

    # ── Evidence score ────────────────────────────────────────────────────────
    e_score = score_evidence(evidence_listed, gold.get("key_evidence", []))

    # ── Weighted total ────────────────────────────────────────────────────────
    base_score = (
        EPISODE_WEIGHTS["domain_accuracy"]    * d_score
        + EPISODE_WEIGHTS["law_identification"] * (l_score + l_penalty)
        + EPISODE_WEIGHTS["action_correctness"] * a_score
        + EPISODE_WEIGHTS["jurisdiction_match"] * j_score
        + EPISODE_WEIGHTS["evidence_quality"]   * e_score
    )

    # Efficiency bonus
    step_ratio     = total_steps / max(max_steps, 1)
    efficiency_adj = 0.05 * (1.0 - step_ratio)
    final_score    = round(max(0.0, min(1.0, base_score + efficiency_adj)), 4)

    return {
        "final_score":      final_score,
        "base_score":       round(base_score, 4),
        "efficiency_adj":   round(efficiency_adj, 4),
        "breakdown": {
            "domain_accuracy":    round(d_score, 4),
            "law_identification": round(l_score + l_penalty, 4),
            "action_correctness": round(a_score, 4),
            "jurisdiction_match": round(j_score, 4),
            "evidence_quality":   round(e_score, 4),
        },
        "matched_laws":   matched_laws,
        "total_steps":    total_steps,
        "max_steps":      max_steps,
    }
