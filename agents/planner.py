import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from llm import get_llm

MAX_PLAN_STEPS = 8


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    agent: Literal["researcher", "writer", "expert", "summarizer"]
    task: str = Field(min_length=1)
    role: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_expert_role(self) -> "Step":
        if self.agent == "expert" and (not self.role or self.role.casefold() == "expert"):
            raise ValueError("Expert steps require a specific role, not just 'Expert'.")
        return self


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    steps: list[Step] = Field(min_length=1, max_length=MAX_PLAN_STEPS)

    @model_validator(mode="after")
    def require_final_synthesis(self) -> "Plan":
        if len(self.steps) >= 3 and self.steps[-1].agent != "summarizer":
            raise ValueError("Plans with three or more steps must end with a summarizer.")
        return self


class PlanValidationError(ValueError):
    """The planner failed validation after its single repair attempt."""

    def __init__(self):
        super().__init__(
            "I couldn't create a valid execution plan after two attempts. "
            "No steps were run. Please rephrase your request and try again."
        )


PLANNER_PROMPT = """You are a task planner for a multi-agent AI assistant. Break the user's request into an execution plan.

Available agents and their tools:
- researcher: web search, read local files — use for facts, research, reading docs the user provides
- writer: writing content, emails, posts, articles, copy, drafts
- expert: any domain expertise or tool execution — always give a specific role (e.g. "Senior Software Engineer", "Google Workspace Operator", "Product Manager"). Has tools: read files, run Python code, save/recall memory, create Google Drive folders, create Google Docs, create Google Slides, and create Google Sheets via MCP
- summarizer: synthesize multiple outputs into one final cohesive response

Rules:
- The user message may be prefixed with conversation history — use it as context but plan only for the current request at the bottom
- Simple requests (one clear output): 1-2 steps max
- Follow-up or history questions (e.g. "what did I ask?", "expand on that"): use {"agent": "expert", "role": "Conversational Assistant", "task": "..."} — never use "Conversational Assistant" as the agent field
- Complex requests: break into logical sequential steps where later steps build on earlier ones
- For plans with 3+ steps, always end with a summarizer step
- Expert roles must be specific and descriptive, not just "Expert"
- Task descriptions must be specific and actionable
- If the user mentions a file path, include it in the relevant step's task description
- If the user asks to create a Google Sheet/spreadsheet, Google Doc, Slides deck, or Drive folder, use exactly one expert step with role "Google Workspace Operator". The task must explicitly say which MCP tool to use and include the title/name and folder_id. Use folder_id "root" if no folder is provided.
- Never plan a Google Workspace creation request as "Conversational Assistant"; it requires an expert tool call.

The "agent" field must be one of exactly: "researcher", "writer", "expert", "summarizer". Nothing else is valid.

Return ONLY valid JSON in this exact format:
{"steps": [{"agent": "...", "role": null, "task": "..."}, ...]}"""

PLANNER_PROMPT += f"\nReturn between 1 and {MAX_PLAN_STEPS} steps. Do not include extra fields."


def _parse_plan_json(content: str | list) -> Any:
    # Some providers return text blocks rather than a plain string.
    if isinstance(content, list):
        content = "\n".join(
            block["text"] for block in content
            if isinstance(block, dict) and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )
    if not isinstance(content, str):
        raise ValueError("Planner output must contain JSON text.")
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    return json.loads(text)


async def create_plan(user_message: str) -> list[dict]:
    llm = get_llm(temperature=0, json_mode=True)
    messages = [
        {"role": "system", "content": PLANNER_PROMPT},
        {"role": "user", "content": user_message},
    ]
    for attempt in range(2):
        response = await llm.ainvoke(messages)
        try:
            plan = Plan.model_validate(_parse_plan_json(response.content))
        except ValueError as exc:
            if attempt == 1:
                raise PlanValidationError() from exc
            messages = [
                *messages,
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": (
                        "Your plan failed validation. Correct it for the original request. "
                        "Return only the complete JSON plan, following all planning rules.\n"
                        f"Validation errors:\n{str(exc)[:2000]}"
                    ),
                },
            ]
        else:
            return [step.model_dump() for step in plan.steps]
