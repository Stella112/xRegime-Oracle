# xRegime Oracle

Autonomous crypto trading agent for the AI Agent Olympics.

xRegime Oracle turns a written or spoken crypto market brief into a transparent Kraken paper-trading decision. It uses Speechmatics for voice transcription, a Featherless multi-model finance ensemble for reasoning, a dynamic Regime Score for adaptive risk control, and a replayable proof trail for every decision.

## What It Does

xRegime Oracle is designed as a voice-first, safety-first trading agent:

1. The user enters a crypto market update by text, sample prompt, or uploaded audio.
2. Speechmatics transcribes uploaded voice notes into text.
3. Featherless models extract market signals and vote independently.
4. A risk judge checks confidence, Regime Score, and active rules.
5. Approved trades execute through Kraken CLI paper trading.
6. Every step is displayed in a forensic proof trail.
7. The Nightly Reflector can update risk rules based on recent outcomes.

The app currently supports Kraken crypto paper pairs:

`BTC`, `ETH`, `SOL`, `XRP`, `ADA`, `DOGE`, `LTC`, `DOT`, `AVAX`, `LINK`

## Core Workflow

```text
Text / Voice Input
  -> Speechmatics Transcription
  -> Signal Extraction
  -> Featherless 3-Model Courtroom
  -> Regime Risk Judge
  -> Security / Safety Guardrails
  -> Kraken CLI Paper Execution
  -> Proof Trail + Portfolio Ledger
```

## Current Dashboard

The live dashboard has been reorganized into simple numbered views:

### 1. Trade

Main user entry point.

- Load BTC sample
- Paste a crypto market brief
- Upload a voice file for Speechmatics transcription
- View front-page Regime Score, Paper PnL, trade count, and win rate
- See a plain-English live verdict

Live microphone recording is prepared in the UI, but browsers block `getUserMedia` on public HTTP IP addresses. Until HTTPS is enabled, voice upload is the reliable voice path.

### 2. Proof

Replayable decision timeline.

- Input captured
- Signals extracted
- Model votes and confidence
- Consensus result
- Risk judge verdict
- Kraken command or `NO_ACTION`

This is the audit view that explains exactly why the agent traded or refused to trade.

### 3. Portfolio

Paper trading performance view.

- Regime Score
- Win rate
- Trade count
- Latest PnL
- Equity chart
- Recent trade ledger

### 4. Security

Visible safety layer for trading-agent trust.

- Paper trading only
- Crypto asset allowlist
- Tiny preset paper order sizes
- Model consensus gate
- Regime risk gate
- Replayable audit trail

Recommended next backend upgrade: add a hard execution safety gate that rejects non-paper Kraken commands, unsupported pairs, prompt-injection phrases, and trades inside a cooldown window.

### 5. System

Operational controls and identity.

- Run Nightly Reflector
- View ERC-8004-style wallet identity
- Inspect active dynamic risk rules

## Sponsor Alignment

| Sponsor / Track | Implementation |
| --- | --- |
| Featherless AI | Multi-model finance ensemble and Nightly Reflector |
| Speechmatics | Voice upload transcription into trading workflow |
| Kraken | CLI-based paper execution layer |
| Base / Ethereum | Agent wallet identity and onchain-style profile |

## Key Features

### Featherless 3-Model Courtroom

The agent does not allow one model to act alone. Multiple Featherless-hosted models vote `BUY`, `SELL`, or `HOLD`, and the app displays each vote with confidence. A consensus is required before the trade reaches risk review.

### Dynamic Regime Score

The Regime Score is a 0-100 risk posture derived from recent trade outcomes. Lower scores make the agent more conservative. Higher scores allow more confidence in stronger signals.

### Nightly Reflector

The Nightly Reflector reviews recent performance and updates `agent/dynamic_config.json`. This is the self-improvement loop: the agent does not retrain models, but it adapts its risk rules based on outcomes.

### Kraken Paper Execution

Approved trades are sent through Kraken CLI in paper mode with tiny preset crypto order sizes. The exact command is shown in the proof trail.

Example:

```bash
/root/.cargo/bin/kraken paper buy BTC/USD 0.0001
```

### Voice-First Interaction

Audio uploads are transcribed by Speechmatics and automatically passed into the trading workflow. Browser live microphone support requires HTTPS on a public IP, so the current deployed version uses upload as the reliable voice path.

## Project Structure

```text
xRegime-Oracle/
├── api.py                      # FastAPI backend for state, execution, transcription, reflection
├── static/
│   └── index.html              # Production dashboard UI
├── app.py                      # Streamlit dashboard variant
├── agent/
│   ├── workflow.py             # LangGraph execution and reflection workflows
│   ├── state.py                # Shared state schema
│   ├── tools.py                # Featherless, Speechmatics, Kraken helpers
│   ├── prompts.py              # Prompt templates
│   ├── wallet.py               # Agent wallet / identity helpers
│   ├── dynamic_config.json     # Adaptive risk rules
│   └── erc8004_identity.json   # Agent identity profile
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Environment Variables

Create a `.env` file:

```bash
FEATHERLESS_API_KEY=...
SPEECHMATICS_API_KEY=...
KRAKEN_API_KEY=...
KRAKEN_API_SECRET=...
```

`FEATHERLESS_API_KEY` and `SPEECHMATICS_API_KEY` are required for full functionality. Kraken keys are only needed if configuring real Kraken access; the demo is designed around paper trading.

## Running Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI app:

```bash
uvicorn api:app --host 0.0.0.0 --port 8501
```

Then open:

```text
http://127.0.0.1:8501
```

## Recent Changes

- Rebuilt the live UI as a FastAPI + static dashboard.
- Reorganized the app into numbered views: Trade, Proof, Portfolio, Security, System.
- Added front-page Regime Score, Paper PnL, trade count, and win rate.
- Added a visible Security layer page for paper-mode and risk guardrails.
- Switched the trading surface from xStocks to supported Kraken crypto pairs.
- Added safer tiny order sizes for Kraken paper trades.
- Improved Featherless retry handling for concurrency/rate-limit errors.
- Added Speechmatics voice-upload flow.
- Added clear HTTPS notice for browser microphone recording.
- Improved proof trail and ledger readability.
- Added dynamic config normalization and safer path handling.

## Demo Summary

xRegime Oracle is not just a bot that says "BUY" or "SELL." It is an autonomous trading agent with visible reasoning, risk controls, paper execution, adaptive rules, and a clear audit trail. The goal is to make every trading decision understandable, replayable, and safe for demo use.
