#!/usr/bin/env python3
"""Small local ML agent that chooses KushBitx SDK tools and stops before payment.

The planner is a learned text classifier, not a fixed tool-call script. It receives the
mission plus compact observation state after each tool call and predicts the next action.
The execution boundary is the Node bridge backed by the published @kushbitx/sdk package.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MISSION = (
    "Inspect the Base USDC token, evaluate a 1.00 USDC agent spend with SpendGuard, "
    "then discover the token-risk x402 payment challenge. Do not sign or pay."
)

TOOL_FOR_ACTION = {
    "preview": "kushbitx_preview_token",
    "spend": "kushbitx_evaluate_spend",
    "challenge": "kushbitx_discover_x402",
}


@dataclass
class State:
    preview: bool = False
    spend: bool = False
    challenge: bool = False

    def prompt(self, mission: str) -> str:
        completed = [name for name, done in (("preview", self.preview), ("spend", self.spend), ("challenge", self.challenge)) if done]
        missing = [name for name, done in (("preview", self.preview), ("spend", self.spend), ("challenge", self.challenge)) if not done]
        return (
            f"mission: {mission}\n"
            f"completed: {' '.join(completed) or 'none'}\n"
            f"missing: {' '.join(missing) or 'none'}\n"
            "choose the next useful action"
        )


def build_planner() -> Pipeline:
    missions = [
        "inspect a token, evaluate a spend, then discover payment terms without paying",
        "check token market data and spend policy before looking at an x402 challenge",
        "preview USDC, ask SpendGuard for advice, inspect unsigned x402 terms, stop",
        "use all three safe tools and never sign a transaction",
        "run the free KushBitx agent flow and halt before payment",
    ]
    rows: list[str] = []
    labels: list[str] = []
    states = [
        ((0, 0, 0), "preview"),
        ((1, 0, 0), "spend"),
        ((1, 1, 0), "challenge"),
        ((1, 1, 1), "finish"),
    ]
    for mission in missions:
        for (p, s, c), label in states:
            rows.append(State(bool(p), bool(s), bool(c)).prompt(mission))
            labels.append(label)

    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
            ("classifier", LogisticRegression(random_state=0, max_iter=1000, C=50.0)),
        ]
    )
    model.fit(rows, labels)
    return model


def tool_args(action: str) -> dict[str, str]:
    if action == "preview":
        return {}
    if action == "spend":
        return {"amount": "1.00"}
    if action == "challenge":
        return {"service": "token-risk"}
    raise ValueError(f"no tool arguments for {action}")


def run_bridge(tool: str, args: dict[str, str], base_url: str | None = None) -> dict:
    env = os.environ.copy()
    if base_url:
        env["KUSHBITX_BASE_URL"] = base_url
    proc = subprocess.run(
        ["node", str(ROOT / "src" / "bridge.mjs"), tool, json.dumps(args)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        msg = proc.stderr.strip() or proc.stdout.strip() or f"bridge exited {proc.returncode}"
        raise RuntimeError(msg)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("bridge returned invalid JSON") from exc


def update_state(state: State, action: str) -> None:
    if action == "preview":
        state.preview = True
    elif action == "spend":
        state.spend = True
    elif action == "challenge":
        state.challenge = True


def run_agent(mission: str, base_url: str | None = None, max_steps: int = 6) -> list[dict]:
    planner = build_planner()
    state = State()
    trace: list[dict] = []

    for step in range(1, max_steps + 1):
        planner_input = state.prompt(mission)
        action = str(planner.predict([planner_input])[0])
        confidence = float(max(planner.predict_proba([planner_input])[0]))
        trace.append(
            {
                "type": "planner",
                "step": step,
                "action": action,
                "confidence": round(confidence, 4),
                "state": asdict(state),
            }
        )
        if action == "finish":
            if not (state.preview and state.spend and state.challenge):
                raise RuntimeError("planner attempted to finish before all acceptance tools succeeded")
            return trace

        tool = TOOL_FOR_ACTION.get(action)
        if not tool:
            raise RuntimeError(f"planner selected unsupported action: {action}")
        observation = run_bridge(tool, tool_args(action), base_url=base_url)
        trace.append({"type": "tool", "step": step, "tool": tool, "observation": observation})
        update_state(state, action)

    raise RuntimeError("agent exceeded step limit without finishing")


def render_trace(mission: str, trace: list[dict]) -> str:
    lines = [
        "KushBitx local ML agent run",
        f"mission: {mission}",
        "",
    ]
    for event in trace:
        if event["type"] == "planner":
            lines.append(
                f"planner step {event['step']}: {event['action']} "
                f"(confidence={event['confidence']}, state={json.dumps(event['state'], sort_keys=True)})"
            )
        else:
            obs = event["observation"]
            summary = {
                "ok": obs.get("ok"),
                "advisory": obs.get("advisory"),
                "executionAuthorizedByThisTool": obs.get("executionAuthorizedByThisTool"),
                "stoppedAtPaymentChallenge": obs.get("stoppedAtPaymentChallenge"),
                "signed": obs.get("signed"),
                "paid": obs.get("paid"),
                "paymentHeaderPresent": obs.get("paymentHeaderPresent"),
                "challenge": obs.get("challenge"),
            }
            summary = {k: v for k, v in summary.items() if v is not None}
            lines.append(f"tool: {event['tool']} -> {json.dumps(summary, sort_keys=True)}")
    lines.extend(
        [
            "",
            "boundary: no private key requested or stored; no signing or payment tool exists.",
            "boundary: SpendGuard is advisory evaluation; enforcement belongs to the signing/execution layer.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", default=DEFAULT_MISSION)
    parser.add_argument("--base-url", default=os.environ.get("KUSHBITX_BASE_URL"))
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args()

    try:
        trace = run_agent(args.mission, base_url=args.base_url)
        rendered = render_trace(args.mission, trace)
    except Exception as exc:  # CLI boundary
        print(f"agent failed: {exc}", file=sys.stderr)
        return 1

    print(rendered, end="")
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
