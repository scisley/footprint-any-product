# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Footprint-Any-Product is a sustainability analysis tool that evaluates the environmental impact of products based on their URL or name. The system uses a multi-agent architecture powered by LangGraph and LangChain to assess different aspects of a product's lifecycle (materials, manufacturing, packaging, transport, usage, and end-of-life) and provides an overall carbon footprint score.

## Repository Structure

- **Backend**: Python-based FastAPI service with LangGraph/LangChain workflow
  - Multi-agent system in `agents/` directory
  - Tools for calculations in `tools/` directory
  - State management in `state.py`
- **Frontend**: Next.js application with React 19 showing analysis results
  - UI components in `frontend/src/components/`
  - Page definitions in `frontend/src/app/`
  - Real-time streaming support via WebSockets
- **Notebooks**: Example implementations and sandbox environments in `notebooks/`

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

1. Navigate to the frontend directory:
   ```bash
   cd frontend
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

Start the Next.js development server with Turbopack:
```bash
cd frontend
pnpm dev --turbopack
```

Build the frontend:
```bash
cd frontend
pnpm build
```

Run linting:
```bash
cd frontend
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

1. User submits a product URL or name through the frontend
2. Backend processes the input through the agent system
3. Each agent performs specialized analysis using LangGraph
4. Results are streamed in real-time to the frontend via WebSockets
5. Frontend displays the carbon footprint score and detailed breakdown

### Key Components

- **State Management**: `state.py` defines the `FootprintState` TypedDict that contains all shared data between agents
- **Agent Definition**: Each agent in the `agents/` directory follows a similar pattern with a system prompt and LangGraph agent definition
- **Tools**: Reusable tools in the `tools/` directory, including:
  - `calculator.py`: Performs mathematical calculations
  - `emissions_factors.py`: Estimates carbon emissions for various processes
- **Frontend Components**:
  - `ProductInput.tsx`: Handles user input of product URLs or names
  - `StreamingText.tsx`: Manages WebSocket connections for real-time updates

### External APIs

The system uses the Muir API to fetch carbon footprint data:
- Requires `MUIR_API_KEY` environment variable
- Provides functions for getting and creating carbon footprint runs

## Technical Stack

- **Frontend**: 
  - React 19 with Next.js 15.3.2
  - Tailwind CSS 4
  - TypeScript
  - WebSocket for real-time streaming

- **Backend**:
  - FastAPI
  - LangGraph and LangChain for agent workflows
  - OpenAI models (gpt-4o)
  - PostgreSQL with pgvector for vector database
  - LangSmith for workflow monitoring