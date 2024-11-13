import aiohttp.web as web
from ipaddress import ip_address
import asyncio
import signal
import os
import socket
from multiprocessing import Process
from argparse import ArgumentParser

from asyncHTTPServer.asyncHTTPServer import AsyncHTTPServer
from multiprocessingServer.multiprocessingServer import MultiprocessingServer

def handler(sig, frame):
    """Handles SIGINT signal to stop both servers in the correct order."""
    print("\nReceived signal SIGINT (" + str(sig) + ").")
    print("\nStopping servers...")
    
    global multiprocessingServerProcess
    
    # Stop the multiprocessing server first
    if multiprocessingServerProcess is not None:
        multiprocessingServerProcess.terminate()
        multiprocessingServerProcess.join()
        
    # Stop the HTTP server loop
    loop = asyncio.get_running_loop()
    loop.stop() 
    print("Servers stopped. Exiting...")
    os._exit(0)

def main(host, port):
    global multiprocessingServerProcess
     
    # Start the multiprocessing server in a separate process
    multiprocessingServerProcess = Process(target=MultiprocessingServer.runServer)
    multiprocessingServerProcess.start()
    
    try:
        # Start the asynchronous HTTP server
        asyncHTTPServer = AsyncHTTPServer()
        app = asyncio.run(asyncHTTPServer.create_app())
        web.run_app(app, host=host, port=port)
        
    except Exception:
        print("Fatal Error: HTTP server failed. Exiting...")
        multiprocessingServerProcess.terminate()
        multiprocessingServerProcess.join()
        os._exit(0)

    finally:
        # Stop the multiprocessing server
        if multiprocessingServerProcess is not None:
            multiprocessingServerProcess.terminate()
            multiprocessingServerProcess.join()
        
if __name__ == "__main__":
    # Set up the signal handler for SIGINT
    signal.signal(signal.SIGINT, handler)
    
    # Argument parser for IP address and port options
    parser = ArgumentParser(description="Process images by converting them to grayscale and compressing them.")
    parser.add_argument("-i", "--ip", type=str, required=True, help="listening IP address")
    parser.add_argument("-p", "--port", type=int, required=True, help="listening port")
    args = parser.parse_args()
    
    try:
        # Validate IP address
        ip_address(args.ip)
        
        # Check if the IP address is IPv4 or IPv6 and set the correct socket family
        try:
            socket.inet_pton(socket.AF_INET, args.ip)  # Check if it's IPv4
            ip_family = socket.AF_INET
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, args.ip)  # Check if it's IPv6
                ip_family = socket.AF_INET6
            except socket.error:
                raise ValueError("Invalid IP address format")
        
        # Validate the port number (1-65535)
        if 1 <= args.port <= 65535:
            with socket.socket(ip_family, socket.SOCK_STREAM) as s:
                s.bind((args.ip, args.port))
        else:
            raise OSError
        
        main(args.ip, args.port)
    except ValueError:
        print("Error: Invalid IP address.")
        os._exit(1)
    except OSError:
        print("Error: Invalid port.")
        os._exit(1)