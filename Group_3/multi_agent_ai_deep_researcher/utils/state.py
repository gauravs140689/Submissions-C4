"""
State definitions for the Multi-Agent AI Deep Researcher using Pydantic.

This module defines all data models using Pydantic BaseModel for:
- Type validation and coercion
- Automatic serialization/deserialization
- IDE autocomplete support
- Runtime type checking

State models:
- SourceMetadata: Information about retrieved sources
- CritiqueSummary: Analysis output from Critic agent
- Insight: Generated insights with confidence scores
- ResearchState: Complete pipeline state (compatible with LangGraph)
"""

from typing import Optional, Any, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class SourceMetadata(BaseModel):
    """Metadata for a single source/document."""
    
    model_config = ConfigDict(extra="allow", from_attributes=True)
    
    url: str
    title: str = Field(default="", description="Source title")
    snippet: str = Field(default="", description="Search result snippet")
    excerpt: str = Field(default="", description="First 200 chars of content")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score 0-1")
    author: Optional[str] = Field(default=None, description="Author name if available")
    domain: str = Field(default="", description="Domain extracted from URL")
    
    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        return max(0.0, min(1.0, v))


class CritiqueSummary(BaseModel):
    """Analysis output from the Critic agent."""
    
    model_config = ConfigDict(extra="allow")
    
    strengths: List[str] = Field(default_factory=list, description="Data strengths")
    weaknesses: List[str] = Field(default_factory=list, description="Data weaknesses")
    contradictions: List[str] = Field(default_factory=list, description="Found contradictions")
    sources_flagged: List[str] = Field(default_factory=list, description="Flagged sources")
    needs_refinement: bool = Field(default=False, description="Needs more retrieval")
    coverage_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Coverage quality")


class Insight(BaseModel):
    """Individual insight with confidence and supporting sources."""
    
    model_config = ConfigDict(extra="allow")
    
    text: str = Field(description="Insight text")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence 0-1")
    supporting_sources: List[str] = Field(default_factory=list, description="Source URLs")
    reasoning: str = Field(default="", description="Reasoning behind insight")


class ResearchState(BaseModel):
    """
    Complete state for research pipeline.
    
    Contains all data flowing through agents in the LangGraph workflow.
    Compatible with LangGraph by supporting dict conversion.
    """
    
    model_config = ConfigDict(extra="allow", from_attributes=True)
    
    # Message History (LangChain messages stored as dicts)
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Message history from LangChain"
    )
    
    # Input
    user_query: str = Field(description="Original research question")
    session_id: str = Field(description="Unique session identifier")
    
    # Retrieval State
    retrieved_docs: List[str] = Field(
        default_factory=list,
        description="List of document texts retrieved"
    )
    source_metadata: Dict[str, SourceMetadata] = Field(
        default_factory=dict,
        description="Mapping of doc_id to source metadata"
    )
    
    # Analysis State
    summary: Optional[str] = Field(default=None, description="Synthesized summary")
    critique: CritiqueSummary = Field(default_factory=CritiqueSummary)
    insights: List[Insight] = Field(
        default_factory=list,
        description="Generated insights with confidence"
    )
    
    # Final Output
    final_report: Optional[str] = Field(default=None, description="Markdown report")
    
    # Control Flow
    current_step: str = Field(default="", description="Currently executing agent")
    error_messages: List[str] = Field(
        default_factory=list,
        description="Errors encountered"
    )
    iteration_count: int = Field(default=0, description="Retrieval iteration count")
    total_iterations: int = Field(default=3, description="Max iterations allowed")
    needs_refinement: bool = Field(default=False, description="Refine retrieval flag")
    
    # Metadata & Tracking
    report_generated_at: Optional[str] = Field(default=None, description="Report timestamp")
    total_sources_used: int = Field(default=0, description="Source count in report")
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Performance metrics"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for LangGraph compatibility."""
        data = self.model_dump(exclude_none=False)
        # Convert Pydantic models to dicts
        if data.get("source_metadata"):
            data["source_metadata"] = {
                k: v.model_dump() if isinstance(v, SourceMetadata) else v
                for k, v in data["source_metadata"].items()
            }
        if data.get("critique"):
            if isinstance(data["critique"], CritiqueSummary):
                data["critique"] = data["critique"].model_dump()
        if data.get("insights"):
            data["insights"] = [
                i.model_dump() if isinstance(i, Insight) else i
                for i in data["insights"]
            ]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchState":
        """Create from dict (LangGraph integration)."""
        # Convert nested dicts to Pydantic models
        if "source_metadata" in data and isinstance(data["source_metadata"], dict):
            data["source_metadata"] = {
                k: SourceMetadata(**v) if isinstance(v, dict) else v
                for k, v in data["source_metadata"].items()
            }
        
        if "critique" in data and isinstance(data["critique"], dict):
            data["critique"] = CritiqueSummary(**data["critique"])
        
        if "insights" in data and isinstance(data["insights"], list):
            data["insights"] = [
                Insight(**i) if isinstance(i, dict) else i
                for i in data["insights"]
            ]
        
        return cls(**data)
    
    def add_error(self, error: str) -> None:
        """Add error message to state."""
        if error not in self.error_messages:
            self.error_messages.append(error)
    
    def add_document(self, content: str, metadata: SourceMetadata) -> None:
        """Add a retrieved document with metadata."""
        self.retrieved_docs.append(content)
        # Use URL hash as doc_id
        import hashlib
        doc_id = hashlib.md5(metadata.url.encode()).hexdigest()[:8]
        self.source_metadata[doc_id] = metadata
    
    def add_insight(self, insight: Insight) -> None:
        """Add an insight to the state."""
        self.insights.append(insight)


# Type alias for state updates returned by agents
StateUpdate = Dict[str, Any]


__all__ = [
    "ResearchState",
    "SourceMetadata",
    "CritiqueSummary",
    "Insight",
    "StateUpdate",
]
