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
    description: str = Field(default="", description="Description of the image")
    
    # Cache configuration
    _cache_dir: Path = Path("cache/markdown")
    
    def __init__(self, url: str, description: str = "", **kwargs):
        super().__init__(url=url, description=description, **kwargs)
        # Ensure cache directory exists
        self._cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_info(self, base_url: str, index: int) -> tuple[Path, str]:
        """Get cache directory and filename for this image."""
        hashed_url = hashlib.blake2s(base_url.encode(), digest_size=8).hexdigest()
        cache_subdir = self._cache_dir / hashed_url
        cache_subdir.mkdir(parents=True, exist_ok=True)
        
        # Get file extension from URL
        parsed_url = urlparse(self.url)
        ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
        
        image_hash = f"{hashed_url}_img_{index}"
        cache_filename = f"{image_hash}{ext}"
        
        return cache_subdir, cache_filename
    
    def _find_cached_file(self, base_url: str, index: int) -> Optional[Path]:
        """Find cached file if it exists."""
        cache_subdir, expected_filename = self._get_cache_info(base_url, index)
        cache_path = cache_subdir / expected_filename
        
        if cache_path.exists():
            return cache_path
        
        # Also check for any file with the same hash prefix (in case extension was different)
        hashed_url = hashlib.blake2s(base_url.encode(), digest_size=8).hexdigest()
        image_hash = f"{hashed_url}_img_{index}"
        
        for cache_file in cache_subdir.glob(f"{image_hash}.*"):
            return cache_file
        
        return None
    
    def is_cached(self, base_url: str, index: int) -> bool:
        """Check if this image is already cached."""
        return self._find_cached_file(base_url, index) is not None
    
    async def get_image_path(self, base_url: str, index: int) -> str:
        """
        Get the path to the image file, downloading and caching if necessary.
        
        Args:
            base_url: The base URL of the page (used for cache organization)
            index: The index of this image in the page's image list
            
        Returns:
            Path to the local image file (cached or original URL if download fails)
        """
        # Check if already cached
        cached_file = self._find_cached_file(base_url, index)
        if cached_file:
            print(f"Using cached image {self.url}, {cached_file}")
            return str(cached_file)
        
        # Download and cache
        cache_subdir, cache_filename = self._get_cache_info(base_url, index)
        cache_path = cache_subdir / cache_filename
        
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
    
    async def get_image_data(self, base_url: str, index: int) -> Optional[bytes]:
        """
        Get the raw image data, downloading and caching if necessary.
        
        Args:
            base_url: The base URL of the page (used for cache organization)
            index: The index of this image in the page's image list
            
        Returns:
            Image data as bytes, or None if unable to fetch
        """
        image_path = await self.get_image_path(base_url, index)
        
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
    async def download_all_images(cls, image_urls: list[str], base_url: str, descriptions: Optional[list[str]] = None) -> list['ProductImage']:
        """
        Create ProductImage objects and download/cache all images concurrently.
        
        Args:
            image_urls: List of original image URLs
            base_url: Base URL of the page
            descriptions: Optional list of descriptions (defaults to empty strings)
            
        Returns:
            List of ProductImage objects with images cached
        """
        if descriptions is None:
            descriptions = [""] * len(image_urls)
        
        # Create ProductImage objects
        images = [cls(url=url, description=desc) for url, desc in zip(image_urls, descriptions)]
        
        # Download all images concurrently
        tasks = [img.get_image_path(base_url, i) for i, img in enumerate(images)]
        await asyncio.gather(*tasks)
        
        return images