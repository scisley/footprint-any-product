import os
from pathlib import Path
from dotenv import load_dotenv

# --- Environment Setup ---

def load_environment():
    """Load environment variables from .env.local file."""
    dotenv_path = Path(__file__).parent / '.env.local'
    
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=True)
        print(f"Environment loaded from {dotenv_path}")
    else:
        print(f"Warning: .env.local file not found at {dotenv_path}")
    
    # Verify critical environment variables
    if os.environ.get('OPENAI_API_KEY'):
        print("OPENAI_API_KEY loaded successfully")
    else:
        print("Warning: OPENAI_API_KEY not found in environment variables")
