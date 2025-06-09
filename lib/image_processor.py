from PIL import Image
import io
from typing import Tuple, Optional
import threading
from concurrent.futures import ThreadPoolExecutor
from .logger import get_logger

logger = get_logger()

class ImageProcessor:
    """Handles efficient image processing and optimization"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._cache = {}  # Simple memory cache for thumbnails
        
    def optimize_image(self, 
                      image_data: bytes, 
                      max_size: Tuple[int, int] = (800, 800),
                      quality: int = 85) -> bytes:
        """
        Optimize an image for sending to LLM API
        - Resizes if larger than max_size
        - Compresses to reduce file size
        - Maintains aspect ratio
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Check if resize needed
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            image.save(output, 
                      format='JPEG', 
                      quality=quality, 
                      optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.log_exception(e, "Failed to optimize image")
            return image_data  # Return original if optimization fails

    def create_thumbnail(self, 
                        image_data: bytes,
                        size: Tuple[int, int] = (200, 200)) -> bytes:
        """
        Create a thumbnail asynchronously
        Returns cached thumbnail if available
        """
        # Check cache
        cache_key = hash(image_data)
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            output = io.BytesIO()
            image.save(output, 
                      format='JPEG',
                      quality=85,
                      optimize=True)
            
            thumbnail_data = output.getvalue()
            
            # Cache thumbnail
            self._cache[cache_key] = thumbnail_data
            
            return thumbnail_data
            
        except Exception as e:
            logger.log_exception(e, "Failed to create thumbnail")
            return image_data

    def process_image_async(self, 
                          image_data: bytes,
                          callback: callable,
                          optimize: bool = True,
                          thumbnail: bool = False) -> None:
        """
        Process an image asynchronously with optimization and/or thumbnailing
        Calls the callback with the processed image data when complete
        """
        def _process():
            try:
                result = image_data
                
                if optimize:
                    result = self.optimize_image(result)
                    
                if thumbnail:
                    result = self.create_thumbnail(result)
                    
                callback(result)
                
            except Exception as e:
                logger.log_exception(e, "Failed to process image asynchronously")
                callback(image_data)  # Return original on error
                
        self.executor.submit(_process)

    def clear_cache(self):
        """Clear the thumbnail cache"""
        self._cache.clear()

    def cleanup(self):
        """Clean up resources"""
        self.executor.shutdown(wait=False)
        self.clear_cache()

# Global image processor instance
_image_processor: Optional[ImageProcessor] = None

def get_image_processor() -> ImageProcessor:
    """Get or create the global image processor instance"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor