#!/usr/bin/env python3
"""
Image processing utilities for Screenshot LLM Assistant
"""

import io
import threading
from typing import Callable, Optional
from PIL import Image, ImageOps
from .logger import get_logger, log_exception

logger = get_logger(__name__)

class ImageProcessor:
    """Handles image processing operations like thumbnails and optimization"""
    
    def __init__(self):
        self.thumbnail_size = (200, 150)
        self.max_size = (1920, 1080)
        self.quality = 85
        
    def create_thumbnail(self, image_data: bytes) -> bytes:
        """Create a thumbnail from image data"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Create thumbnail
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.quality)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            log_exception(e, "Failed to create thumbnail")
            raise
    
    def optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image for display/transmission"""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
                image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Save optimized
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.quality, optimize=True)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            log_exception(e, "Failed to optimize image")
            raise
    
    def process_image_async(self, image_data: bytes, callback: Callable[[bytes], None], 
                          optimize: bool = True, thumbnail: bool = False):
        """Process image asynchronously and call callback with result"""
        def process():
            try:
                if thumbnail:
                    result = self.create_thumbnail(image_data)
                elif optimize:
                    result = self.optimize_image(image_data)
                else:
                    result = image_data
                
                callback(result)
                
            except Exception as e:
                log_exception(e, "Async image processing failed")
        
        thread = threading.Thread(target=process, daemon=True)
        thread.start()
    
    def get_image_dimensions(self, image_data: bytes) -> tuple:
        """Get image dimensions"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return image.size
        except Exception as e:
            log_exception(e, "Failed to get image dimensions")
            return (0, 0)
    
    def cleanup(self):
        """Cleanup resources"""
        # Nothing to cleanup for now
        pass

# Global instance
_image_processor = None

def get_image_processor() -> ImageProcessor:
    """Get the global image processor instance"""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor

if __name__ == "__main__":
    # Test the image processor
    processor = get_image_processor()
    logger.info("Image processor test successful")