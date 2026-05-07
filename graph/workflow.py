from typing import TypedDict
from langgraph.graph import StateGraph, END, START

from agents.researcher import run_researcher
from agents.writer import run_writer
from agents.expert import run_expert
from agents.planner import create_plan
from agents.summarizer import run_summarizer


class AgentState(TypedDict):
    user_message: str
    selected_agent: str   # set by bot when user uses explicit prefix (writer:/researcher:)
    plan: list            # list of {agent, role, task} dicts created by planner
    step_results: list    # list of {agent, role, task, result} dicts from executor
    response: str         # final response text


# --- Entry routing ---

def route_entry(state: AgentState) -> str:
    if state.get("selected_agent") in ("writer", "researcher"):
        return "single"
    return "planner"


# --- Nodes ---

async def planner_node(state: AgentState) -> dict:
    plan = await create_plan(state["user_message"])
    return {"plan": plan}


async def executor_node(state: AgentState) -> dict:
    """Execute each plan step sequentially, passing accumulated context forward."""
    step_results = []

    for step in state["plan"]:
        task = step["task"]

        if step_results:
            context_parts = []
            for r in step_results:
                label = r["agent"].upper()
                if r.get("role"):
                    label += f" ({r['role']})"
                context_parts.append(f"[{label}]:\n{r['result']}")
            context = "\n\n".join(context_parts)
            task = f"Previous agents have gathered the following:\n{context}\n\nYour task: {task}"

        agent = step["agent"]
        role = step.get("role")

        if agent == "researcher":
            result = await run_researcher(task)
        elif agent == "writer":
            result = await run_writer(task)
        elif agent == "expert":
            result = await run_expert(role or "Expert", task)
        elif agent == "summarizer":
            result = await run_summarizer(task)
        else:
            result = f"Unknown agent: {agent}"

        step_results.append({
            "agent": agent,
            "role": role,
            "task": step["task"],
            "result": result,
        })

    return {
        "step_results": step_results,
        "response": step_results[-1]["result"] if step_results else "",
    }


async def single_agent_node(state: AgentState) -> dict:
    """Direct execution when the user explicitly chose an agent via prefix."""
    agent = state["selected_agent"]
    message = state["user_message"]

    if agent == "researcher":
        result = await run_researcher(message)
    elif agent == "writer":
        result = await run_writer(message)
    else:
        result = await run_researcher(message)

    step_results = [{"agent": agent, "role": None, "task": message, "result": result}]
    return {"step_results": step_results, "response": result}


# --- Build graph ---

def build_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("single", single_agent_node)

    workflow.add_conditional_edges(START, route_entry, {
        "single": "single",
        "planner": "planner",
    })

    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", END)
    workflow.add_edge("single", END)

    return workflow.compile()


app = build_workflow()
