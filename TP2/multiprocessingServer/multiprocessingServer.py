import socketserver

from multiprocessingServer.imageHandler import ImageHandler

class MultiprocessingServer(socketserver.TCPServer):
    # Allow reuse of the address to avoid binding issues when restarting
    allow_reuse_address = True

    def runServer(host="127.0.0.1", port=9090):
        """Run the scaling server on the specified host and port."""
        
        # Create an instance of the MultiprocessingServer with the ImageHandler
        with MultiprocessingServer((host, port), ImageHandler) as server:
            # Run the server indefinitely to handle incoming requests
            server.serve_forever()