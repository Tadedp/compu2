import aiohttp.web as web

from asyncHTTPServer.imageHandler import ImageHandler

class AsyncHTTPServer():
    async def create_app(self):
        """Creates and configures the asynchronous web application"""
        
        # Create an instance of the ImageHandler to process image data
        imageHandler = ImageHandler()
        
        # Initialize the web application
        app = web.Application()
        
        # Define the route and associate it with the image handler's `handle` method
        app.router.add_post('/upload', imageHandler.handle)
        return app


    

    
    
        