from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..state import ResearchState
from ..config import Config
import os
from datetime import datetime

class NarrativeDesigner:
    """
    Agent responsible for compiling the final research report.
    """
    def __init__(self):
        """
        Initializes the NarrativeDesigner with LLM.
        """
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0.3,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.prompt = ChatPromptTemplate.from_template(
            """Compile a structured research report based on the following claims and query.
            
            Query: {query}
            
            Claims:
            {claims}
            
            Contradictions Identified:
            {contradictions}
            
            Insights:
            {insights}
            
            Hallucination Warnings:
            {hallucinations}
            
            The report should include:
            - Executive Summary
            - Research Breakdown
            - Contradiction Analysis
            - Key Insights
            - Hallucination/Verification Notes
            - Limitations
            - References (List of source URLs)

            IMPORTANT: 
            - Use Markdown formatting.
            - Cite sources inline like [1], [2].
            - Include a "References" section at the bottom mapping [X] to URLs.
            """
        )

    def run(self, state: ResearchState) -> dict:
        print("--- EDITOR AGENT ---")
        query = state["query"]
        claims = state.get("claims", [])
        
        # Format claims for prompt
        claims_text = ""
        for i, c in enumerate(claims):
            source = c.get('source', 'Unknown')
            claims_text += f"{i+1}. {c.get('claim_text')} (Source: {source}, Confidence: {c.get('confidence')})\n"
            
        contradictions = state.get("contradictions", [])
        insights = state.get("insights", [])
        hallucinations = state.get("hallucination_flags", [])
        
        if state.get("loop_count", 0) > 0 and len(contradictions) > 0:
            contradictions_header = "PERSISTENT CONTRADICTIONS (Unresolved after research loop):"
        else:
            contradictions_header = "Contradictions Identified:"

        contradictions_text = f"{contradictions_header}\n" + "\n".join([f"- {c.get('claim_1')} vs {c.get('claim_2')}: {c.get('reasoning')}" for c in contradictions])
        insights_text = "\n".join([str(i) for i in insights])
        hallucinations_text = "\n".join([f"- Claim: {h.get('claim')} -> Flagged: {h.get('reason')}" for h in hallucinations])
            
        chain = self.prompt | self.llm
        result = chain.invoke({
            "query": query, 
            "claims": claims_text,
            "contradictions": contradictions_text,
            "insights": insights_text,
            "hallucinations": hallucinations_text
        })
        
        report_content = result.content
        
        # Save report to file
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(" ", "_")[:30]
        filename = f"{output_dir}/report_{timestamp}_{safe_query}.md"
        
        with open(filename, "w") as f:
            f.write(report_content)
            
        print(f"Report saved to {filename}")
        
        return {"report": report_content, "stage": "completed"}
