from langgraph.graph import StateGraph, END
from .state import ResearchState
from .agents.research_strategist import ResearchStrategist
from .agents.information_gatherer import InformationGatherer
from .agents.claim_extractor import ClaimExtractor
from .agents.narrative_designer import NarrativeDesigner
from .agents.conflict_detector import ConflictDetector
from .agents.source_verifier import SourceVerifier
from .agents.knowledge_synthesizer import KnowledgeSynthesizer
from .config import Config

def increment_loop(state: ResearchState) -> dict:
    """
    Increments the loop counter in the state.
    
    Args:
        state: Current research state.
        
    Returns:
        A dictionary with the updated loop_count.
    """
    current_loop = state.get("loop_count", 0)
    print(f"--- LOOP INCREMENT ({current_loop + 1}) ---")
    return {"loop_count": current_loop + 1}

def check_contradiction(state):
    """
    Determines the next step based on conflict detection results.
    
    Routes to 'increment_loop' if a critical contradiction is found and loop limit is not reached.
    Otherwise, routes to 'source_verifier'.
    
    Args:
        state: Current research state.
        
    Returns:
        The name of the next node to execute.
    """
    loop_count = state.get("loop_count", 0)
    max_loops = state.get("max_loops", 2)
    top_contradiction = state.get("top_contradiction")
    
    # If we have a critical contradiction and haven't hit max loops
    if top_contradiction and loop_count < max_loops:
        print(f"Contradiction found. Entering loop {loop_count + 1}")
        return "increment_loop"
    
    print("No critical contradiction or max loops reached. Proceeding to Source Verifier.")
    return "source_verifier"

def create_graph():
    """
    Constructs the LangGraph state graph for the research workflow.
    
    Initializes agents, defines nodes and edges, and sets up conditional routing.
    
    Returns:
        A compiled StateGraph application.
    """
    # Initialize agents
    strategist = ResearchStrategist()
    gatherer = InformationGatherer()
    extractor = ClaimExtractor()
    detector = ConflictDetector()
    verifier = SourceVerifier()
    synthesizer = KnowledgeSynthesizer()
    designer = NarrativeDesigner()

    # Create graph
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("strategist", strategist.run)
    workflow.add_node("gatherer", gatherer.run)
    workflow.add_node("extractor", extractor.run)
    workflow.add_node("detector", detector.run)
    workflow.add_node("increment_loop", increment_loop)
    workflow.add_node("source_verifier", verifier.run)
    workflow.add_node("knowledge_synthesizer", synthesizer.run)
    workflow.add_node("narrative_designer", designer.run)

    # Define edges
    # Define edges
    workflow.set_entry_point("strategist")
    workflow.add_edge("strategist", "gatherer")
    workflow.add_edge("gatherer", "extractor")
    workflow.add_edge("extractor", "detector")
    
    # Conditional logic
    workflow.add_conditional_edges(
        "detector",
        check_contradiction,
        {
            "increment_loop": "increment_loop",
            "source_verifier": "source_verifier"
        }
    )
    
    workflow.add_edge("increment_loop", "strategist")
    workflow.add_edge("source_verifier", "knowledge_synthesizer")
    workflow.add_edge("knowledge_synthesizer", "narrative_designer")
    workflow.add_edge("narrative_designer", END)

    # Compile
    app = workflow.compile()
    return app
