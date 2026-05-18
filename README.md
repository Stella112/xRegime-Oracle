# ♾️ xRegime Oracle
**Self-Evolving Enterprise Trading Agent for the AI Agent Olympics**

## One-Line Pitch

> xRegime Oracle is a self-evolving enterprise trading agent that converts earnings calls, executive briefings, and market text into risk-gated xStock trades through Kraken CLI, using Speechmatics transcription, Featherless ensemble voting, and a dynamic Regime Score that adapts its risk rules nightly.

---

## Core Design Philosophy

xRegime Oracle is designed to dominate three major hackathon tracks — **Featherless AI**, **Speechmatics Voice AI**, and **Kraken** — by treating each as a first-class integration, not a bolt-on.

The agent is **real-execution capable, safety-first**. It runs in Kraken paper/sandbox mode for demo safety, but the same execution layer supports real Kraken CLI trading when live mode is enabled with capped notional size, no-withdrawal API keys, and circuit breakers.

---

## Architecture & Core Features

### 1. Enterprise Audio Ingestion (Speechmatics)
xRegime Oracle is built around **earnings-call and executive-briefing ingestion** — not generic audio upload.

- Upload or record a `.wav`/`.mp3` earnings call, investor briefing, or analyst note directly in the dashboard.
- The audio is sent to the **Speechmatics Batch Transcription API** for high-accuracy financial speech recognition.
- The resulting transcript is fed directly into the financial reasoning engine.

This is designed to simulate the way real trading desks process live earnings calls, not just text inputs.

### 2. Featherless Configurable Ensemble (Open-Source)
Transcribed text goes through a **configurable three-model Featherless ensemble**, defaulting to Llama, Qwen, and Mixtral-class open-source models.

Each model independently votes `BUY`, `SELL`, or `HOLD` based on the extracted signals and the agent's current active risk rules. A **majority consensus of 2/3 models** is required before any trade is triggered — significantly reducing hallucination-driven errors.

### 3. Kraken CLI Execution Layer
Once the ensemble reaches a consensus, xRegime Oracle directly invokes the **official Kraken CLI binary** via system subprocess — no REST API wrapper, no middleware.

- **Demo mode**: runs in Kraken's native paper/sandbox environment (`kraken paper buy ...`) for safe demonstration.
- **Live mode** (when enabled): the same execution layer supports real Kraken CLI trading with capped notional size, no-withdrawal API key restrictions, and PnL circuit breakers.

### 4. Dynamic Regime Score (Self-Adapting Risk Posture)

This is the core originality of xRegime Oracle: it is a **self-evolving agent that adapts its own risk posture based on recent logged trade outcomes**.

- Every executed trade is logged with its PnL outcome.
- The **Regime Score** (0–100) is recalculated from recent trade history — a high score means recent strategy is working; a low score means it's failing.
- A secondary LangGraph workflow (**Nightly Reflector**) runs `Qwen2-72B-Instruct` against the trade log and current Regime Score to propose updated risk parameters.
- These are written back to `dynamic_config.json`, which is loaded at the start of every new trade cycle.

> The agent does not "learn" in the machine learning sense — it **adapts risk rules based on logged outcomes**. No retraining, no model updates. Just dynamic JSON config evolution driven by reasoning.

### 5. Human-in-the-Loop Controls (Enterprise Grade)
High-confidence ensemble votes (`≥ 0.75` average confidence) execute automatically. Borderline trades require **one-click approval** in the dashboard — a critical feature for enterprise adoption and judge credibility.

---

## Execution Workflows (LangGraph)

**Workflow A: Live Execution Loop**
```
Ingest Audio/Text
  → Speechmatics Transcription
  → Featherless Signal Extraction (Qwen-7B)
  → 3-Model Ensemble Vote (parallel)
  → Backtest / Circuit Breaker Check
  → Kraken CLI Execution (paper or live)
  → Log Trade + Update Regime Score
```

**Workflow B: Nightly Regime Reflector**
```
Calculate Current Regime Score
  → Reflect with Qwen2-72B
  → Propose JSON Rule Changes
  → Overwrite dynamic_config.json
  → New rules loaded on next Workflow A cycle
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph, LangChain |
| UI / Dashboard | Streamlit |
| AI Ensemble | Featherless API (Llama, Qwen2, Mixtral-class) |
| Voice / Audio | Speechmatics Batch Transcription API |
| Trading Execution | Kraken CLI (official Rust binary) |
| Infrastructure | Vultr VPS (Ubuntu) |

---

## Environment Variables

```bash
FEATHERLESS_API_KEY=...       # Required — powers the ensemble
SPEECHMATICS_API_KEY=...      # Required — earnings call transcription
KRAKEN_API_KEY=...            # Optional — for live trading (paper mode default)
KRAKEN_API_SECRET=...         # Optional — for live trading (paper mode default)
```
