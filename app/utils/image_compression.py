import os
from PIL import Image
import io

def compress_image(input_path: str, output_path: str, quality: int = 70, max_width: int = 1920) -> None:
    """
    Compresses an image from input_path and saves it to output_path.
    
    Args:
        input_path: Path to the original image (e.g., data/temp/photo.jpg)
        output_path: Path to save the compressed image (e.g., data/images/photo.jpg)
        quality: JPEG quality (1-100). 70-80 is usually a great balance.
        max_width: Maximum width in pixels. If image is wider, it gets resized.
    """
    try:
        # Open the image from the temp folder
        with Image.open(input_path) as img:
            # Convert to RGB to avoid issues with PNGs with transparency or CMYK images
            img = img.convert("RGB")
            
            # Resize if the width is greater than max_width
            width, height = img.size
            if width > max_width:
                new_height = int((max_width / width) * height)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Save the compressed image to the target folder
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            
        print(f"✅ Image compressed and saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Error compressing image: {e}")
        # Fallback: If compression fails, just copy the original file so data isn't lost
        os.replace(input_path, output_path)