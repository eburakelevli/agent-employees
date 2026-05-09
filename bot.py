import asyncio
from contextlib import asynccontextmanager, nullcontext
import discord
from config import LLM_PROVIDER, OLLAMA_MODEL, OPENAI_MODEL
from langchain_community.callbacks import get_openai_callback

from agents.planner import create_plan
from agents.researcher import run_researcher
from agents.writer import run_writer
from agents.expert import run_expert
from agents.summarizer import run_summarizer

DISCORD_MSG_LIMIT = 2000


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
            icon = "✅"
        elif i == current_index:
            icon = "⚙️"
        else:
            icon = "⏳"
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


STEP_TIMEOUT = 90  # seconds before a step is considered hung


async def _dispatch(step: dict, context: str) -> str:
    task = step["task"]
    if context:
        task = f"Previous agents have gathered:\n{context}\n\nYour task: {task}"

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


async def _keepalive(status_msg: discord.Message, base_text: str, stop: asyncio.Event):
    """Appends animated dots to the status message every 5s so it never looks frozen."""
    count = 0
    while not stop.is_set():
        await asyncio.sleep(5)
        if stop.is_set():
            break
        try:
            dots = "." * (count % 3 + 1)
            await status_msg.edit(content=base_text + dots)
            count += 1
        except Exception:
            break


def _active_model() -> str:
    return OLLAMA_MODEL if LLM_PROVIDER == "ollama" else OPENAI_MODEL


def _truncate(header: str, body: str) -> str:
    max_body = DISCORD_MSG_LIMIT - len(header)
    if len(body) > max_body:
        body = body[:max_body - 3] + "..."
    return header + body


# --- Bot ---

class AgentBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Bot is online as {self.user}")
        print(f"Connected to {len(self.guilds)} server(s)")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        if not is_mentioned and not is_dm:
            return

        content = message.content.replace(f"<@{self.user.id}>", "").strip()
        if not content:
            await message.reply(
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

        try:
            ctx = get_openai_callback() if LLM_PROVIDER == "openai" else nullcontext()
            with ctx as cb:
                if forced_agent:
                    await self._run_single(message, forced_agent, content)
                else:
                    await self._run_plan(message, content)

            if LLM_PROVIDER == "openai" and cb is not None:
                cost_line = f"`{cb.total_tokens:,} tokens · ${cb.total_cost:.5f}`"
            else:
                cost_line = f"`local · {OLLAMA_MODEL}`"
            await message.channel.send(cost_line)

        except Exception as e:
            print(f"Error processing message: {e}")
            await message.reply("Something went wrong. Try again.")

    async def _run_single(self, message: discord.Message, agent: str, content: str):
        status = await message.reply(f"⚙️ Running **{agent}**... · `{_active_model()}`")

        if agent == "researcher":
            result = await run_researcher(content)
        else:
            result = await run_writer(content)

        await status.edit(content=_truncate(f"**[{agent.upper()}]**\n", result))

    async def _run_plan(self, message: discord.Message, content: str):
        status = await message.reply(f"🧠 **Planning your task...** · `{_active_model()}`")

        plan = await create_plan(content)

        step_results = []
        for i, step in enumerate(plan):
            step_text = f"**Running plan:**\n{_plan_progress(plan, i)}"
            await status.edit(content=step_text)

            stop = asyncio.Event()
            keepalive = asyncio.create_task(_keepalive(status, step_text, stop))
            try:
                result = await _dispatch(step, _build_context(step_results))
            finally:
                stop.set()
                keepalive.cancel()

            step_results.append({
                "agent": step["agent"],
                "role": step.get("role"),
                "task": step["task"],
                "result": result,
            })

        await status.edit(content=f"**Done:**\n{_plan_progress(plan, len(plan))}")

        for i, step in enumerate(step_results):
            is_last = i == len(step_results) - 1
            if is_last and step["agent"] == "summarizer":
                header = "**[FINAL SYNTHESIS]**\n"
            else:
                header = f"**[STEP {i + 1} — {_agent_label(step)}]**\n"
            await message.channel.send(_truncate(header, step["result"]))
