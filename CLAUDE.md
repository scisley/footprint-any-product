# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Footprint-Any-Product is a sustainability analysis tool that evaluates the environmental impact of products based on their URL. The system uses a multi-agent architecture powered by LangGraph and LangChain to assess different aspects of a product's lifecycle (materials, manufacturing, packaging, transport, usage, and end-of-life) and provides an overall carbon footprint score.

## Repository Structure

- **Backend**: Python-based FastAPI service with LangGraph/LangChain workflow
- **Frontend**: Next.js application with React 19 showing analysis results
- **Notebooks**: Example implementations and sandbox environments

## Setup Instructions

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
   - Get project secrets from Steve
   - Create accounts for LangSmith and Neon
   - Access the Neon project shared by Steve and create a dev branch
   - Set the `DB_DEV_CONNECTION` environment variable
   - Set the `MUIR_API_KEY` environment variable

### Frontend Setup

1. Navigate to the frontend Next.js project:
   ```bash
   cd frontend/footprint-any-product
   ```

2. Install dependencies (using pnpm):
   ```bash
   pnpm install
   ```

## Development Commands

### Backend

Start the FastAPI server:
```bash
fastapi dev main.py
```

Run the sandbox notebook to test LangGraph setup:
```bash
jupyter notebook notebooks/examples/sandbox.ipynb
```

### Frontend

Start the Next.js development server:
```bash
cd frontend/footprint-any-product
pnpm dev
```

Build the frontend:
```bash
cd frontend/footprint-any-product
pnpm build
```

Run linting:
```bash
cd frontend/footprint-any-product
pnpm lint
```

## Architecture

### Agent-Based System

The project uses a multi-agent architecture to analyze different aspects of a product:

1. **Materials Agent**: Analyzes product materials and their environmental impact
2. **Manufacturing Agent**: Evaluates energy sources and manufacturing processes
3. **Packaging Agent**: Analyzes product packaging materials and design
4. **Transport Agent**: Analyzes transportation methods and distances
5. **Lifecycle Use Agent**: Analyzes energy consumption during product use
6. **End-of-Life Agent**: Analyzes end-of-life handling and recycling potential
7. **Summary Agent**: Provides consolidated environmental impact assessment

### Data Flow

1. User submits a product URL through the frontend
2. Backend processes the URL through the agent system
3. Each agent performs specialized analysis
4. Results are consolidated and returned to the frontend
5. Frontend displays the carbon footprint score and detailed breakdown

### External APIs

The system uses the Muir API to fetch carbon footprint data:
- API Client: `frontend/muir_api_client.py`
- Requires `MUIR_API_KEY` environment variable
- Provides functions for getting and creating carbon footprint runs

## Technical Notes

- The frontend uses React 19 with Next.js 15 and Tailwind CSS
- The backend uses FastAPI with LangGraph and LangChain
- The project uses PostgreSQL with pgvector for vector database functionality
- LangSmith is used for workflow monitoring and debugging