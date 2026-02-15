from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from tavily import TavilyClient
from ..state import ResearchState
from ..config import Config

class ResearchStrategist:
    """
    Agent responsible for planning and refining research strategies.
    
    Generates sub-questions based on the initial query and context, or focused queries 
    to resolve specific contradictions.
    """
    def __init__(self):
        """
        Initializes the ResearchStrategist with LLM and Tavily client.
        """
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=0,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)
        
        self.prompt = ChatPromptTemplate.from_template(
            """You are a research planner. 
            I have performed an initial search on the query: "{query}".
            
            Here is the context summary:
            {context}
            
            Based on this, generate {max_questions} UNIQUE and distinct sub-questions detailed enough to provide a comprehensive answer.
            Avoid overlap.
            
            Assign the best tool for each question:
            - [Wikipedia]: For definitions, history, general knowledge, persons, places.
            - [Arxiv]: For scientific papers, physics, math, computer science, technical research.
            - [Tavily]: For recent news, current events, specific facts, or broader web search.
            
            Return ONLY a list of questions, one per line, prefixed with the tool.
            Example:
            [Wikipedia] Who discovered coffee?
            [Tavily] What are the latest coffee price trends?
            """
        )
        
        self.loop_prompt = ChatPromptTemplate.from_template(
            """You are a research strategist resolving a specific contradiction.
            
            Original Query: {query}
            
            Top Contradiction to Resolve:
            {contradiction}
            
            Generate EXACLTY ONE (1) focused search query to resolve this specific contradiction.
            Prefix it with the best tool: [Wikipedia], [Arxiv], or [Tavily].
            
            Return ONLY the question.
            """
        )

    def run(self, state: ResearchState) -> dict:
        """
        Executes the strategist logic.
        
        Args:
            state: Current research state.
            
        Returns:
            Dictionary containing generated sub-questions or a focused query for conflict resolution.
        """
        print("--- PLANNER AGENT ---")
        query = state["query"]
        loop_count = state.get("loop_count", 0)
        
        # Check if we are in a loop (specific contradiction resolution)
        # We need to check if 'top_contradiction' exists or if we are just looping.
        # Ideally, CriticalAnalysis sets 'top_contradiction'.
        top_contradiction = state.get("top_contradiction")
        
        if loop_count > 0 and top_contradiction:
            print(f"Looping ({loop_count}): Targeting Top Contradiction.")
            
            contradiction_text = f"- {top_contradiction.get('claim_1')} vs {top_contradiction.get('claim_2')}"
            chain = self.loop_prompt | self.llm
            result = chain.invoke({
                "query": query,
                "contradiction": contradiction_text
            })
            
            focused_query = result.content.strip()
            print(f"Generated focused query: {focused_query}")
            
            # For the loop, we set this as the ONLY question to retrieve
            return {
                "current_sub_questions": [focused_query],
                "stage": "retrieving"
            }

        else:
            # Initial Run: 1 Tavily Search -> 5 Sub-questions
            print(f"Performing initial broad search for: {query}")
            try:
                # 1. Initial Search
                search_result = self.tavily.search(query, search_depth="advanced", max_results=5)
                # Create a context summary from the results
                context_snippets = [r.get("content", "")[:200] for r in search_result.get("results", [])]
                context = "\n".join(context_snippets)
                
                # 2. Generate Sub-questions from Context
                chain = self.prompt | self.llm
                result = chain.invoke({
                    "query": query,
                    "context": context,
                    "max_questions": Config.MAX_SUB_QUESTIONS # Should be 5
                })
                
                sub_questions = [line.strip() for line in result.content.split('\n') if line.strip()]
                # Enforce limit just in case
                sub_questions = sub_questions[:Config.MAX_SUB_QUESTIONS]
                
                print(f"Generated {len(sub_questions)} sub-questions based on initial context.")
                
                return {
                    "sub_questions": sub_questions, 
                    "current_sub_questions": sub_questions,
                    "stage": "retrieving"
                }
            except Exception as e:
                print(f"Error in Planner Initial Search: {e}")
                # Fallback: Generate questions without context if search fails
                fallback_sub = [query]
                return {
                    "sub_questions": fallback_sub,
                    "current_sub_questions": fallback_sub,
                    "stage": "retrieving"
                }
