import os
from PIL import Image
import io

def compress_image(input_path: str, output_path: str, quality: int = 70) -> None:
    try:
        # Open the image from the temp folder
        with Image.open(input_path) as img:
            # Convert to RGB to avoid issues with PNGs with transparency or CMYK images
            img = img.convert("RGB")
            
            # Resize if the width is greater than max_width
            width, height = img.size
            
            # Save the compressed image to the target folder
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            
        print(f"✅ Image compressed and saved to {output_path}")
        
    except Exception as e:
        print(f"❌ Error compressing image: {e}")
        # Fallback: If compression fails, just copy the original file so data isn't lost
        os.replace(input_path, output_path)