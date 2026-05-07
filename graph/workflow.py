from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.router import route_message
from agents.researcher import run_researcher
from agents.writer import run_writer


# --- State Definition ---
class AgentState(TypedDict):
    user_message: str       # The original message from Discord
    selected_agent: str     # Which agent the router picked
    response: str           # The final response to send back


# --- Node Functions ---
async def router_node(state: AgentState) -> dict:
    """Route the message to the correct agent."""
    agent = await route_message(state["user_message"])
    return {"selected_agent": agent}


async def researcher_node(state: AgentState) -> dict:
    """Run the researcher agent."""
    response = await run_researcher(state["user_message"])
    return {"response": response}


async def writer_node(state: AgentState) -> dict:
    """Run the writer agent."""
    response = await run_writer(state["user_message"])
    return {"response": response}


# --- Conditional Edge ---
def pick_agent(state: AgentState) -> str:
    """Decide which agent node to go to next."""
    return state["selected_agent"]


# --- Build the Graph ---
def build_workflow():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)

    # Set entry point
    workflow.set_entry_point("router")

    # Router decides which agent to use
    workflow.add_conditional_edges(
        "router",
        pick_agent,
        {
            "researcher": "researcher",
            "writer": "writer",
        },
    )

    # All agents end after responding
    workflow.add_edge("researcher", END)
    workflow.add_edge("writer", END)

    return workflow.compile()


# Compiled graph, ready to use
app = build_workflow()
