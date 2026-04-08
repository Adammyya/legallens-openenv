"""
LegalLens AI — Indian Laws Knowledge Base
Complete mapping of laws, sections, and their applicability.
"""

from __future__ import annotations
from typing import Dict, List, Any

# ─────────────────────────────────────────────
# MASTER LAW DATABASE
# Each entry: act → section → details
# ─────────────────────────────────────────────

LAW_DATABASE: Dict[str, Dict[str, Any]] = {

    # ── IPC — Indian Penal Code ───────────────────────────────────────────────
    "IPC_420": {
        "act": "Indian Penal Code",
        "section": "420",
        "short": "IPC 420",
        "description": "Cheating and dishonestly inducing delivery of property",
        "punishment": "Up to 7 years imprisonment + fine",
        "keywords": ["cheating", "fraud", "money taken", "product not delivered",
                     "fake", "deceived", "false promise", "scam", "paisa gaya"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.9,
    },
    "IPC_406": {
        "act": "Indian Penal Code",
        "section": "406",
        "short": "IPC 406",
        "description": "Criminal breach of trust",
        "punishment": "Up to 3 years imprisonment + fine",
        "keywords": ["trust", "money kept", "entrusted", "not returned",
                     "breach", "held money", "builder", "agent"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.85,
    },
    "IPC_384": {
        "act": "Indian Penal Code",
        "section": "384",
        "short": "IPC 384",
        "description": "Extortion",
        "punishment": "Up to 3 years imprisonment + fine",
        "keywords": ["extortion", "threatening for money", "blackmail",
                     "forcefully taking money", "dhamki de ke paisa"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.88,
    },
    "IPC_498A": {
        "act": "Indian Penal Code",
        "section": "498A",
        "short": "IPC 498A",
        "description": "Husband or relative subjecting wife to cruelty",
        "punishment": "Up to 3 years imprisonment + fine",
        "keywords": ["domestic violence", "husband", "in-laws", "cruelty",
                     "harassment by husband", "dowry", "wife"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.92,
    },
    "IPC_354": {
        "act": "Indian Penal Code",
        "section": "354",
        "short": "IPC 354",
        "description": "Assault or criminal force against woman to outrage modesty",
        "punishment": "1 to 5 years imprisonment + fine",
        "keywords": ["molestation", "outrage modesty", "physical harassment",
                     "touching inappropriately", "assault woman"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.93,
    },
    "IPC_506": {
        "act": "Indian Penal Code",
        "section": "506",
        "short": "IPC 506",
        "description": "Criminal intimidation / threatening",
        "punishment": "Up to 2 years imprisonment + fine",
        "keywords": ["threat", "threatening", "dhamki", "intimidation",
                     "harm threatened", "job threatened", "will hurt"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.80,
    },
    "IPC_500": {
        "act": "Indian Penal Code",
        "section": "500",
        "short": "IPC 500",
        "description": "Defamation",
        "punishment": "Up to 2 years imprisonment + fine",
        "keywords": ["defamation", "false statements", "reputation damaged",
                     "false rumours", "badnami", "false social media post"],
        "domain": "criminal",
        "forum": "local_police",
        "strength_base": 0.75,
    },

    # ── Consumer Protection Act 2019 ──────────────────────────────────────────
    "CPA_DEF_SERVICE": {
        "act": "Consumer Protection Act 2019",
        "section": "Section 2(11) — Deficiency of Service",
        "short": "CPA Deficiency of Service",
        "description": "Any fault, imperfection, shortcoming in service promised",
        "punishment": "Compensation + refund + punitive damages",
        "keywords": ["service not provided", "product not delivered", "delayed service",
                     "poor quality", "not as promised", "online shopping", "refund nahi mila"],
        "domain": "consumer",
        "forum": "consumer_forum",
        "strength_base": 0.88,
    },
    "CPA_UNFAIR_TRADE": {
        "act": "Consumer Protection Act 2019",
        "section": "Section 2(47) — Unfair Trade Practice",
        "short": "CPA Unfair Trade Practice",
        "description": "False representation, misleading advertisement, deceptive pricing",
        "punishment": "Compensation + cease and desist order",
        "keywords": ["misleading ad", "false advertisement", "bait and switch",
                     "hidden charges", "fake discount", "wrong price shown"],
        "domain": "consumer",
        "forum": "consumer_forum",
        "strength_base": 0.82,
    },
    "CPA_PRODUCT_LIABILITY": {
        "act": "Consumer Protection Act 2019",
        "section": "Chapter VI — Product Liability",
        "short": "CPA Product Liability",
        "description": "Manufacturer/seller liable for defective product causing harm",
        "punishment": "Compensation for harm caused",
        "keywords": ["defective product", "product caused injury", "faulty goods",
                     "manufacturing defect", "product harmed"],
        "domain": "consumer",
        "forum": "consumer_forum",
        "strength_base": 0.85,
    },

    # ── IT Act 2000 ───────────────────────────────────────────────────────────
    "IT_66": {
        "act": "Information Technology Act 2000",
        "section": "66",
        "short": "IT Act 66",
        "description": "Computer related offences — hacking, data theft",
        "punishment": "Up to 3 years imprisonment + fine up to ₹5 lakh",
        "keywords": ["hacking", "unauthorized access", "data stolen",
                     "account hacked", "computer crime", "password stolen"],
        "domain": "cyber",
        "forum": "cyber_cell",
        "strength_base": 0.87,
    },
    "IT_66C": {
        "act": "Information Technology Act 2000",
        "section": "66C",
        "short": "IT Act 66C",
        "description": "Identity theft — using another's electronic signature/password",
        "punishment": "Up to 3 years imprisonment + fine up to ₹1 lakh",
        "keywords": ["identity theft", "fake profile", "someone using my account",
                     "impersonation", "fake ID", "profile cloned"],
        "domain": "cyber",
        "forum": "cyber_cell",
        "strength_base": 0.90,
    },
    "IT_66D": {
        "act": "Information Technology Act 2000",
        "section": "66D",
        "short": "IT Act 66D",
        "description": "Cheating by personation using computer resource",
        "punishment": "Up to 3 years imprisonment + fine up to ₹1 lakh",
        "keywords": ["online fraud", "fake website", "cyber fraud", "UPI fraud",
                     "online cheating", "fake call", "OTP fraud", "phishing"],
        "domain": "cyber",
        "forum": "cyber_cell",
        "strength_base": 0.91,
    },
    "IT_67": {
        "act": "Information Technology Act 2000",
        "section": "67",
        "short": "IT Act 67",
        "description": "Publishing obscene material in electronic form",
        "punishment": "Up to 3 years imprisonment + fine up to ₹5 lakh",
        "keywords": ["obscene content", "morphed photos", "intimate images shared",
                     "revenge porn", "objectionable content online"],
        "domain": "cyber",
        "forum": "cyber_cell",
        "strength_base": 0.89,
    },

    # ── POSH Act 2013 ─────────────────────────────────────────────────────────
    "POSH_3": {
        "act": "Sexual Harassment of Women at Workplace Act 2013 (POSH)",
        "section": "Section 3",
        "short": "POSH Act S.3",
        "description": "Prevention of sexual harassment at workplace",
        "punishment": "Warning, termination, compensation — up to ₹50,000",
        "keywords": ["workplace harassment", "sexual harassment", "boss harassing",
                     "colleague harassment", "uncomfortable at office",
                     "inappropriate comments at work", "POSH"],
        "domain": "labour",
        "forum": "internal_complaints_committee",
        "strength_base": 0.92,
    },

    # ── Payment of Wages Act ──────────────────────────────────────────────────
    "POWA_15": {
        "act": "Payment of Wages Act 1936",
        "section": "Section 15",
        "short": "Payment of Wages Act S.15",
        "description": "Employer failing to pay wages on time or deducting illegally",
        "punishment": "Compensation 10x the delayed wages",
        "keywords": ["salary not paid", "wages delayed", "illegal deduction",
                     "salary withheld", "paisa nahi mila", "salary rok li"],
        "domain": "labour",
        "forum": "labour_court",
        "strength_base": 0.88,
    },

    # ── RERA Act 2016 ─────────────────────────────────────────────────────────
    "RERA_18": {
        "act": "Real Estate (Regulation and Development) Act 2016",
        "section": "Section 18",
        "short": "RERA S.18",
        "description": "Builder failing to give possession of property on time",
        "punishment": "Full refund + interest OR compensation for delay",
        "keywords": ["flat not given", "builder delayed", "possession not received",
                     "property not delivered", "flat ka paisa gaya possession nahi",
                     "builder fraud", "housing project delayed"],
        "domain": "property",
        "forum": "rera_authority",
        "strength_base": 0.93,
    },
    "RERA_12": {
        "act": "Real Estate (Regulation and Development) Act 2016",
        "section": "Section 12",
        "short": "RERA S.12",
        "description": "Builder making false representation in advertisement/agreement",
        "punishment": "5% of cost of apartment as penalty",
        "keywords": ["builder lied", "agreement mein clause chhupaaya",
                     "false promises builder", "amenities not provided",
                     "different flat given", "layout changed"],
        "domain": "property",
        "forum": "rera_authority",
        "strength_base": 0.88,
    },
}


# ─────────────────────────────────────────────
# Evidence Checklists per domain
# ─────────────────────────────────────────────

EVIDENCE_CHECKLISTS: Dict[str, List[str]] = {
    "criminal": [
        "Written complaint / FIR copy",
        "Identity proof (Aadhar / PAN)",
        "Evidence of incident (screenshots, photos, videos)",
        "Witness names and contact details",
        "Any prior communication with accused (messages, emails)",
        "Bank statements if money involved",
    ],
    "consumer": [
        "Purchase receipt / invoice",
        "Order confirmation (email/SMS)",
        "Payment proof (bank statement / UPI screenshot)",
        "Product photos (if defective)",
        "All communication with seller/company",
        "Delivery status / tracking screenshot",
        "Any warranty card",
    ],
    "cyber": [
        "Screenshots of fraud / hack",
        "Transaction IDs and bank statements",
        "Email/message records from fraudster",
        "Your registered mobile number proof",
        "Cybercrime portal complaint number",
        "Device details (phone/laptop used)",
    ],
    "labour": [
        "Appointment letter / offer letter",
        "Salary slips (last 3 months)",
        "Employment contract",
        "Communication with HR / manager",
        "Attendance records",
        "Bank account statements showing salary credits",
        "Termination letter (if applicable)",
    ],
    "property": [
        "Builder-buyer agreement / sale deed",
        "Payment receipts to builder",
        "All correspondence with builder",
        "Original advertisement / brochure",
        "Occupancy certificate (if any)",
        "RERA registration number of project",
        "Bank loan documents (if applicable)",
    ],
    "family": [
        "Marriage certificate",
        "Identity proof of both parties",
        "Any written communication",
        "Medical reports (if domestic violence)",
        "Witness statements",
        "Financial documents if alimony involved",
    ],
    "civil": [
        "All relevant contracts / agreements",
        "Communication records",
        "Payment proofs",
        "Identity documents",
        "Property documents (if applicable)",
        "Witness details",
    ],
}


# ─────────────────────────────────────────────
# Jurisdiction Mapping
# ─────────────────────────────────────────────

JURISDICTION_MAP: Dict[str, Dict[str, Any]] = {
    "criminal": {
        "primary":    "local_police",
        "secondary":  "district_court",
        "escalation": "high_court",
        "note": "File FIR at nearest police station. If police refuses, approach Magistrate directly.",
    },
    "consumer": {
        "under_1cr":  "consumer_district_forum",
        "1cr_to_10cr": "state_consumer_commission",
        "above_10cr": "national_consumer_commission",
        "note": "Claim amount determines which forum. District forum handles most cases.",
    },
    "cyber": {
        "primary":    "cyber_cell",
        "online":     "cybercrime.gov.in",
        "escalation": "district_court",
        "note": "File complaint at cybercrime.gov.in immediately. Also report to local cyber cell.",
    },
    "labour": {
        "harassment": "internal_complaints_committee",
        "wages":      "labour_court",
        "escalation": "high_court",
        "note": "For POSH: Internal Complaints Committee first. If no ICC, approach Local Complaints Committee.",
    },
    "property": {
        "primary":    "rera_authority",
        "escalation": "high_court",
        "note": "RERA complaints are faster and cheaper than civil courts. File online on state RERA portal.",
    },
    "civil": {
        "primary":    "district_court",
        "escalation": "high_court",
        "note": "Civil suit requires vakalatnama. Consider mediation first — faster and cheaper.",
    },
}


# ─────────────────────────────────────────────
# Limitation Periods (Statute of Limitations)
# ─────────────────────────────────────────────

LIMITATION_PERIODS: Dict[str, Dict[str, Any]] = {
    "criminal":  {"days": None,  "note": "No strict limitation for FIR, but act ASAP for evidence"},
    "consumer":  {"days": 730,   "note": "2 years from date of cause of action"},
    "cyber":     {"days": None,  "note": "File immediately — digital evidence degrades fast"},
    "labour":    {"days": 365,   "note": "1 year from date of grievance"},
    "property":  {"days": 1825,  "note": "5 years for RERA complaint from possession date"},
    "civil":     {"days": 1095,  "note": "3 years limitation under Limitation Act 1963"},
    "family":    {"days": None,  "note": "Varies by type — consult lawyer"},
}
