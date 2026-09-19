# KushBitx no-pay agent integration

AI-agent integration for the KushBitx bounty using the published `@kushbitx/sdk`.

The agent has exactly three tools:

- token preview
- SpendGuard evaluation
- unsigned x402 challenge discovery

It has **no signing, payment, recovery, private-key, or policy-mutation tool**. SpendGuard is treated as an advisory policy evaluation; transaction enforcement belongs to a separate signing/execution layer.

## Agent runtime

`src/agent.py` is a small local ML agent. A scikit-learn text classifier is trained at startup and chooses the next tool from the mission plus observations of completed work. Tool execution crosses a Node bridge into `@kushbitx/sdk`; the Python agent does not call KushBitx HTTP endpoints directly.

This is intentionally local and keyless: no OpenAI/API credential is required to reproduce the agent-directed run.

## Setup

Requirements: Node.js 22+ and Python 3.11+.

```bash
npm install
python3 -m pip install -r requirements.txt
```

## Test

```bash
npm test
```

The suite covers the three tools, invalid input, upstream errors, unexpected/missing HTTP 402 challenges, output redaction, the no-sign/no-pay boundary, the ML planner, and a complete agent-directed run against a local fake KushBitx service.

## Live free-path run

```bash
python3 src/agent.py --evidence evidence/run-output.txt
```

The default mission asks the agent to preview Base USDC, run a 1.00 USDC SpendGuard evaluation, discover the `token-risk` x402 challenge, and stop. The evidence file is sanitized: payment addresses and request identifiers are redacted, and the raw payment header is never printed.

No paid request is made. A successful run ends with `signed: false` and `paid: false`.

## Acceptance-criteria map

| Requirement | Implementation |
| --- | --- |
| Published SDK | exact `@kushbitx/sdk` 0.1.0 dependency |
| AI agent runtime | local learned classifier planner in `src/agent.py` |
| Free token preview | `kushbitx_preview_token` |
| SpendGuard evaluation | `kushbitx_evaluate_spend` |
| Unsigned x402 discovery | `kushbitx_discover_x402` |
| No private key | bridge exposes no signing/payment/recovery tool |
| Reproducible tests | `npm test` |
| Sanitized evidence | `evidence/run-output.txt` |
