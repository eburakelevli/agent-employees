import asyncio
import os
from contextlib import nullcontext

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from langchain_community.callbacks import get_openai_callback

from config import LLM_PROVIDER, OLLAMA_MODEL, OPENAI_MODEL, CLAUDE_MODEL
from agents.planner import create_plan
from agents.researcher import run_researcher
from agents.writer import run_writer
from agents.expert import run_expert
from agents.summarizer import run_summarizer
from tools.history import format_history, add_exchange

SLACK_MSG_LIMIT = 3000

_bot_user_id: str | None = None


# --- Helpers ---

def _agent_label(step: dict) -> str:
    label = step["agent"].upper()
    if step.get("role"):
        label += f": {step['role']}"
    return label


def _plan_progress(plan: list, current_index: int) -> str:
    lines = []
    for i, step in enumerate(plan):
        if i < current_index:
            icon = ":white_check_mark:"
        elif i == current_index:
            icon = ":gear:"
        else:
            icon = ":hourglass_flowing_sand:"
        lines.append(f"{icon} {i + 1}. {_agent_label(step)}")
    return "\n".join(lines)


def _build_context(step_results: list) -> str:
    parts = []
    for r in step_results:
        label = r["agent"].upper()
        if r.get("role"):
            label += f" ({r['role']})"
        parts.append(f"[{label}]:\n{r['result']}")
    return "\n\n".join(parts)


def _truncate(header: str, body: str) -> str:
    max_body = SLACK_MSG_LIMIT - len(header)
    if len(body) > max_body:
        body = body[:max_body - 3] + "..."
    return header + body


def _active_model() -> str:
    if LLM_PROVIDER == "ollama":
        return OLLAMA_MODEL
    if LLM_PROVIDER == "claude":
        return CLAUDE_MODEL
    return OPENAI_MODEL


STEP_TIMEOUT = 90


async def _dispatch(step: dict, context: str, full_request: str = "") -> str:
    parts = []
    if full_request:
        parts.append(f"Full user request (including conversation history):\n{full_request}")
    if context:
        parts.append(f"Previous agents' outputs:\n{context}")
    parts.append(f"Your specific task: {step['task']}")
    task = "\n\n".join(parts)

    agent = step["agent"]
    role = step.get("role")

    if agent == "researcher":
        coro = run_researcher(task)
    elif agent == "writer":
        coro = run_writer(task)
    elif agent == "expert":
        coro = run_expert(role or "Expert", task)
    elif agent == "summarizer":
        coro = run_summarizer(task)
    else:
        return f"Unknown agent: {agent}"

    try:
        return await asyncio.wait_for(coro, timeout=STEP_TIMEOUT)
    except asyncio.TimeoutError:
        return f"⚠️ Step timed out after {STEP_TIMEOUT}s."


async def _keepalive(client, channel: str, ts: str, base_text: str, stop: asyncio.Event):
    """Appends animated dots to the status message every 5s so it never looks frozen."""
    count = 0
    while not stop.is_set():
        await asyncio.sleep(5)
        if stop.is_set():
            break
        try:
            dots = "." * (count % 3 + 1)
            await client.chat_update(channel=channel, ts=ts, text=base_text + dots)
            count += 1
        except Exception:
            break


# --- Slack App ---

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.event("app_mention")
async def handle_mention(event, say, client):
    global _bot_user_id
    if _bot_user_id is None:
        _bot_user_id = (await client.auth_test())["user_id"]

    user_id = event["user"]
    channel = event["channel"]
    content = event["text"].replace(f"<@{_bot_user_id}>", "").strip()

    if not content:
        await say(
            "Give me a task and I'll plan it across agents.\n"
            "Or target one directly: `writer: <request>` or `researcher: <request>`"
        )
        return

    forced_agent = None
    for agent in ("writer", "researcher"):
        if content.lower().startswith(f"{agent}:"):
            forced_agent = agent
            content = content[len(agent) + 1:].strip()
            break

    original_content = content
    history = format_history(user_id)
    if history:
        content = f"{history}\n[CURRENT MESSAGE]\n{content}"

    try:
        ctx = get_openai_callback() if LLM_PROVIDER == "openai" else nullcontext()
        with ctx as cb:
            if forced_agent:
                result = await _run_single(say, client, channel, forced_agent, content)
            else:
                result = await _run_plan(say, client, channel, content)

        add_exchange(user_id, original_content, result or "")

        if LLM_PROVIDER == "openai" and cb is not None:
            cost_line = f"`{OPENAI_MODEL} · {cb.total_tokens:,} tokens · ${cb.total_cost:.5f}`"
        elif LLM_PROVIDER == "claude":
            cost_line = f"`{CLAUDE_MODEL}`"
        else:
            cost_line = f"`{OLLAMA_MODEL} (local) · no API cost`"
        await say(cost_line)

    except Exception as e:
        print(f"Error processing message: {e}")
        await say("Something went wrong. Try again.")


async def _run_single(say, client, channel: str, agent: str, content: str) -> str:
    resp = await say(f":gear: Running *{agent}*... · `{_active_model()}`")
    ts = resp["ts"]

    if agent == "researcher":
        result = await run_researcher(content)
    else:
        result = await run_writer(content)

    await client.chat_update(
        channel=channel,
        ts=ts,
        text=_truncate(f"*[{agent.upper()}]*\n", result),
    )
    return result


async def _run_plan(say, client, channel: str, content: str) -> str:
    resp = await say(f":brain: *Planning your task...* · `{_active_model()}`")
    ts = resp["ts"]

    plan = await create_plan(content)

    step_results = []
    for i, step in enumerate(plan):
        step_text = f"*Running plan:*\n{_plan_progress(plan, i)}"
        await client.chat_update(channel=channel, ts=ts, text=step_text)

        stop = asyncio.Event()
        keepalive = asyncio.create_task(_keepalive(client, channel, ts, step_text, stop))
        try:
            result = await _dispatch(step, _build_context(step_results), content)
        finally:
            stop.set()
            keepalive.cancel()

        step_results.append({
            "agent": step["agent"],
            "role": step.get("role"),
            "task": step["task"],
            "result": result,
        })

    await client.chat_update(
        channel=channel,
        ts=ts,
        text=f"*Done:*\n{_plan_progress(plan, len(plan))}",
    )

    for i, step in enumerate(step_results):
        is_last = i == len(step_results) - 1
        if is_last and step["agent"] == "summarizer":
            header = "*[FINAL SYNTHESIS]*\n"
        else:
            header = f"*[STEP {i + 1} — {_agent_label(step)}]*\n"
        await say(_truncate(header, step["result"]))

    return step_results[-1]["result"] if step_results else ""


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    print("Starting Agent Employees bot (Slack)...")
    try:
        await handler.start_async()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await handler.close_async()
        print("\nSlack bot stopped.")
