"""
LegalLens AI — Pydantic Models
Typed Observation, Action, Reward, and State models.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────

class LegalDomain(str, Enum):
    CRIMINAL  = "criminal"
    CIVIL     = "civil"
    CONSUMER  = "consumer"
    LABOUR    = "labour"
    CYBER     = "cyber"
    FAMILY    = "family"
    PROPERTY  = "property"
    UNKNOWN   = "unknown"


class ActionType(str, Enum):
    CLASSIFY_DOMAIN   = "classify_domain"     # Identify legal domain
    IDENTIFY_LAW      = "identify_law"         # Map to specific law/section
    RANK_VIOLATION    = "rank_violation"       # Rank violations by strength
    RECOMMEND_ACTION  = "recommend_action"     # Suggest legal action
    FIND_JURISDICTION = "find_jurisdiction"    # Which court/authority
    LIST_EVIDENCE     = "list_evidence"        # What documents needed
    CHECK_LIMITATION  = "check_limitation"     # Deadline to file case
    ESCALATE          = "escalate"             # Next level if local fails
    ASK_CLARIFICATION = "ask_clarification"   # Ask appellant for more info


class LegalAction(str, Enum):
    FILE_FIR            = "file_fir"
    CONSUMER_FORUM      = "consumer_forum"
    CIVIL_SUIT          = "civil_suit"
    LABOUR_COURT        = "labour_court"
    CYBER_PORTAL        = "cyber_portal"
    HIGH_COURT          = "high_court"
    SUPREME_COURT       = "supreme_court"
    RERA_COMPLAINT      = "rera_complaint"
    INTERNAL_COMPLAINT  = "internal_complaint"   # e.g. POSH ICC
    SEND_LEGAL_NOTICE   = "send_legal_notice"
    MEDIATION           = "mediation"
    NEGOTIATION         = "negotiation"


class Jurisdiction(str, Enum):
    LOCAL_POLICE        = "local_police"
    DISTRICT_COURT      = "district_court"
    HIGH_COURT          = "high_court"
    SUPREME_COURT       = "supreme_court"
    CONSUMER_FORUM      = "consumer_district_forum"
    STATE_COMMISSION    = "state_consumer_commission"
    NATIONAL_COMMISSION = "national_consumer_commission"
    LABOUR_COURT        = "labour_court"
    CYBER_CELL          = "cyber_cell"
    RERA_AUTHORITY      = "rera_authority"
    ICC                 = "internal_complaints_committee"


# ─────────────────────────────────────────────
# Law Reference Model
# ─────────────────────────────────────────────

class LawReference(BaseModel):
    act:         str   = Field(description="Name of the Act e.g. IPC, IT Act 2000")
    section:     str   = Field(description="Section number e.g. 420, 66C")
    description: str   = Field(description="What this section covers")
    punishment:  str   = Field(description="Penalty / relief available")
    strength:    float = Field(ge=0.0, le=1.0, description="How strongly this applies 0-1")


# ─────────────────────────────────────────────
# Appellant Problem
# ─────────────────────────────────────────────

class AppellantProblem(BaseModel):
    problem_id:       str
    statement:        str   = Field(description="Raw problem statement from appellant")
    keywords:         List[str] = Field(description="Key facts extracted from statement")
    amount_involved:  Optional[float] = Field(default=None, description="Money involved in INR")
    time_of_incident: Optional[str]   = Field(default=None, description="When did incident happen")
    parties_involved: List[str]       = Field(default=[], description="Who is involved")
    location:         Optional[str]   = Field(default=None, description="Where did it happen")
    prior_action:     Optional[str]   = Field(default=None, description="What has appellant done so far")
    urgency:          str             = Field(default="normal", description="low/normal/high/critical")


# ─────────────────────────────────────────────
# Observation
# ─────────────────────────────────────────────

class Observation(BaseModel):
    """What the agent sees at each step."""
    problem:               AppellantProblem
    classified_domain:     Optional[str]           = None
    identified_laws:       List[LawReference]      = []
    ranked_violations:     List[Dict[str, Any]]    = []
    recommended_actions:   List[str]               = []
    jurisdiction:          Optional[str]           = None
    evidence_checklist:    List[str]               = []
    limitation_status:     Optional[str]           = None
    last_action_feedback:  str                     = ""
    step_number:           int                     = 0
    steps_remaining:       int                     = 0
    episode_complete:      bool                    = False
    task_hint:             str                     = ""
    clarifications_asked:  List[str]               = []


# ─────────────────────────────────────────────
# Action
# ─────────────────────────────────────────────

class Action(BaseModel):
    """Action taken by the agent."""
    action_type:    ActionType
    problem_id:     str
    # For classify_domain
    domain:         Optional[LegalDomain]  = None
    # For identify_law
    laws:           List[LawReference]     = []
    # For rank_violation
    ranked_laws:    List[str]              = []   # section IDs in priority order
    # For recommend_action
    legal_action:   Optional[LegalAction] = None
    # For find_jurisdiction
    jurisdiction:   Optional[Jurisdiction]= None
    # For list_evidence
    evidence_items: List[str]             = []
    # For check_limitation
    limitation_days: Optional[int]        = None
    # For ask_clarification
    question:       Optional[str]         = None
    # Always
    reasoning:      str                   = ""

    class Config:
        use_enum_values = True


# ─────────────────────────────────────────────
# Reward
# ─────────────────────────────────────────────

class Reward(BaseModel):
    """Structured reward with sub-components."""
    total:               float = 0.0
    domain_accuracy:     float = 0.0
    law_identification:  float = 0.0
    action_correctness:  float = 0.0
    jurisdiction_match:  float = 0.0
    evidence_quality:    float = 0.0
    penalty:             float = 0.0

    class Config:
        frozen = True


# ─────────────────────────────────────────────
# Episode State
# ─────────────────────────────────────────────

class EpisodeState(BaseModel):
    """Full internal state returned by state()."""
    task_id:             str
    task_name:           str
    task_difficulty:     str
    problem:             AppellantProblem
    classified_domain:   Optional[str]        = None
    identified_laws:     List[LawReference]   = []
    ranked_violations:   List[Dict[str, Any]] = []
    recommended_actions: List[str]            = []
    jurisdiction:        Optional[str]        = None
    evidence_checklist:  List[str]            = []
    limitation_status:   Optional[str]        = None
    clarifications:      List[str]            = []
    action_history:      List[Dict[str, Any]] = []
    step_count:          int                  = 0
    total_reward:        float                = 0.0
    done:                bool                 = False
