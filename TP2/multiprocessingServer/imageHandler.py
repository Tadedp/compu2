import socketserver
import struct
from multiprocessing import Pool
from imageUtils.imageProcessor import ImageProcessor
from PIL import Image

class ImageHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """Handles incoming requests for image resizing"""
        
        # Receive the scale factor (as a float)
        scaleFactor = struct.unpack("f", self.request.recv(4))[0]

        # Receive the length of the image data and then the actual image data
        dataLength = struct.unpack("I", self.request.recv(4))[0]
        imageData = self.request.recv(dataLength)
        
        # Create an ImageProcessor instance and use it to resize the image
        imageProcessor = ImageProcessor()
        
        # Resize the image using a Pool process
        with Pool() as pool:
            resizedImageData = pool.apply(imageProcessor.scaleImage, (imageData, scaleFactor))

        # Send back the length of the resized image data, followed by the image itself
        self.request.sendall(struct.pack("I", len(resizedImageData)))
        self.request.sendall(resizedImageData)
