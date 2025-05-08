import asyncio
from urllib.parse import urlparse
from firecrawl import FirecrawlApp
from typing import Dict, Any
from state import FootprintState
import os
import utils
import re
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI

utils.load_environment()
api_key = os.environ["FIRECRAWL_API_KEY"]
image_link_regex = r"https?://\S+\.(?:jpg|jpeg|png|gif|svg)(?:\?[\w=&]*)?"
image_question = '''Extract all image urls from the following markdown, making sure to avoid small icons and logos, and only include the images that pertain to the main product on the page, rather than images of recommended or similar products in other components of the page. Prefer larger images (over 1kb), prefer to be stricter and only keep 1-2 images with white-only backgrounds if possible, rather than keeping too many or images with complex backgrounds. Return the result as a space-delimited list of image_urls and nothing else.'''
brand_question = "What is the brand of the product in the markdown below? Return only the simple brand name, not a description of the product. Return just the brand, no other text."
category_question = "What is the category of the product in the markdown below, in very simple terms, that don't include the brand or very descriptive details? For example, a bike, t-shirt, office chair, or notebook, rather than something more specific like a blue notebook or an ergonomic office chair. Return just the category, no other text."
short_description_question = "What is a very brief description of the product in the markdown below? Return a single sentence, no more than 20 words, and make sure it actually describes the product and what it might be used for."
long_description_question = "Extract all product details in the markdown below that are relevant to the main product on this page. Ignore descriptions or details for secondary products like recommendations or related products."

llm = ChatOpenAI(model_name="gpt-4o-mini")

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