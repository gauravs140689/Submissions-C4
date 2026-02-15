from tavily import TavilyClient
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from ..state import ResearchState
from ..config import Config

class InformationGatherer:
    """
    Agent responsible for gathering information from various sources.
    
    Supports Tavily (web search), Wikipedia, and Arxiv.
    """
    def __init__(self):
        self.tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)
        self.wikipedia = WikipediaAPIWrapper()
        self.arxiv = ArxivAPIWrapper()

    def run(self, state: ResearchState) -> dict:
        """
        Executes the information gathering process.
        
        Args:
            state: Current research state containing sub-questions.
            
        Returns:
            Dictionary containing retrieved documents and tool usage statistics.
        """
        print("--- RETRIEVER AGENT ---")
        
        queries_to_run = state.get("current_sub_questions", [])
        if not queries_to_run:
             queries_to_run = state.get("sub_questions", [])
        
        if not queries_to_run:
            queries_to_run = [state["query"]]

        documents = []
        # Initialize usage counters
        usage = {"tavily": 0, "wikipedia": 0, "arxiv": 0}
        
        for q in queries_to_run:
            print(f"Processing: {q}")
            
            # Explicit Tool Selection from Planner
            tool = "tavily" # Default
            search_query = q
            
            if q.startswith("[Wikipedia]"):
                tool = "wikipedia"
                search_query = q[11:].strip()
            elif q.startswith("[Arxiv]"):
                tool = "arxiv"
                search_query = q[7:].strip()
            elif q.startswith("[Tavily]"):
                tool = "tavily"
                search_query = q[8:].strip()
            
            # Fallback Smart Selection (if no prefix or legacy query)
            if tool == "tavily":
                q_lower = search_query.lower()
                if any(k in q_lower for k in ["history", "biography", "definition"]):
                    tool = "wikipedia"
                elif any(k in q_lower for k in ["physics", "math", "quantum", "paper"]):
                    tool = "arxiv"

            print(f"-> Routing to {tool.upper()}: {search_query}")
            
            # Increment Usage
            if tool in usage:
                usage[tool] += 1

            try:
                if tool == "wikipedia":
                    # Wiki run returns string, need to structure it
                    wiki_res = self.wikipedia.run(search_query)
                    if wiki_res:
                        documents.append({
                            "content": wiki_res,
                            "metadata": {"title": f"Wikipedia: {search_query}", "url": "wikipedia.org", "query": q}
                        })
                
                elif tool == "arxiv":
                    arxiv_res = self.arxiv.run(search_query)
                    if arxiv_res:
                         documents.append({
                            "content": arxiv_res,
                            "metadata": {"title": f"Arxiv: {search_query}", "url": "arxiv.org", "query": q}
                        })

                else: # Tavily
                    response = self.tavily.search(search_query, search_depth="advanced")
                    results = response.get("results", [])
                    for result in results:
                        documents.append({
                            "content": result.get("content"),
                            "metadata": {
                                "title": result.get("title"),
                                "url": result.get("url"),
                                "query": q
                            }
                        })
            except Exception as e:
                print(f"Error searching for {q}: {e}")

        print(f"Retrieved {len(documents)} new documents.")
        # Return documents and tool_usage
        return {"documents": documents, "tool_usage": usage, "stage": "synthesizing"}
