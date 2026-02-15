import operator
from typing import List, TypedDict, Annotated, Optional, Any

class ResearchState(TypedDict):
    """
    State definition for the research graph.
    
    Attributes:
        query: The original research query.
        sub_questions: Accumulated list of generated sub-questions.
        current_sub_questions: Active sub-questions for the current iteration.
        documents: Accumulated research documents.
        claims: Accumulated extracted claims.
        contradictions: List of identified contradictions.
        top_contradiction: The most critical contradiction to resolve.
        contradiction_confidence: Confidence score of the top contradiction.
        loop_count: Current iteration count of the research loop.
        max_loops: Maximum allowed iterations.
        insights: Accumulated insights from the research.
        hallucination_flags: List of potential hallucinated claims.
        report: Final generated report.
        stage: Current stage of the research process.
        logs: Execution logs.
        tool_usage: Usage statistics for external tools.
    """
    query: str
    sub_questions: Annotated[List[str], operator.add]
    current_sub_questions: List[str] # Non-accumulating list for current loop
    documents: Annotated[List[dict], operator.add]  # content, metadata, source
    claims: Annotated[List[dict], operator.add]     # claim_text, confidence, sources
    contradictions: List[dict]
    top_contradiction: Optional[dict] # Logic Refactor: Single targeted resolution
    contradiction_confidence: float
    loop_count: int
    max_loops: int
    insights: List[str]
    hallucination_flags: List[dict]
    report: str
    stage: str
    logs: Annotated[List[str], operator.add]
    tool_usage: Annotated[dict, lambda a, b: {k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)}]
