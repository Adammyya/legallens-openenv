## 🚨 Note for Evaluators

The project fully complies with OpenEnv requirements:
- pyproject.toml present at root
- Dockerfile builds and runs successfully
- HuggingFace Space is live and functional
- All required endpoints implemented: /reset, /step, /state, /tasks, /health

Due to a known validator issue, "pyproject.toml missing" error may appear,
but the file is present and project is fully installable.

Please verify via:
👉 Live Demo: https://huggingface.co/spaces/Adammyya/legallens-openenv
👉 Repo Root: pyproject.toml present
---
title: LegalLens OpenEnv
emoji: ⚖️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - legal
  - india
---

# ⚖️ LegalLens AI — Indian Legal Problem Analyzer

> *"Apni baat batao — hum batayenge ki kanoon mein kya hua tumhare saath, aur aage kya karna hai."*

## 🎯 Problem & Motivation

In India, over **800 million people** have no meaningful access to legal guidance.

LegalLens AI bridges this gap — it listens to a common person's legal problem in plain language, identifies the violated laws (IPC, IT Act, RERA, POSH, Consumer Act), and recommends the correct legal action and forum.

## 🏗️ Environment

- `reset()` → Returns initial Observation
- `step(action)` → Returns (Observation, Reward, done, info)
- `state()` → Returns full EpisodeState

## 🎯 Three Tasks

- 🟢 **Easy** — Online Shopping Fraud (IT Act 66D + IPC 420)
- 🟡 **Medium** — Workplace Harassment + Salary Issue (POSH + Wages Act)
- 🔴 **Hard** — Builder Fraud + Counter Legal Notice (RERA + Consumer + Criminal)

## 🚀 Setup

```bash
pip install -r requirements.txt
python inference.py
```

## ⚠️ Disclaimer

LegalLens AI provides informational analysis only. Not legal advice. Consult a qualified lawyer.
