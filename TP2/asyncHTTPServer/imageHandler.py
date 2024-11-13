import aiohttp.web as web
import asyncio
import struct

from imageUtils.imageProcessor import ImageProcessor

class ImageHandler():  
    async def sendToMultiprocessingServer(self, imageData, scaleFactor):
        """Send the processed image to the scaling server and receive the resized image."""
        try:
             # Connect to the scaling server (IPv4: 127.0.0.1 on port 9090)
            reader, writer = await asyncio.open_connection('127.0.0.1', 9090)

            # Send the scale factor and the length of the image data
            writer.write(struct.pack("f", scaleFactor))
            writer.write(struct.pack("I", len(imageData)))
            writer.write(imageData)
            await writer.drain()

            # Receive the length of the resized image and its data
            dataLength = struct.unpack("I", await reader.readexactly(4))[0]
            resizedImageData = await reader.readexactly(dataLength)
            
            writer.close()
            await writer.wait_closed()
            
            return resizedImageData
     
        except Exception:
            raise # Reraise exception to be handled higher up
            
    
    async def handle(self, request):
        """Handle the image upload, grayscale conversion, and scaling operations"""
        reader = await request.multipart() # Read the multipart request (for image file upload)
        field = await reader.next() # Get the next field in the multipart form
        
        # Validate the uploaded file
        if field.name != 'file' or field.filename is None:
            return web.Response(status=400, text="Bad Request: Expected an image file upload.")
        
        # Check the file type (ensure it's JPG or PNG)
        content_type = field.headers.get('Content-Type', '').lower()
        if 'image/jpeg' not in content_type and 'image/png' not in content_type:
            return web.Response(status=400, text="Invalid file type. Only JPG and PNG are allowed.")
        
        # Read the image data into memory
        imageData = await field.read()
        imageProcessor = ImageProcessor()

        try:
            # Convert the image to grayscale
            grayImageData = await imageProcessor.imageToGrayscale(imageData)
            
            # Define the scale factor
            scaleFactor = 0.5
            
            # Send the grayscale image to the scaling server and get the resized image data
            resizedImageData = await self.sendToMultiprocessingServer(grayImageData, scaleFactor)
            
            # Return the resized image in the response
            response = web.Response(body=resizedImageData)
            response.content_type = 'image/png'
            return response
        except Exception as e:
            # Return an error response if anything goes wrong
            return web.Response(status=500, text=f"Internal Server Error: {str(e)}")