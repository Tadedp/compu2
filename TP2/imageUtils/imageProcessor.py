from concurrent.futures import ThreadPoolExecutor
from asyncio import get_event_loop
from PIL import Image
from io import BytesIO

class ImageProcessor:
    async def imageToGrayscale(self, image_data):
        """Convert an image to grayscale asynchronously using a thread pool to avoid blocking the event loop."""
        loop = get_event_loop()
        
        # Run image processing in a separate thread to prevent blocking
        with ThreadPoolExecutor() as pool:
            # Open the image from bytes and convert to grayscale
            image = await loop.run_in_executor(pool, lambda: Image.open(BytesIO(image_data)).convert("L"))
            output = BytesIO()
            # Save the grayscale image to output as PNG
            await loop.run_in_executor(pool, lambda: image.save(output, format="PNG"))
        
        return output.getvalue()
    
    def scaleImage(self, imageData, scaleFactor):
        """Resize an image according to the given scale factor."""
        
        # Load the image from byte data
        image = Image.open(BytesIO(imageData))
        
        # Calculate the new dimensions based on the scaling factor
        width, height = image.size
        newWidth = int(width * scaleFactor)
        newHeight = int(height * scaleFactor)

        # Resize the image to the new dimensions
        resizedImage = image.resize((newWidth, newHeight))
        
        # Convert the resized image back to bytes to send back
        with BytesIO() as output:
            resizedImage.save(output, format="PNG")
            return output.getvalue()