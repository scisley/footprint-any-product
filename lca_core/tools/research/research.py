from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_perplexity import ChatPerplexity
from langchain_core.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger(__name__)

async def research_topic(topic: str, model_config: str = "low") -> str:
    """
    Core research function that uses Perplexity to research a topic and return answers with citations.
    
    Args:
        topic: The topic or question to research
        model_config: Model configuration (not used for Perplexity, kept for consistency)
        
    Returns:
        Research result with citations as text
    """
        
    # Initialize Perplexity chat model
    chat = ChatPerplexity(
        temperature=0,
        # See https://docs.perplexity.ai/models/models/sonar
        model="sonar" if model_config == "low" else "sonar-pro"
    )
    
    # Create research prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research assistant. Provide succinct, accurate information with citations. Focus on factual data relevant to environmental impact analysis."),
        ("human", "Research the following topic and provide a succinct answer with citations: {topic}")
    ])
    
    # Create chain and invoke
    chain = prompt | chat
    response = await chain.ainvoke({"topic": topic})
    citations = response.additional_kwargs.get('citations', [])
    
    # Format citations with numbers
    formatted_citations = []
    for i, citation in enumerate(citations, 1):
        formatted_citations.append(f"[{i}] {citation}")
    
    answer = response.content.strip()
    if len(formatted_citations) > 0:
        answer += "\n\nCitations:\n" + "\n".join(formatted_citations)

    return answer

class ResearchToolSchema(BaseModel):
    """
    Researches a topic and returns succinct information with citations. This
    tool can be used to gather current information about materials,
    manufacturing processes, industry standards, where products are made, etc.
    Make sure to provide enough detail to avoid ambiguity. For example, if
    asking about a brand, provide the product category to help disambiguate.
    """
    topic: str = Field(description="The question to research. Be specific for better results.")

@tool(args_schema=ResearchToolSchema)
async def research_tool(
    topic: str,
    config: RunnableConfig
) -> str:
    print(f"TOOL: Research for topic: {topic}")
    
    # Get model configuration (not used for Perplexity but kept for consistency)
    model = config["configurable"].get("model", "low")
    
    # Use the core research function
    return await research_topic(topic, model)