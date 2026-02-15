from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import ResearchState
from ..config import Config

class KnowledgeSynthesizer:
    """
    Agent responsible for synthesizing research findings into high-level insights.
    """
    def __init__(self):
        """
        Initializes the KnowledgeSynthesizer with LLM.
        """
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.4,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.prompt = ChatPromptTemplate.from_template(
            """Generate high-level insights, trends, and implications based on the research findings.
            
            Query: {query}
            
            Claims:
            {claims}
            
            Contradictions:
            {contradictions}
            
            Provide a list of 3-5 unique insights that go beyond the raw facts.
            """
        )

    def run(self, state: ResearchState) -> dict:
        """
        Executes the knowledge synthesis process.
        
        Args:
            state: Current research state containing claims and contradictions.
            
        Returns:
            Dictionary containing generated insights.
        """
        print("--- INSIGHT AGENT ---")
        query = state["query"]
        claims = state.get("claims", [])
        contradictions = state.get("contradictions", [])
        
        claims_text = "\n".join([f"- {c.get('claim_text')}" for c in claims])
        contradictions_text = "\n".join([f"- {c.get('claim_1')} vs {c.get('claim_2')}" for c in contradictions])
        
        chain = self.prompt | self.llm
        result = chain.invoke({
            "query": query, 
            "claims": claims_text, 
            "contradictions": contradictions_text
        })
        
        insights = [line.strip() for line in result.content.split('\n') if line.strip() and line.strip().startswith("-")]
        if not insights:
             insights = [line.strip() for line in result.content.split('\n') if line.strip()]

        print(f"Generated {len(insights)} insights.")
        return {"insights": insights, "stage": "editing"}
