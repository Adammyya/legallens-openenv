# \---

# title: LegalLens OpenEnv

# emoji: ⚖️

# colorFrom: blue

# colorTo: green

# sdk: docker

# pinned: false

# license: mit

# tags:

# &#x20; - openenv

# &#x20; - legal

# &#x20; - india

# \---

# 

# ⚖️ LegalLens AI — Indian Legal Problem Analyzer

> \*"Apni baat batao — hum batayenge ki kanoon mein kya hua tumhare saath, aur aage kya karna hai."\*

[!\[OpenEnv](https://img.shields.io/badge/OpenEnv-compliant-green)](https://openenv.ai)
[!\[HuggingFace](https://img.shields.io/badge/🤗-Spaces-yellow)](https://huggingface.co/spaces)
[!\[Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[!\[Docker](https://img.shields.io/badge/docker-ready-blue)](https://docker.com)

\---

## 🎯 Problem \& Motivation

In India, over **800 million people** have no meaningful access to legal guidance.

When something wrong happens to a common person:

```
❌ Can't afford a lawyer (₹2000–5000 for first consultation)
❌ Doesn't know which law applies
❌ Doesn't know which court to approach  
❌ Police says "civil matter" — court says "file FIR first"
❌ Result: injustice continues
```

**LegalLens AI bridges this gap.**

It acts as an AI legal analyst that:

1. **Listens** to the problem in plain language
2. **Identifies** the exact violated laws and sections
3. **Recommends** the correct legal action and forum
4. **Guides** on evidence collection and deadlines

\---

## 🏗️ Environment Design

```
┌─────────────────────────────────────────────────────┐
│                   LegalLensEnv                      │
│                                                     │
│  Appellant Problem Statement (plain text)           │
│         ↓                                           │
│  ┌──────────────┐   step(action)   ┌─────────────┐ │
│  │  AI Agent    │ ───────────────▶ │ Environment │ │
│  │ (LLM + Rules)│                  │ - Laws DB   │ │
│  │              │ ◀─────────────── │ - Grader    │ │
│  └──────────────┘  obs, reward,    │ - Simulator │ │
│                    done, info      └─────────────┘ │
│                                                     │
│  Final Output: Law Analysis Report                  │
└─────────────────────────────────────────────────────┘
```

### Analysis Steps (Agent Actions)

|Step|Action|What happens|
|-|-|-|
|1|`classify\_domain`|Criminal? Consumer? Cyber? Labour?|
|2|`identify\_law`|IPC 420? IT Act 66D? RERA S.18?|
|3|`rank\_violation`|Which law is strongest for this case?|
|4|`recommend\_action`|File FIR? Consumer Forum? RERA?|
|5|`find\_jurisdiction`|Which court / authority / portal?|
|6|`list\_evidence`|What documents to collect?|
|7|`check\_limitation`|Is filing deadline still alive?|

\---

## 📁 Project Structure

```
legallens/
├── environment.py              # Core step/reset/state
├── models.py                   # Pydantic: Observation, Action, Reward
├── grader.py                   # Deterministic scoring logic
├── app.py                      # FastAPI REST server
├── baseline\_agent.py           # GPT-4o baseline script
├── openenv.yaml                # Environment metadata
├── requirements.txt
├── Dockerfile
├── README.md
├── laws/
│   ├── \_\_init\_\_.py
│   └── knowledge\_base.py       # IPC, IT Act, Consumer Act, RERA, POSH...
└── tasks/
    ├── \_\_init\_\_.py
    └── task\_definitions.py     # 3 tasks with gold standard answers
```

\---

## 🎯 Three Tasks

### 🟢 Task 1 — Easy: Online Shopping Fraud

**Appellant says:**

> \*"Maine ek website se ₹15,000 ka mobile order kiya. UPI se payment ki. 3 hafte baad na phone aaya na refund. Website band ho gayi."\*

**Agent must identify:**

* IT Act 66D (online cheating) — PRIMARY
* IPC 420 (cheating/fraud)
* Consumer Protection Act 2019
* **Action:** cybercrime.gov.in + Consumer Forum
* **Baseline score: 0.78**

\---

### 🟡 Task 2 — Medium: Workplace Harassment + Salary Issue

**Appellant says:**

> \*"Mera boss inappropriate comments karta hai. HR ne complaint ignore ki. Ab manager ne salary rok li aur job jaane ki dhamki de raha hai."\*

**Agent must identify:**

* POSH Act S.3 (workplace sexual harassment) — PRIMARY
* Payment of Wages Act S.15 (salary withheld)
* IPC 506 (criminal intimidation)
* **Action:** ICC complaint + Labour Court
* **Challenge:** Two separate legal issues in one complaint
* **Baseline score: 0.63**

\---

### 🔴 Task 3 — Hard: Builder Fraud + Counter Legal Notice

**Appellant says:**

> \*"₹45 lakh ka flat book kiya 2019 mein. 3 saal baad bhi possession nahi. Agreement mein hidden clause tha. Complaint ki toh builder ne defamation notice bheja."\*

**Agent must identify:**

* RERA S.18 (possession delay) — PRIMARY
* RERA S.12 (misrepresentation in agreement)
* IPC 420 + IPC 406 (criminal fraud)
* Consumer Protection Act (parallel forum)
* IPC 500 (counter — builder's defamation threat is weak)
* **Action:** RERA complaint + Consumer Forum + Criminal FIR
* **Challenge:** Counter notice handling + multiple forums + priority order
* **Baseline score: 0.51**

\---

## 🧮 Reward Function

### Per Step

```
R\_step = domain\_r + law\_r + action\_r + jurisdiction\_r + evidence\_r + penalty\_r
```

### Episode Score (0.0 – 1.0)

```
Score = 0.20 × domain\_accuracy
      + 0.35 × law\_identification    ← highest weight (core task)
      + 0.25 × action\_correctness
      + 0.10 × jurisdiction\_match
      + 0.10 × evidence\_quality
      - 0.08 × (wrong laws identified)
      + 0.05 × efficiency\_bonus
```

### Why Law Identification Gets 35%?

Because correctly identifying the applicable law is the hardest and most valuable part. Getting IPC 420 right when IT Act 66D applies is a legal error — the agent must be precise.

\---

## 🚀 Setup \& Usage

### Local

```bash
git clone https://huggingface.co/spaces/your-username/legallens
cd legallens
pip install -r requirements.txt
python app.py
# → http://localhost:7860
```

### Docker

```bash
docker build -t legallens .
docker run -p 7860:7860 -e OPENAI\_API\_KEY=sk-... legallens
curl http://localhost:7860/health
```

### Python API

```python
from environment import LegalLensEnv
from models import Action, ActionType, LegalDomain, LegalAction, LawReference, Jurisdiction

env = LegalLensEnv(task\_id="task\_1\_easy")
obs = env.reset()

# Step 1: Classify domain
action = Action(
    action\_type=ActionType.CLASSIFY\_DOMAIN,
    problem\_id="PROB\_001",
    domain=LegalDomain.CYBER,
    reasoning="Payment made online, product not received, website fake — cyber fraud"
)
obs, reward, done, info = env.step(action)

# Step 2: Identify laws
action = Action(
    action\_type=ActionType.IDENTIFY\_LAW,
    problem\_id="PROB\_001",
    laws=\[
        LawReference(act="Information Technology Act 2000", section="66D",
                     description="Online cheating via computer resource",
                     punishment="3 years + ₹1 lakh fine", strength=0.92),
        LawReference(act="Indian Penal Code", section="420",
                     description="Cheating and dishonest delivery of property",
                     punishment="7 years + fine", strength=0.88),
    ],
    reasoning="Fake website + UPI fraud = IT Act 66D primary, IPC 420 secondary"
)
obs, reward, done, info = env.step(action)

# Step 3: Recommend action
action = Action(
    action\_type=ActionType.RECOMMEND\_ACTION,
    problem\_id="PROB\_001",
    legal\_action=LegalAction.CYBER\_PORTAL,
    reasoning="Immediate cybercrime.gov.in complaint — preserves digital evidence"
)
obs, reward, done, info = env.step(action)

# Step 4: List evidence
action = Action(
    action\_type=ActionType.LIST\_EVIDENCE,
    problem\_id="PROB\_001",
    evidence\_items=\[
        "UPI transaction screenshot",
        "Order confirmation email/SMS",
        "Website URL and screenshots",
        "Bank statement showing debit",
    ],
    reasoning="Digital evidence critical for cyber fraud cases"
)
obs, reward, done, info = env.step(action)

print(f"Score: {info.get('final\_score', 'N/A')}")
```

### REST API

```bash
# Reset (start new case)
curl -X POST http://localhost:7860/reset \\
  -H "Content-Type: application/json" \\
  -d '{"task\_id": "task\_1\_easy"}'

# Step
curl -X POST http://localhost:7860/step \\
  -H "Content-Type: application/json" \\
  -d '{
    "session\_id": "YOUR\_SESSION\_ID",
    "action\_type": "classify\_domain",
    "problem\_id": "PROB\_001",
    "domain": "cyber",
    "reasoning": "Online fraud case"
  }'
```

### Baseline Agent

```bash
export OPENAI\_API\_KEY=sk-...
python baseline\_agent.py --model gpt-4o
# Results saved to baseline\_results.json
```

\---

## 📊 Baseline Results

|Task|Difficulty|Steps|Score|
|-|-|-|-|
|Online Shopping Fraud|Easy|8/12|**0.78**|
|Workplace Harassment|Medium|15/18|**0.63**|
|Builder Fraud|Hard|22/25|**0.51**|

\---

## ⚖️ Laws Covered

|Act|Sections|Domain|
|-|-|-|
|Indian Penal Code|354, 384, 406, 420, 498A, 500, 506|Criminal|
|Consumer Protection Act 2019|Deficiency, Unfair Trade, Product Liability|Consumer|
|IT Act 2000|66, 66C, 66D, 67|Cyber|
|POSH Act 2013|Section 3|Labour|
|Payment of Wages Act 1936|Section 15|Labour|
|RERA 2016|Section 12, 18|Property|

\---

## 🤗 HuggingFace Deployment

1. Create new Space → SDK: **Docker**
2. Push this repo
3. Add secret: `OPENAI\_API\_KEY`
4. Space auto-deploys at `https://username-legallens.hf.space`

\---

## ⚠️ Disclaimer

LegalLens AI provides **informational analysis only**.
It does not constitute legal advice.
Always consult a qualified lawyer for your specific situation.

\---

*Built for OpenEnv × Scaler Hackathon — Making justice accessible. ⚖️*

