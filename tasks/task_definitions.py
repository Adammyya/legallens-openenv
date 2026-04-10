"""
LegalLens AI — Task Definitions
3 Tasks: Easy → Medium → Hard
Each has a real appellant problem statement + gold standard answer.
"""

from __future__ import annotations
from typing import Any, Dict, List
from legallens_openenv.models import AppellantProblem, LegalDomain, LegalAction, Jurisdiction


# ─────────────────────────────────────────────
# TASK 1 — EASY
# Online Shopping Fraud
# ─────────────────────────────────────────────

TASK_1_PROBLEM = AppellantProblem(
    problem_id="PROB_001",
    statement=(
        "Maine ek website se ₹15,000 ka mobile phone order kiya tha. "
        "Maine UPI se payment kar di. Order confirm bhi hua, tracking number bhi mila. "
        "Lekin 3 hafte ho gaye, na phone aaya na refund. "
        "Jab website pe contact kiya toh customer care number band aa raha hai. "
        "Website ab open bhi nahi ho rahi. Mera paisa le ke bhaag gaye."
    ),
    keywords=["online fraud", "payment done", "product not received", "website closed",
              "UPI payment", "no refund", "fake website"],
    amount_involved=15000.0,
    time_of_incident="3 weeks ago",
    parties_involved=["Appellant", "Fake online seller"],
    location="Online",
    prior_action="Tried contacting customer care — number not working",
    urgency="high",
)

TASK_1_GOLD_STANDARD = {
    "correct_domain":  LegalDomain.CYBER,
    "correct_laws":    ["IT_66D", "IPC_420", "CPA_DEF_SERVICE"],
    "primary_law":     "IT_66D",
    "correct_action":  LegalAction.CYBER_PORTAL,
    "secondary_action": LegalAction.CONSUMER_FORUM,
    "correct_jurisdiction": Jurisdiction.CYBER_CELL,
    "key_evidence": [
        "Payment proof (UPI screenshot)",
        "Order confirmation screenshot",
        "Website URL and screenshots",
        "Bank statement showing deduction",
    ],
    "limitation_applicable": False,
    "amount_threshold": 15000,
}

TASK_1_CONFIG = {
    "task_id":    "task_1_easy",
    "name":       "Online Shopping Fraud",
    "difficulty": "easy",
    "description": (
        "Appellant ne fake website se phone order kiya, paisa gaya, product nahi aaya. "
        "Agent ko identify karna hai — IT Act 66D (cyber fraud) + IPC 420 (cheating) + "
        "Consumer Protection Act. Primary action: cybercrime.gov.in complaint."
    ),
    "problem":    TASK_1_PROBLEM,
    "gold":       TASK_1_GOLD_STANDARD,
    "max_steps":  12,
    "hint": (
        "Yeh online fraud hai — IT Act 66D (online cheating) sabse strong law hai. "
        "IPC 420 bhi apply hota hai. Action: pehle cybercrime.gov.in pe complaint, "
        "phir Consumer Forum (refund ke liye)."
    ),
}


# ─────────────────────────────────────────────
# TASK 2 — MEDIUM
# Workplace Harassment + Salary Withheld
# Multiple laws overlap
# ─────────────────────────────────────────────

TASK_2_PROBLEM = AppellantProblem(
    problem_id="PROB_002",
    statement=(
        "Main ek private company mein kaam karti hoon. "
        "Mere senior manager ne mujhe last 2 mahine se uncomfortable feel karaaya hai — "
        "inappropriate comments karta hai, akele cabin mein bulata hai. "
        "Jab maine HR ko bataya toh unhone kaha 'kuch nahi hua hoga, tum over-react kar rahi ho.' "
        "Ab manager ne meri performance rating kharab kar di aur kehta hai ki agar "
        "complaint ki toh job se nikaala jaayega. "
        "Aur pichle mahine ki salary bhi nahi aayi — HR bol raha hai 'processing mein hai.'"
    ),
    keywords=["workplace harassment", "sexual harassment", "salary withheld",
              "manager threatening", "HR not helping", "inappropriate behaviour",
              "job threat", "performance rating"],
    amount_involved=None,
    time_of_incident="Last 2 months",
    parties_involved=["Appellant (female employee)", "Senior Manager", "HR Department"],
    location="Private company office",
    prior_action="Complained to HR verbally — ignored",
    urgency="high",
)

TASK_2_GOLD_STANDARD = {
    "correct_domain":  LegalDomain.LABOUR,
    "correct_laws":    ["POSH_3", "POWA_15", "IPC_506", "IPC_354"],
    "primary_law":     "POSH_3",
    "correct_action":  LegalAction.INTERNAL_COMPLAINT,
    "secondary_action": LegalAction.LABOUR_COURT,
    "correct_jurisdiction": Jurisdiction.ICC,
    "key_evidence": [
        "Written complaint to HR (get acknowledgment)",
        "Messages / emails from manager",
        "Salary slip showing non-payment",
        "Bank statement (salary not credited)",
        "Witnesses in office",
        "Any previous communication records",
    ],
    "limitation_applicable": False,
    "overlapping_laws": True,
    "note": "POSH Act — ICC complaint first. Salary issue — Payment of Wages Act S.15.",
}

TASK_2_CONFIG = {
    "task_id":    "task_2_medium",
    "name":       "Workplace Harassment + Salary Issue",
    "difficulty": "medium",
    "description": (
        "Female employee — manager se sexual harassment + HR ne complaint ignore ki + "
        "job threat + salary withheld. Multiple laws overlap: POSH Act (harassment), "
        "Payment of Wages Act (salary), IPC 506 (threat). "
        "Agent ko sahi priority order mein laws identify karni hain."
    ),
    "problem":    TASK_2_PROBLEM,
    "gold":       TASK_2_GOLD_STANDARD,
    "max_steps":  18,
    "hint": (
        "Yahan 2 alag problems hain — harassment alag law, salary alag law. "
        "POSH Act S.3 harassment ke liye, Payment of Wages Act S.15 salary ke liye. "
        "IPC 506 (threat) bhi apply hota hai. "
        "ICC mein complaint pehle — agar ICC nahi hai toh Local Complaints Committee."
    ),
}


# ─────────────────────────────────────────────
# TASK 3 — HARD
# Builder Fraud + Counter Legal Notice + Multiple Forums
# ─────────────────────────────────────────────

TASK_3_PROBLEM = AppellantProblem(
    problem_id="PROB_003",
    statement=(
        "Maine 2019 mein ek builder se ₹45 lakh mein flat book kiya. "
        "Agreement mein likha tha ki possession December 2021 mein milegi. "
        "Aaj 2024 hai — na possession mili, na paisa wapas. "
        "Builder ka kehna hai ki COVID ki wajah se delay hua — lekin maine notice kiya ki "
        "agreement mein ek clause tha jo unhone mujhse chhupaaya — usme likha tha ki "
        "builder ko 5 saal tak delay karne ka haq hai bina kisi penalty ke. "
        "Jab maine complaint ki toh builder ne mujhe ek legal notice bheja ki "
        "maine unki reputation kharab ki hai aur ₹10 lakh ka defamation case karega. "
        "Maine home loan bhi liya tha — bank ka EMI chal raha hai lekin flat nahi mila. "
        "Mujhe samajh nahi aa raha — kahan jaoon, kya karoon, aur woh notice ka kya karoon."
    ),
    keywords=["builder fraud", "flat not delivered", "possession delayed",
              "hidden clause", "agreement fraud", "legal notice received",
              "defamation threat", "home loan", "RERA", "counter notice"],
    amount_involved=4500000.0,
    time_of_incident="2019 to present (2024)",
    parties_involved=["Appellant", "Builder/Developer", "Bank (home loan)"],
    location="Real estate — residential flat",
    prior_action="Verbal complaint to builder, received legal notice in return",
    urgency="critical",
)

TASK_3_GOLD_STANDARD = {
    "correct_domain":  LegalDomain.PROPERTY,
    "correct_laws":    ["RERA_18", "RERA_12", "IPC_420", "IPC_406", "CPA_DEF_SERVICE", "IPC_500"],
    "primary_law":     "RERA_18",
    "correct_action":  LegalAction.RERA_COMPLAINT,
    "secondary_action": LegalAction.CONSUMER_FORUM,
    "tertiary_action": LegalAction.SEND_LEGAL_NOTICE,
    "correct_jurisdiction": Jurisdiction.RERA_AUTHORITY,
    "key_evidence": [
        "Original builder-buyer agreement",
        "All payment receipts to builder",
        "Bank loan documents and EMI statements",
        "Original advertisement / brochure",
        "All written communication with builder",
        "Copy of hidden clause (highlighted)",
        "Builder's legal notice (received)",
        "RERA project registration number",
    ],
    "limitation_applicable": False,
    "counter_notice_response": True,
    "overlapping_laws": True,
    "complexity_factors": [
        "Hidden clause in agreement",
        "Counter legal notice from builder",
        "Multiple forums available",
        "Bank loan involved",
        "Defamation threat",
    ],
    "note": (
        "RERA S.18 — full refund + interest OR possession with compensation. "
        "RERA S.12 — false representation in agreement. "
        "IPC 420 + 406 — criminal fraud + breach of trust. "
        "Counter notice — builder ka defamation threat weak hai, "
        "consumer/RERA complaint filing is a legal right. "
        "Priority: RERA first (fastest relief), Consumer Forum parallel."
    ),
}

TASK_3_CONFIG = {
    "task_id":    "task_3_hard",
    "name":       "Builder Fraud + Counter Legal Notice",
    "difficulty": "hard",
    "description": (
        "₹45 lakh flat — 3 saal se possession nahi, hidden clause in agreement, "
        "builder ne defamation notice bheja, home loan EMI chal raha hai. "
        "Agent ko: RERA + IPC + Consumer Forum sab identify karna hai, "
        "counter notice ka response strategy dena hai, priority order decide karna hai."
    ),
    "problem":    TASK_3_PROBLEM,
    "gold":       TASK_3_GOLD_STANDARD,
    "max_steps":  25,
    "hint": (
        "Yeh multi-law case hai. RERA S.18 (possession delay) primary. "
        "RERA S.12 (hidden clause = misrepresentation). "
        "IPC 420 + 406 parallel criminal complaint. "
        "Builder ka defamation notice — ignore mat karo, "
        "lekin RERA complaint filing defamation nahi hai — yeh legal right hai. "
        "Consumer Forum bhi parallel file kar sakte hain."
    ),
}


# ─────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────

ALL_TASKS: Dict[str, Dict] = {
    "task_1_easy":   TASK_1_CONFIG,
    "task_2_medium": TASK_2_CONFIG,
    "task_3_hard":   TASK_3_CONFIG,
}
