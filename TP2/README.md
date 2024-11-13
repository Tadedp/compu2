# Application Setup and Running Guide

This application allows you to process **only** PNG and JPG images by converting them to grayscale using an asynchronous HTTP server and resizing them using a multiprocessing server.

## Dependencies

The application depends on the following libraries:

- Pillow (version 11.0.0): for image manipulation and processing.
- aiohttp (version 3.10.10): for handling HTTP requests asynchronously.

## Installing Dependencies

You can install the necessary dependencies using pip and a requirements.txt file. by running:

```
pip install -r requirements.txt
```

## Usage

To run the application, follow these steps:

- From the terminal, navigate to the directory containing the main.py file and run the following command changing ip (IPv4 or IPv6) and port values as desired to run both the asynchronous HTTP server and the multiprocessing server in the background:

```
python tp2.py --ip 127.0.0.1 --port 8080
```

- Once the application is running, you can access the image upload and processing functionality by running the following command changing both input file and output png paths as desired (Windows example):

```
curl -F "file=@C:\Users\yourUser\Desktop\example.jpg" http://127.0.0.1:8080/upload -o C:\Users\yourUser\Desktop\gray_example.png
```

## Stopping the Application

To stop the application, you can press Ctrl + C in the terminal where it is running. This will send an interrupt signal (SIGINT), which will stop both servers.

## Authors
 
 - Tadeo Drube - _Developer_ - [Tadedp](https://github.com/Tadedp)  