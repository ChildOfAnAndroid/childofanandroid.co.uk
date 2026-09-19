import unittest
from unittest.mock import patch

from src.agent import DEFAULT_MISSION, State, build_planner, render_trace, run_agent


class AgentPlannerTests(unittest.TestCase):
    def test_planner_progression_is_learned_and_state_sensitive(self):
        planner = build_planner()
        expected = [
            (State(), "preview"),
            (State(preview=True), "spend"),
            (State(preview=True, spend=True), "challenge"),
            (State(preview=True, spend=True, challenge=True), "finish"),
        ]
        for state, action in expected:
            self.assertEqual(planner.predict([state.prompt(DEFAULT_MISSION)])[0], action)

    @patch("src.agent.run_bridge")
    def test_agent_finishes_only_after_three_successful_tool_observations(self, run_bridge):
        run_bridge.side_effect = [
            {"tool": "kushbitx_preview_token", "ok": True},
            {
                "tool": "kushbitx_evaluate_spend",
                "ok": True,
                "advisory": True,
                "executionAuthorizedByThisTool": False,
            },
            {
                "tool": "kushbitx_discover_x402",
                "ok": True,
                "stoppedAtPaymentChallenge": True,
                "signed": False,
                "paid": False,
            },
        ]
        trace = run_agent(DEFAULT_MISSION)
        self.assertEqual([event["action"] for event in trace if event["type"] == "planner"], [
            "preview", "spend", "challenge", "finish"
        ])
        self.assertEqual(run_bridge.call_count, 3)
        output = render_trace(DEFAULT_MISSION, trace)
        self.assertIn("no private key requested or stored", output)
        self.assertIn("SpendGuard is advisory evaluation", output)

    @patch("src.agent.run_bridge", side_effect=RuntimeError("upstream failed"))
    def test_agent_surfaces_tool_failure_and_does_not_mark_progress(self, _run_bridge):
        with self.assertRaisesRegex(RuntimeError, "upstream failed"):
            run_agent(DEFAULT_MISSION)


if __name__ == "__main__":
    unittest.main()
