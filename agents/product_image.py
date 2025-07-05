import os
import hashlib
import aiohttp
import aiofiles
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Union
from pydantic import BaseModel, Field

class ProductImage(BaseModel):
    """
    Represents a product image with transparent caching.
    
    Stores the original URL and handles downloading/caching internally.
    External code should always use the original URL for references.
    """
    url: str = Field(description="Original image URL from the website")
    description: str = Field(default="", description="AI-generated description of the image for carbon footprint analysis")
    
    # Cache configuration
    _cache_dir: Path = Path("cache/images")
    
    def __init__(self, url: str, description: str = "", **kwargs):
        super().__init__(url=url, description=description, **kwargs)
        # Ensure cache directory exists
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self) -> Path:
        """Get cache path based on image URL hash."""
        url_hash = hashlib.blake2s(self.url.encode(), digest_size=16).hexdigest()
        parsed_url = urlparse(self.url)
        ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        return self._cache_dir / f"{url_hash}{ext}"
    
    def _find_cached_file(self) -> Optional[Path]:
        """Find cached file if it exists."""
        cache_path = self._get_cache_path()
        if cache_path.exists():
            return cache_path
        
        # Also check for any file with the same hash prefix (in case extension was different)
        url_hash = hashlib.blake2s(self.url.encode(), digest_size=16).hexdigest()
        for cache_file in self._cache_dir.glob(f"{url_hash}.*"):
            return cache_file
        
        return None
    
    def is_cached(self) -> bool:
        """Check if this image is already cached."""
        return self._find_cached_file() is not None
    
    async def get_image_path(self) -> str:
        """
        Get the path to the image file, downloading and caching if necessary.
        
        Returns:
            Path to the local image file (cached or original URL if download fails)
        """
        # Check if already cached
        cached_file = self._find_cached_file()
        if cached_file:
            print(f"Using cached image {self.url}, {cached_file}")
            return str(cached_file)
        
        # Download and cache
        cache_path = self._get_cache_path()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status == 200:
                        async with aiofiles.open(cache_path, 'wb') as f:
                            await f.write(await response.read())
                        return str(cache_path)
                    else:
                        print(f"Failed to download image {self.url}: {response.status}")
                        return self.url
        except Exception as e:
            print(f"Error downloading image {self.url}: {e}")
            return self.url
    
    async def get_image_data(self) -> Optional[bytes]:
        """
        Get the raw image data, downloading and caching if necessary.
        
        Returns:
            Image data as bytes, or None if unable to fetch
        """
        image_path = await self.get_image_path()
        
        # If we got back the original URL, it means download failed
        if image_path == self.url:
            return None
        
        try:
            async with aiofiles.open(image_path, 'rb') as f:
                return await f.read()
        except Exception as e:
            print(f"Error reading cached image {image_path}: {e}")
            return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization (only exposes original URL)."""
        return {
            "url": self.url,
            "description": self.description
        }
    
    @classmethod
    def format_images_for_prompt(cls, state: dict) -> str:
        """
        Format images for a prompt.
        """
        image_context = ""
        if state.get("product_images"):
            image_context = "\n\nAvailable Images:\n"
            for i, img in enumerate(state["product_images"]):
                image_context += f"Image {i+1}: {img.url}\nDescription: {img.description}\n\n"
        return image_context
    
    @classmethod
    async def download_all_images(cls, image_urls: list[str], descriptions: Optional[list[str]] = None) -> list['ProductImage']:
        """
        Create ProductImage objects and download/cache all images concurrently.
        
        Args:
            image_urls: List of original image URLs
            descriptions: Optional list of descriptions (defaults to empty strings)
            
        Returns:
            List of ProductImage objects with images cached
        """
        if descriptions is None:
            descriptions = [""] * len(image_urls)
        
        # Create ProductImage objects
        images = [cls(url=url, description=desc) for url, desc in zip(image_urls, descriptions)]
        
        # Download all images concurrently
        tasks = [img.get_image_path() for img in images]
        await asyncio.gather(*tasks)
        
        return images