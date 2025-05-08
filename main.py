"""
Footprint-Any-Product - Main Entry Point

This script initializes the environment and starts the Uvicorn server
for the FastAPI application defined in the 'api' module.
"""

import uvicorn
import utils # For loading environment variables
from api.main import app # Import the FastAPI app instance

if __name__ == "__main__":
    # Load environment variables once at the start
    utils.load_environment()
    
    # Run the Uvicorn server
    # Use the same port as in the frontend configuration and api/main.py if specified there
    uvicorn.run(app, host="127.0.0.1", port=3005)
