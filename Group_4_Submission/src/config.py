import os
from dotenv import load_dotenv

# Try loading from .env, if that fails or keys missing, try config.env
if not load_dotenv(".env"):
    load_dotenv("config.env")
# Also explicitly try loading config.env to be sure if .env skipped
load_dotenv("config.env", override=True)

class Config:
    """
    Configuration class for the application.
    
    Loads environment variables and provides static access to configuration settings.
    """
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN")
    MAX_LOOPS = int(os.getenv("MAX_LOOPS", 1))
    # Default to a cost-effective powerful model, user can override in .env
    LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o") 
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    CONTRADICTION_THRESHOLD = float(os.getenv("CONTRADICTION_THRESHOLD", 0.9))
    MAX_SUB_QUESTIONS = 5
    
    # Local Config
    LOCAL_LLM_BASE_URL = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1233/v1")
    LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "openai/gpt-oss-20b")

    @staticmethod
    def validate():
        """
        Validates the presence of required environment variables.
        
        Raises:
            ValueError: If required API keys are missing.
        """
        if not Config.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is not set in environment variables")
        if not Config.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set in environment variables")
