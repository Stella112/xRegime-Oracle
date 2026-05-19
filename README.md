# xRegime Oracle

## Autonomous Voice-to-Trade xStock Agent

xRegime Oracle is a voice-first autonomous trading agent built for tokenized equities and xStocks. It converts spoken or written market briefs into transparent, risk-gated trading decisions using Speechmatics transcription, a Featherless multi-model finance ensemble, a dynamic Regime Score, Kraken CLI execution, and a visible security layer.

The live demo currently executes Kraken crypto paper trades because Kraken paper mode did not support the xStock pairs we tested. Crypto is the paper-execution fallback; xStocks remain the product thesis.

## The Problem

Trading agents are powerful, but most of them fail the trust test.

They often:

- Act like black boxes.
- Give trade recommendations without showing why.
- Depend on one model response.
- Mix analysis and execution without clear guardrails.
- Hide risk decisions from the user.
- Have no clear audit trail after a trade.

For a financial agent, that is not enough. Users and judges need to see what the agent heard, what it believed, how confident it was, what risk rules were applied, and exactly what command was sent or blocked.

## The Solution

xRegime Oracle turns the xStock trading-agent workflow into a transparent cockpit.

The user gives a market brief by text or voice upload. The agent transcribes the input, extracts trading signals, sends the signal through a multi-model courtroom, checks dynamic risk rules, passes through visible security guardrails, and only then prepares execution.

In the intended production path, this execution layer targets Kraken xStocks/tokenized equities. In the current paper demo, the same execution pattern is demonstrated with supported Kraken crypto pairs because xStocks were unavailable in paper mode.

Every run creates a proof trail:

```text
Input
-> Signal Extraction
-> Model Courtroom
-> Regime Risk Judge
-> Security Layer
-> Kraken Paper Execution
-> Proof Trail + Portfolio Ledger
```

The result is not just "BUY" or "SELL." It is a complete explanation of the agent's decision.

## One-Line Pitch

xRegime Oracle is a self-evolving, voice-first xStock trading agent that makes AI trading decisions auditable from transcript to Kraken execution.

## Why This Wins

xRegime Oracle is built around four judge-friendly ideas:

1. **Real execution layer**
   The agent does not stop at advice. Approved trades pass into a Kraken CLI execution layer, with visible commands and PnL tracking. The demo uses crypto paper pairs because xStocks did not work in Kraken paper mode.

2. **Voice-first interaction**
   Users can upload spoken market briefs. Speechmatics transcribes the audio and sends it directly into the trading workflow.

3. **Domain-specialized intelligence**
   A Featherless-hosted finance ensemble votes independently before a trade can continue.

4. **Self-improvement loop**
   A dynamic Regime Score and Nightly Reflector update the agent's risk posture based on recent outcomes.

## Current Product Experience

The dashboard is organized into five simple numbered views.

### 1. Trade

The main cockpit.

- Paste an xStock, equity, or crypto market brief.
- Load a BTC sample.
- Upload a voice file for Speechmatics transcription.
- See the live verdict in plain English.
- View front-page Regime Score, Paper PnL, trade count, and win rate.

Live browser microphone support requires HTTPS on a public IP. Until HTTPS is enabled, voice upload is the reliable voice path.

### 2. Proof

The audit trail.

Shows:

- Input captured
- Signals extracted
- Model votes and confidence
- Final consensus
- Risk judge verdict
- Kraken command or `NO_ACTION`

This page answers the most important question: "Why did the agent do that?"

### 3. Portfolio

The paper performance view.

Shows:

- Regime Score
- Win rate
- Trade count
- Latest PnL
- Equity curve
- Recent trade ledger

### 4. Security

The visible safety layer.

Shows:

- Paper trading only
- Crypto asset allowlist
- Tiny preset order sizes
- Model consensus gate
- Regime risk gate
- Replayable audit trail

This page makes the guardrails obvious before users or judges ask about them.

### 5. System

The operating panel.

Shows:

- Nightly Reflector control
- Agent identity
- Active dynamic risk rules

## Supported Markets and Demo Fallback

xRegime Oracle was designed around xStocks/tokenized equity trading. During testing, Kraken CLI paper mode did not accept the xStock pairs, so the live demo uses supported Kraken crypto paper markets to prove the execution layer safely.

Demo execution allowlist:

```text
BTC, ETH, SOL, XRP, ADA, DOGE, LTC, DOT, AVAX, LINK
```

This means:

- **Product thesis:** autonomous xStock/tokenized equity agent.
- **Live paper demo:** crypto pairs, because they work reliably in Kraken paper mode.
- **Execution layer:** same Kraken CLI pattern, visible command, PnL tracking, and proof trail.

## Execution Layer

Approved demo trades are executed through Kraken CLI in paper mode.

Example:

```bash
/root/.cargo/bin/kraken paper buy BTC/USD 0.0001
```

The exact command is shown in the Proof view. If the model vote or risk rules block the trade, the command becomes `NO_ACTION`.

## Security and Safety Layer

xRegime Oracle is designed to make safety visible.

Current visible guardrails:

- Paper trading mode only
- Supported demo pair allowlist
- Tiny preset order sizes
- Multi-model consensus required
- Regime risk gate can block trades
- Full proof trail for every decision

Recommended backend hardening:

- Reject any non-paper Kraken command before subprocess execution.
- Block prompt-injection phrases like "ignore rules" or "trade live."
- Enforce a trade cooldown, for example one trade every five minutes.
- Require user confirmation before execution.
- Log every blocked command to an audit file.

## Dynamic Regime Score

The Regime Score is the agent's adaptive risk posture.

- High score: recent outcomes are stronger, so the agent can accept more risk.
- Low score: recent outcomes are weaker, so the agent becomes more conservative.

The score is recalculated from recent trade outcomes and displayed on the front page and Portfolio view.

## Nightly Reflector

The Nightly Reflector is the self-improvement loop.

It reviews:

- Recent trades
- Current Regime Score
- Active dynamic rules

Then it proposes updates to `agent/dynamic_config.json`.

The agent does not retrain models. Instead, it evolves its risk rules based on observed outcomes.

## Sponsor Alignment

| Sponsor / Track | How xRegime Oracle Uses It |
| --- | --- |
| Featherless AI | Multi-model finance ensemble, signal extraction, and Nightly Reflector |
| Speechmatics | Voice upload transcription for spoken market briefs |
| Kraken | CLI-based xStock execution thesis, demonstrated with crypto paper trading fallback |
| Base / Ethereum | Agent wallet identity and ERC-8004-style profile |

## Contracts / Onchain Identity

xRegime Oracle includes an agent identity layer in:

```text
agent/erc8004_identity.json
agent/wallet.py
```

This identity profile represents the agent's wallet address, capabilities, model ensemble, and reputation source.

Current state:

- The app generates and stores an agent wallet identity.
- The dashboard links the identity to Basescan.
- The identity is structured around the ERC-8004 Trustless Agents concept.

Important note:

This repository currently does not include a deployed Solidity smart contract. The onchain component is an identity/profile layer, not a full contract system. A future version can add a registry contract for agent reputation, decision hashes, and audit proofs.

## Architecture

```text
Frontend
  static/index.html
  Numbered dashboard views: Trade, Proof, Portfolio, Security, System

Backend
  api.py
  FastAPI routes for state, execution, transcription, and reflection

Agent Core
  agent/workflow.py
  LangGraph trading and reflection workflows

Tools
  agent/tools.py
  Featherless, Speechmatics, Kraken CLI, config, and execution helpers

State
  agent/state.py
  Shared agent state schema

Prompts
  agent/prompts.py
  Signal extraction, model voting, and reflection prompts

Identity
  agent/wallet.py
  agent/erc8004_identity.json
```

## Technical Workflow

```text
1. User submits text or audio
2. Audio is transcribed with Speechmatics
3. Featherless extracts tickers, sentiment, and summary
4. Three Featherless models vote BUY / SELL / HOLD
5. Consensus is calculated
6. Risk judge checks Regime Score and dynamic config
7. Security layer communicates guardrails
8. Kraken CLI command executes or is blocked
9. Proof trail and portfolio state update
10. Nightly Reflector can evolve risk rules
```

## Demo Flow

1. Open the app.
2. Start on `1 Trade`.
3. Load the BTC sample or upload a voice file.
4. Click `Analyze and Execute`.
5. Move to `2 Proof` to show the full decision path.
6. Open `3 Portfolio` to show PnL and ledger.
7. Open `4 Security` to show guardrails.
8. Open `5 System` to show identity and dynamic rules.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI |
| Agent workflow | LangGraph |
| Frontend | Static HTML, CSS, JavaScript |
| Charts | Chart.js |
| AI reasoning | Featherless API |
| Voice transcription | Speechmatics API |
| Trading execution | Kraken CLI |
| Identity | Ethereum wallet / ERC-8004-style profile |

## Project Structure

```text
xRegime-Oracle/
|-- api.py
|-- static/
|   `-- index.html
|-- app.py
|-- agent/
|   |-- workflow.py
|   |-- state.py
|   |-- tools.py
|   |-- prompts.py
|   |-- wallet.py
|   |-- dynamic_config.json
|   `-- erc8004_identity.json
|-- requirements.txt
|-- Dockerfile
`-- docker-compose.yml
```

## Environment Variables

Create a `.env` file:

```bash
FEATHERLESS_API_KEY=...
SPEECHMATICS_API_KEY=...
KRAKEN_API_KEY=...
KRAKEN_API_SECRET=...
```

`FEATHERLESS_API_KEY` and `SPEECHMATICS_API_KEY` are required for the full demo. Kraken credentials are optional for paper/demo operation depending on local Kraken CLI setup.

## Running Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI app:

```bash
uvicorn api:app --host 0.0.0.0 --port 8501
```

Open:

```text
http://127.0.0.1:8501
```

## Recent Changes

- Rebuilt the live UI as a FastAPI plus static dashboard.
- Added numbered app navigation: Trade, Proof, Portfolio, Security, System.
- Added front-page Regime Score, Paper PnL, trade count, and win rate.
- Added a dedicated Security page for visible guardrails.
- Kept the xStock product thesis while switching the live paper demo to supported Kraken crypto pairs because xStocks did not work in paper mode.
- Added tiny preset Kraken paper order sizes.
- Added Speechmatics voice upload flow.
- Added clear HTTPS notice for live microphone recording.
- Improved proof trail and portfolio ledger.
- Improved Featherless retry handling for concurrency and rate-limit errors.
- Updated README into a full project pitch.

## Roadmap

- Add HTTPS so browser live microphone recording works on the public deployment.
- Restore xStock execution when Kraken paper/live support is available for the desired xStock pairs.
- Add a backend hard safety gate before Kraken subprocess execution.
- Add trade confirmation before paper execution.
- Add cooldown and rate limiting.
- Add prompt-injection detection.
- Add onchain decision hash registry.
- Add downloadable audit reports.

## Closing Pitch

xRegime Oracle is not a generic chatbot and not a simple trading dashboard.

It is a full autonomous trading-agent cockpit: voice input, model consensus, adaptive risk, paper execution, proof trail, security layer, and portfolio tracking in one flow.

The goal is simple: make AI trading decisions understandable enough to trust and structured enough to audit.
