# Carbon Thread

<p align="center">
  <img src="frontend/public/carbon-thread-logo.png" alt="Carbon Thread Logo" width="150">
</p>

Carbon Thread is a sustainability analysis tool that evaluates the environmental impact of products based on their URL or name. The system uses a multi-agent architecture powered by LangGraph and LangChain to assess different aspects of a product's lifecycle and provides an overall carbon footprint score.

## Setup

### Backend Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Environment Variables:
   - Talk to Steve about getting the project secrets
   - Create a free [LangSmith](https://www.langchain.com/langsmith) account
   - Create a free [Neon](https://neon.tech/) account
     - Access the project Steve shared with you and create a dev branch for yourself
     - Set the `DB_DEV_CONNECTION` environment variable to the connection string for your dev branch
   - Set the `MUIR_API_KEY` environment variable

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   pnpm install
   ```

## Running the Application

### Running the Backend

1. Start the FastAPI server:
   ```bash
   fastapi dev main.py
   ```
   The API will be available at http://localhost:8000

2. API Documentation:
   - OpenAPI UI: http://localhost:8000/docs
   - ReDoc UI: http://localhost:8000/redoc

3. Testing LangGraph Setup:
   ```bash
   jupyter notebook notebooks/examples/sandbox.ipynb
   ```

### Running the Frontend

1. Start the Next.js development server:
   ```bash
   cd frontend
   pnpm dev --turbopack
   ```
   The application will be available at http://localhost:3000

2. Building for production:
   ```bash
   cd frontend
   pnpm build
   pnpm start
   ```

3. Linting:
   ```bash
   cd frontend
   pnpm lint
   ```

## Architecture

Carbon Thread uses a multi-agent architecture to analyze different aspects of a product's lifecycle:
- Materials Analysis
- Manufacturing Process
- Packaging
- Transportation
- Usage
- End-of-Life

For more technical details, see the documentation in the `ai_docs/` directory.