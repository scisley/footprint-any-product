import base64
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from lca_core.utils.config import MODELS
from lca_core.agents.product_image import ProductImage
from langchain_core.runnables import RunnableConfig

async def analyze_image(product_image: ProductImage, analysis_prompt: str, model: str = "low") -> str:
    """
    Core image analysis function that works with a ProductImage.
    
    Args:
        product_image: ProductImage instance with cached image data
        analysis_prompt: Prompt describing what to analyze in the image
        model: Model configuration to use
        
    Returns:
        Analysis result as text
    """
    try:
        # Get image data from cache
        image_data = await product_image.get_image_data()
        if not image_data:
            return f"Could not load image data for {product_image.url}"
        
        # Convert to base64
        image_b64 = base64.b64encode(image_data).decode()
        
        # Determine MIME type based on file extension
        mime_type = "image/jpeg"  # Default
        if product_image.url.lower().endswith('.png'):
            mime_type = "image/png"
        elif product_image.url.lower().endswith('.webp'):
            mime_type = "image/webp"
        
        # Create multimodal message
        message_content = [
            {"type": "text", "text": analysis_prompt},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": image_b64
                }
            }
        ]
        
        # Analyze with vision model
        llm = MODELS[model]
        response = await llm.ainvoke([
            HumanMessage(content=message_content)
        ])
        
        return response.content.strip()
        
    except Exception as e:
        return f"Error analyzing image {product_image.url}: {str(e)}"

class AnalyzeImageToolSchema(BaseModel):
    """
    Analyzes an image according to a given prompt. For example, this can be used
    to analyze an image for the type of packaging, to estimate materials used,
    or to determine power requirements.
    """
    image_url: str = Field(description="The URL of the image to analyze")
    analysis_prompt: str = Field(description="The prompt describing what information to look for in the image")

@tool(args_schema=AnalyzeImageToolSchema)
async def analyze_image_tool(
    image_url: str, 
    analysis_prompt: str,
    config: RunnableConfig
) -> str:
    print(f"TOOL: Image Analysis for {image_url}, prompt: {analysis_prompt}")
    
    # Get model configuration
    model = config["configurable"].get("model", "low")
    
    # Find the ProductImage in state
    # product_images: List[ProductImage] = state.get("product_images", [])
    # target_image = None
    
    # for product_image in product_images:
    #     if product_image.url == image_url:
    #         target_image = product_image
    #         break
    target_image = ProductImage(url=image_url)
    
    if not target_image:
        return f"Image not found: {image_url}"
    
    # Use the core analysis function
    return await analyze_image(target_image, analysis_prompt, model)