import asyncio
import os
import re
import yaml
from urllib.parse import urlparse
from firecrawl import FirecrawlApp
from typing import Dict, Any
from .state import FootprintState
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from pathlib import Path

api_key = os.environ["FIRECRAWL_API_KEY"]
image_link_regex = r"https?://\S+\.(?:jpg|jpeg|png|gif|svg)(?:\?[\w=&]*)?"

# Load prompts from YAML
_PROMPTS_FILE = Path(__file__).parent / "prompts.yaml"
with open(_PROMPTS_FILE, 'r') as f:
    _prompts_data = yaml.safe_load(f)

image_question = _prompts_data['page_analysis_image_question']
brand_question = _prompts_data['page_analysis_brand_question']
category_question = _prompts_data['page_analysis_category_question']
short_description_question = _prompts_data['page_analysis_short_description_question']
long_description_question = _prompts_data['page_analysis_long_description_question']

llm = ChatOpenAI(model_name="gpt-4.1-2025-04-14")

def trim_url(url):
    parsed = urlparse(url)
    return parsed.scheme + '://' + parsed.netloc + parsed.path

def query_markdown(markdown, question):
    return llm.invoke(f"{question} \n\n {markdown}").content

def query_images(question, images):
    return llm.invoke([
        HumanMessage(content=[
            {"type": "text", "text": question},
            *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}} for image in images.values()]
        ])]).content


async def page_analysis_phase(state: FootprintState) -> Dict[str, Any]:
    """
    Analyzes the product URL using PageAnalyzer to extract initial product details.
    """
    await asyncio.sleep(0.1) # Small delay for streaming appearance
    
    # Scrape the markdown
    product_url = trim_url(state["url"])
    state['url'] = product_url
    markdown = FirecrawlApp(api_key=api_key).scrape_url(product_url, formats=['markdown']).markdown
    print(f"Scraped markdown for {product_url}")

    # Extract images
    image_urls_response = llm.invoke(f"{image_question} \n\n {markdown}").content
    images = dict([(image_url, None) for image_url in re.findall(image_link_regex, image_urls_response)])
    print(f"Extracted {len(images)} image urls from {product_url}")

    # Extracted data
    brand = query_markdown(markdown, brand_question)
    category = query_markdown(markdown, category_question)
    short_description = query_markdown(markdown, short_description_question)
    long_description = query_markdown(markdown, long_description_question)
    
    return {
        "url": product_url,
        "product_image_urls": list(images.keys()),
        "brand": brand,
        "category": category,
        "short_description": short_description,
        "long_description": long_description,
        "messages": state.get("messages", []) + [ # Append to existing messages
            {"role": "ai", "content": f"Page analysis complete for {product_url}. Brand: {brand}, Category: {category}."}
        ]
    }
