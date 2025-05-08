from urllib.parse import urlparse
from firecrawl import FirecrawlApp
import os
import re
import utils
import requests
import base64
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage


utils.load_env()
api_key = os.environ["FIRECRAWL_API_KEY"]
image_link_regex = r"https?://\S+\.(?:jpg|jpeg|png|gif|svg)(?:\?[\w=&]*)?"
category_question = "In less than 10 words and ignoring the brand, what category of product does this detail page sell?"
image_question = '''Extract all image urls from the following markdown, making sure to avoid small icons and logos, and only include the images that pertain to the main product on the page, rather than images of recommended or similar products in other components of the page. Prefer larger images (over 1kb), prefer to be stricter and only keep 1-2 images with white-only backgrounds if possible, rather than keeping too many or images with complex backgrounds. Return the result as a space-delimited list of image_urls and nothing else.'''
llm = ChatOpenAI(model_name="gpt-4o-mini")

def trim_url(url):
    parsed = urlparse(url)
    return parsed.scheme + '://' + parsed.netloc + parsed.path

class PageAnalyzer:
    url = None
    markdown = None
    images = {}

    def __init__(self, url):
        self.url = trim_url(url)
        self._do_scrape()
        # self._check_or_scrape()

    def _do_scrape(self):
        # scrape the page
        self.markdown = FirecrawlApp(api_key=api_key).scrape_url(self.url, formats=['markdown']).markdown
        print(f"Scraped markdown for {self.url}")

        # extract the image urls
        image_urls_response = llm.invoke(f"{image_question} \n\n {self.markdown}").content
        self.images = dict([(image_url, None) for image_url in re.findall(image_link_regex, image_urls_response)])
        print(f"Extracted {len(self.images)} image urls from {self.url}")

    def query_markdown(self, question):
        return llm.invoke(f"{question} \n\n {self.markdown}").content
    
    def query_images(self, question):
        return llm.invoke([
            HumanMessage(content=[
                {"type": "text", "text": question},
                *[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}} for image in self.images.values()]
            ])]).content

    def _check_or_scrape(self):
        with utils.pool.connection() as conn:
            # Create table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pagemetadata (
                    url TEXT PRIMARY KEY,
                    markdown TEXT,
                    images TEXT[]
                )""")
            
            # Check if URL already exists
            with conn.cursor() as cur:
                cur.execute("SELECT url, markdown, images FROM pagemetadata WHERE url = %s", (self.url,))
                result = cur.fetchone()
                if not result:
                    self._do_scrape()
                    # Store document content and metadata separately
                    cur.execute(
                        "INSERT INTO pagemetadata (url, markdown, image_urls) VALUES (%s, %s, %s)",
                        (self.url, self.markdown, self.images.keys())
                    )
                else:
                    self.markdown = result[1]
                    self.images = dict([(image_url, None) for image_url in result[2]])

    def load_relevant_images(self):
        for image_url, image in self.images.items():
            if image is not None:
                continue
            try:                    
                # Download image
                response = requests.get(image_url)
                if response.status_code == 200:
                    self.images[image_url] = base64.b64encode(response.content).decode('utf-8')
            except Exception as e:
                print(f"Error processing image {image_url}: {str(e)}")
                continue

if __name__ == "__main__":
    url = "https://www.walmart.com/ip/Five-Star-1-Subject-7x5-Notebook-Green/5488604868?athcpid=5488604868&athpgid=AthenaItempage&athcgid=null&athznid=si&athieid=v0_eeMjEyLjg2LDY2NzAuNTYsMC4wMzE3MDkzNTMwMjk2OTg5NCwwLjVf&athstid=CS055~CS004&athguid=EmUu_FhMExkUy0XMpCa_SLyabAy10fZMsFd4&athancid=5349984957&athposb=0&athena=true&athbdg=L1600"
    pa = PageAnalyzer(url)

    print(pa.query_markdown("Where is this product is made. Be very very concise. Make sure you're not simply returning the brand of the product, but an actual location where it may have been manufactured. If that cannot be determined, return 'unknown'."))
    print(pa.query_markdown("Where is this product is shipping from. Be very very concise. Make sure you're not simply returning the brand of the product, but an actual location where it may be shipping from. If that cannot be determined, return 'unknown'."))

    print(pa.images.keys())
    pa.load_relevant_images()
    print(pa.query_images("Provide a very concise list of raw materials that appear to be inputs to this product including the percent of the total mass."))