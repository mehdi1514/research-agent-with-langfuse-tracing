from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from agent.nodes import (
    coordinator,
    web_searcher,
    summarizer,
    critic,
    reviser,
    assembler,
)
from agent.state import ResearchState


# ============================================================================
# Routing functions
# ============================================================================


def route_critic(state: ResearchState) -> str:
    """Route based on critic feedback.

    Returns:
        "pass" if critic approves or max iterations reached.
        "revise" otherwise.
    """
    iteration_count = state.get("iteration_count", 0)
    if iteration_count >= 2:
        return "pass"

    feedback = state.get("critic_feedback", "").lower()
    if feedback.startswith("pass"):
        return "pass"
    return "revise"


# ============================================================================
# Build the graph
# ============================================================================

research_graph = StateGraph(ResearchState)

# Add nodes
research_graph.add_node("coordinator", coordinator)
research_graph.add_node("web_searcher", web_searcher)
research_graph.add_node("summarizer", summarizer)
research_graph.add_node("critic", critic)
research_graph.add_node("reviser", reviser)
research_graph.add_node("assembler", assembler)

# Linear flow up to critic
research_graph.add_edge(START, "coordinator")
research_graph.add_edge("coordinator", "web_searcher")
research_graph.add_edge("web_searcher", "summarizer")
research_graph.add_edge("summarizer", "critic")

# Critic loop
research_graph.add_conditional_edges(
    "critic",
    route_critic,
    {"pass": "assembler", "revise": "reviser"},
)

# Reviser feeds back to critic for re-evaluation
research_graph.add_edge("reviser", "critic")

# Assembler → END
research_graph.add_edge("assembler", END)

# Compile with in-memory checkpointing
memory_saver = MemorySaver()
compiled_research_graph = research_graph.compile(checkpointer=memory_saver)
