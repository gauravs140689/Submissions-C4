from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import ResearchState
from ..config import Config
import json

class ConflictDetector:
    """
    Agent responsible for detecting contradictions between extracted claims.
    """
    def __init__(self):
        """
        Initializes the ConflictDetector with LLM.
        """
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.prompt = ChatPromptTemplate.from_template(
            """Analyze the following claims for contradictions. 
            
            Query: {query}
            
            Claims:
            {claims}
            
            Identify if there are any contradictions between the claims.
            If yes, list them and assign a contradiction confidence score (0.0 to 1.0).
            
            Return JSON format:
            {{
                "contradictions": [
                    {{
                        "claim_1": "text",
                        "claim_2": "text",
                        "reasoning": "explanation"
                    }}
                ],
                "contradiction_confidence": float
            }}
            """
        )

    def run(self, state: ResearchState) -> dict:
        """
        Executes the conflict detection process.
        
        Args:
            state: Current research state containing claims.
            
        Returns:
            Dictionary containing identified contradictions and confidence scores.
        """
        print("--- CRITICAL ANALYSIS AGENT ---")
        query = state["query"]
        claims = state.get("claims", [])
        
        if len(claims) < 2:
            return {"contradictions": [], "contradiction_confidence": 0.0, "stage": "debunking"}

        claims_text = ""
        for i, c in enumerate(claims):
            claims_text += f"{i+1}. {c.get('claim_text')}\n"
            
        try:
            chain = self.prompt | self.llm
            result = chain.invoke({"query": query, "claims": claims_text})
            
            content = result.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            analysis = json.loads(content)
            
            contradictions = analysis.get("contradictions", [])
            confidence = analysis.get("contradiction_confidence", 0.0)
            
            print(f"Detected {len(contradictions)} contradictions with confidence {confidence}")
            
            if contradictions:
                # Sort by confidence or severity if available (mocking selection of first/best for now)
                # In a real scenario, we'd have a 'score' field. 
                # Let's assume the LLM output list puts most significant first.
                top_contradiction = contradictions[0]
                print(f"Identified Top Contradiction: {top_contradiction.get('claim_1')} vs {top_contradiction.get('claim_2')}")
            else:
                top_contradiction = None

            return {
                "contradictions": contradictions,
                "top_contradiction": top_contradiction, # New State Field
                "contradiction_confidence": confidence,
                "stage": "checking_loop"  # We'll use graph conditional logic
            }
            
        except Exception as e:
            print(f"Error in critical analysis: {e}")
            return {"contradictions": [], "contradiction_confidence": 0.0, "stage": "debunking"}
