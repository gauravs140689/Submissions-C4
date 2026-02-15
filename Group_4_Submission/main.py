import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from src.config import Config
from src.graph import create_graph
import argparse

def main():
    """
    Main entry point for the Multi-Agent AI Deep Researcher application.
    
    Loads configuration, sets up the agent graph, and executes the research loop based on the provided query.
    """
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Multi-Agent AI Deep Researcher")
    parser.add_argument("query", type=str, help="Research query")
    args = parser.parse_args()

    try:
        Config.validate()
        graph = create_graph()
        
        print(f"Starting research on: {args.query}")
        result = graph.invoke({
            "query": args.query, 
            "max_loops": Config.MAX_LOOPS,
            "loop_count": 0
        })
        
        print("\n--- FINAL REPORT ---\n")
        print(result["report"])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
