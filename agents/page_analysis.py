import os
import json
from pathlib import Path
from urllib.parse import urlparse
from firecrawl import FirecrawlApp
from typing import Dict, Any
from .state import FootprintState
from .product_image import ProductImage
from langchain.schema import HumanMessage
from langchain_core.runnables import RunnableConfig
from api.config import MODELS, get_prompt
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
import hashlib

# Create cache directory if it doesn't exist
CACHE_DIR = Path("cache/markdown")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

api_key = os.environ["FIRECRAWL_API_KEY"]
sys_prompt = get_prompt('page_analysis_sys_prompt')

class PageDetails(BaseModel):
    brand: str = Field(description=get_prompt('page_analysis_brand_question'))
    images: list[str] = Field(description=get_prompt('page_analysis_image_question'))
    category: str = Field(description=get_prompt('page_analysis_category_question'))
    short_description: str = Field(description=get_prompt('page_analysis_short_description_question'))
    long_description: str = Field(description=get_prompt('page_analysis_long_description_question'))


async def page_analysis_phase(state: FootprintState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Analyzes the product URL using PageAnalyzer to extract initial product details.
    """

    model = config["configurable"].get("model", "low")
    llm = MODELS[model].with_structured_output(PageDetails)

    def trim_url(url):
        parsed = urlparse(url)
        return parsed.scheme + '://' + parsed.netloc + parsed.path

    # Scrape the markdown
    product_url = trim_url(state["url"])
    markdown = get_page_markdown(product_url)

    response: PageDetails = llm.invoke([
        SystemMessage(sys_prompt),
        HumanMessage(markdown)
    ])
    
    # Limit product images to the first 10
    image_urls = response.images[:10]
    
    # Create ProductImage objects and download/cache all images
    product_images = await ProductImage.download_all_images(image_urls, product_url)

    return {
        "product_images": product_images,
        "brand": response.brand,
        "category": response.category,
        "short_description": response.short_description,
        "long_description": response.long_description,
        "messages": [
            {"role": "ai", "content": f"Page analysis complete for {product_url}. Brand: {response.brand}, Category: {response.category}."}
        ]
    }

def hash_url(url: str) -> str:
    return hashlib.blake2s(url.encode(), digest_size=8).hexdigest()

def get_cached_markdown(url: str) -> str:
    """
    Get cached markdown content for a URL if it exists.
    Returns None if no cache exists.
    """
    hashed_url = hash_url(url)
    cache_file = CACHE_DIR / hashed_url / f"{hashed_url}.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            print(f"Using cached markdown for {url}, {cache_file}")
            return json.load(f)['markdown']
    return None

def cache_markdown(url: str, markdown: str) -> None:
    """
    Cache markdown content for a URL.
    """
    hashed_url = hash_url(url)
    cache_file = CACHE_DIR / hashed_url / f"{hashed_url}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump({'url': url, 'markdown': markdown}, f)

def get_page_markdown(url: str, use_cache: bool = True) -> str:
    """
    Get the markdown for a product page.
    If use_cache is True, will try to get from cache first.
    If not in cache or use_cache is False, will scrape and cache the result.
    """
    if use_cache:
        cached = get_cached_markdown(url)
        if cached is not None:
            return cached
    print(f"Scraping {url}")
    markdown = FirecrawlApp(api_key=api_key).scrape_url(url, formats=['markdown']).markdown
    cache_markdown(url, markdown)
    return markdown

