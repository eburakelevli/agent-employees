import importlib
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError

from agents.planner import MAX_PLAN_STEPS, Plan, PlanValidationError, create_plan


WRITER = {"agent": "writer", "task": "Write a draft"}
SUMMARY = {"agent": "summarizer", "task": "Synthesize the findings"}
VALID_JSON = json.dumps({"steps": [WRITER]})


def fake_model(*contents):
    return SimpleNamespace(
        ainvoke=AsyncMock(side_effect=[SimpleNamespace(content=c) for c in contents])
    )


class PlanSchemaTests(unittest.TestCase):
    def test_rejects_invalid_plans(self):
        invalid = [
            None, [], "plan", {}, {"steps": None}, {"steps": []},
            {"steps": "writer"}, {"steps": [None]},
            {"steps": [{"agent": "unknown", "task": "Do something"}]},
            {"steps": [{"agent": "writer"}]},
            {"steps": [{"task": "Do something"}]},
            {"steps": [{"agent": "writer", "task": " \n "}]},
            {"steps": [{"agent": "writer", "task": 42}]},
            {"steps": [{**WRITER, "role": 42}]},
            {"steps": [{**WRITER, "unexpected": True}]},
            {"steps": [WRITER], "unexpected": True},
            {"steps": [WRITER] * MAX_PLAN_STEPS + [SUMMARY]},
            {"steps": [WRITER] * 3},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                Plan.model_validate(payload)

    def test_experts_require_specific_nonempty_roles(self):
        for role in (None, "", "  ", "Expert", " eXpErT "):
            with self.subTest(role=role), self.assertRaises(ValidationError):
                Plan.model_validate({"steps": [{"agent": "expert", "task": "Review", "role": role}]})

    def test_valid_agents_and_whitespace_normalization(self):
        for agent in ("writer", "researcher", "summarizer", "expert"):
            with self.subTest(agent=agent):
                plan = Plan.model_validate({"steps": [{
                    "agent": agent, "task": "  Review this  ",
                    "role": " Senior Engineer " if agent == "expert" else None,
                }]})
                self.assertEqual(plan.steps[0].task, "Review this")
                if agent == "expert":
                    self.assertEqual(plan.steps[0].role, "Senior Engineer")

    def test_accepts_two_steps_without_summarizer_and_maximum_with_one(self):
        self.assertEqual(len(Plan.model_validate({"steps": [WRITER] * 2}).steps), 2)
        plan = Plan.model_validate({"steps": [WRITER] * (MAX_PLAN_STEPS - 1) + [SUMMARY]})
        self.assertEqual(len(plan.steps), MAX_PLAN_STEPS)


class CreatePlanTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_output_does_not_retry(self):
        model = fake_model(VALID_JSON)
        with patch("agents.planner.get_llm", return_value=model):
            result = await create_plan("Write a draft")
        self.assertEqual(result, [{**WRITER, "role": None}])
        self.assertEqual(model.ainvoke.await_count, 1)

    async def test_accepts_fenced_json_and_provider_text_blocks(self):
        for content in (
            f"```json\n{VALID_JSON}\n```",
            [{"type": "text", "text": VALID_JSON}],
        ):
            with self.subTest(content=content):
                model = fake_model(content)
                with patch("agents.planner.get_llm", return_value=model):
                    self.assertEqual((await create_plan("Draft"))[0]["agent"], "writer")
                self.assertEqual(model.ainvoke.await_count, 1)

    async def test_repairs_json_and_schema_errors_once(self):
        for invalid in ("not JSON", "{}", '{"steps":null}', VALID_JSON + " trailing text"):
            with self.subTest(invalid=invalid):
                model = fake_model(invalid, VALID_JSON)
                with patch("agents.planner.get_llm", return_value=model):
                    self.assertEqual((await create_plan("Original request"))[0]["agent"], "writer")
                self.assertEqual(model.ainvoke.await_count, 2)
                repair_messages = model.ainvoke.call_args_list[1].args[0]
                self.assertEqual(repair_messages[1]["content"], "Original request")
                self.assertEqual(repair_messages[2]["content"], invalid)
                self.assertIn("Validation errors:", repair_messages[3]["content"])

    async def test_second_invalid_response_raises_clear_error_without_third_call(self):
        model = fake_model("{}", '{"steps":[]}', VALID_JSON)
        with patch("agents.planner.get_llm", return_value=model):
            with self.assertRaisesRegex(PlanValidationError, "No steps were run"):
                await create_plan("Draft")
        self.assertEqual(model.ainvoke.await_count, 2)

    async def test_provider_failure_is_not_retried_as_validation_failure(self):
        model = SimpleNamespace(ainvoke=AsyncMock(side_effect=RuntimeError("Provider unavailable")))
        with patch("agents.planner.get_llm", return_value=model):
            with self.assertRaisesRegex(RuntimeError, "Provider unavailable"):
                await create_plan("Draft")
        self.assertEqual(model.ainvoke.await_count, 1)


class ExecutionBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_discord_does_not_execute_valid_prefix_of_invalid_plan(self):
        import bot

        # The first step is valid; the whole plan must pass before it can run.
        invalid = json.dumps({"steps": [WRITER, {"agent": "expert", "task": "Review"}]})
        model = fake_model(invalid, invalid)
        status = SimpleNamespace(edit=AsyncMock())
        message = SimpleNamespace(reply=AsyncMock(return_value=status))
        with patch("agents.planner.get_llm", return_value=model), patch.object(bot, "_dispatch", new_callable=AsyncMock) as dispatch:
            with self.assertRaises(PlanValidationError):
                await bot.AgentBot._run_plan(None, message, "Draft and review")
        dispatch.assert_not_awaited()
        status.edit.assert_awaited_once_with(content="⚠️ Planning failed.")

    async def test_slack_does_not_execute_invalid_plan(self):
        # Replace app registration so importing Slack requires no credentials or network.
        fake_app = MagicMock()
        fake_app.event.side_effect = lambda event: lambda handler: handler
        with patch("slack_bolt.async_app.AsyncApp", return_value=fake_app):
            slack_bot = importlib.import_module("slack_bot")
        model = fake_model("{}", "{}")
        say = AsyncMock(return_value={"ts": "review-status"})
        client = SimpleNamespace(chat_update=AsyncMock())
        with patch("agents.planner.get_llm", return_value=model), patch.object(slack_bot, "_dispatch", new_callable=AsyncMock) as dispatch:
            with self.assertRaises(PlanValidationError):
                await slack_bot._run_plan(say, client, "review-channel", "Draft")
        dispatch.assert_not_awaited()
        client.chat_update.assert_awaited_once_with(
            channel="review-channel", ts="review-status", text="⚠️ Planning failed."
        )

    async def test_graph_does_not_execute_invalid_plan(self):
        from graph import workflow

        model = fake_model("{}", "{}")
        with patch("agents.planner.get_llm", return_value=model), patch.object(workflow, "run_writer", new_callable=AsyncMock) as writer:
            with self.assertRaises(PlanValidationError):
                await workflow.app.ainvoke({"user_message": "Draft"})
        writer.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
