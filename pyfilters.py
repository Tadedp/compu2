import os
import signal
import functools
import argparse
import multiprocessing
from PIL import Image
from scipy import ndimage

class InvalidValueException(Exception):
    pass

"""
Handler function for SIGINT signal. 
Only lets the parent process execute the code.
Releases all resources and terminates worker and coordinator processes before exiting.
"""
def handler(coordinator, workers, coordinator_pipes, workers_pipes, images, parent_pid, sig, frame):
    if os.getppid() == parent_pid:
        pass
    else:    
        print("")
        print("Received signal SIGINT (" + str(sig) + ").")
        if len(workers) > 0:
            for process in workers:
                try:
                    os.kill(process.pid, signal.SIGKILL)
                except Exception:
                    continue
                
        if len(coordinator) > 0:
            try:
                os.kill(coordinator[0].pid, signal.SIGKILL)
            except Exception:
                pass
            
        if len(coordinator_pipes) > 0:
            for pipe in coordinator_pipes:
                try:
                    pipe.close()
                except Exception:
                    continue
                
        if len(workers_pipes) > 0:
            for pipe in workers_pipes:
                try:
                    pipe.close()
                except Exception:
                    pass
                
        if len(images) > 0:
            for image in images:
                image.close()
        
        print("Resources released. Exiting...")
        os._exit(os.EX_OK)
        
"""
Divides the original image into, depending on processes value, one or more horizontal rectangles.
Returns a list of all horizontal rectangles(image parts).  
"""
def split_image(image, num_parts, width, height):
    image_parts = []
    part_height = height // num_parts
    for i in range(num_parts):
        area = (0, i * part_height, width, (i * part_height) + part_height)
        image_part = image.crop(area)
        image_parts.append(image_part)
        
    return image_parts

"""
Applies the filter selected by the user to the corresponding part of the image.
Converts the image part into a sequence of bytes so that the shared memory can store it.
Notifies the coordinator process when the task has been completed through the pipe and closes it.  
"""
def apply_filter(image_part, shared_array, start, end, filter_num, worker_pipe):
    if filter_num == 1:
        shared_array[start:end] = ndimage.gaussian_filter(image_part, sigma=3).tobytes()
    
    elif filter_num == 2:
        shared_array[start:end] = ndimage.median_filter(image_part, size=3).tobytes()
    
    elif filter_num == 3:
        shared_array[start:end] = ndimage.sobel(image_part).tobytes()
    
    elif filter_num == 4:
        shared_array[start:end] = ndimage.laplace(image_part).tobytes()
    
    elif filter_num == 5:
        shared_array[start:end] = ndimage.prewitt(image_part).tobytes()
    
    try:
        worker_pipe.send("Filter applied.")
        worker_pipe.close()
    except Exception:
        pass
    
"""
Combines the processed image parts stored in shared memory by creating a new image and pasting 
the parts in order into it. 
Returns the image fully reconstructed.
"""   
def combine_parts(shared_array, width, height, num_parts):    
    current_height = 0
    result_image = Image.new("RGB", (width, height)) 
    part_size_bytes = width * (height // num_parts) * 3    
    
    for i in range(num_parts):
        start = i * part_size_bytes
        end = start + part_size_bytes
        image_part = Image.frombytes("RGB", (width, height // num_parts), bytes(shared_array[start:end]))   
        result_image.paste(image_part, (0, current_height))
        current_height += (height // num_parts)    
        
    return result_image

"""
Waits for the arrival of the messages from the worker processes notifying the completion of their tasks.
Calls combine_parts and saves the resulting image. 
Releases alredy used resources.
"""
def coordinate(pipes, shared_array, width, height, workers):
    for coordinator_pipe in pipes:
        try:
            coordinator_pipe.recv()
            coordinator_pipe.close()
        except Exception:
            pass
     
    result_image = combine_parts(shared_array, width, height, len(workers)) 
        
    result_image.show()
    result_image.save("image.png")
    result_image.close()
    
"""
Receives user inputs.
Opens the image and creates all the necessary processes (always one coordinator).
Creates the shared array so the processes can work. It's size is due to RGB, each pixel has
3 values (total number of pixels multiplied by 3).
Starts all processes and waits for their completion.
"""        
def main(path, processes):
    images = []
    workers = []
    workers_pipes = []
    coordinator_list = []
    coordinator_pipes = []   
    parent_pid = os.getpid() 
    pre_handler = functools.partial(handler, coordinator_list, workers, coordinator_pipes, workers_pipes, images, parent_pid) 
    signal.signal(signal.SIGINT, pre_handler)
    
    try:
        image = Image.open(path)
    except Exception:
        print("Error: Invalid path or file.")
        os._exit(os.EX_OK)
    
    images.append(image)
    width = image.size[0]
    height = image.size[1]    
    
    image_parts = split_image(image, processes - 1, width, height)
        
    print("------FILTERS------")
    print("1- Gaussian filter.")
    print("2- Median filter.")
    print("3- Sobel filter.")
    print("4- Laplace filter")
    print("5- Prewitt filter.")
    
    while True:
        try:    
            filter_num = int(input("Select a filter (1-5): "))
            if filter_num < 1 or filter_num > 5:
                raise InvalidValueException("Out of range(1-5)")
            else:
                break
        except Exception:
            print("Error: Invalid value. Enter an integer between 1 and 5.")    
    
    total_size_bytes = width * height * 3
    shared_array = multiprocessing.Array("B", total_size_bytes)
    part_size_bytes = width * (height // (processes - 1)) * 3
    
    for i in range(processes):
        if i < processes - 1:
            coordinator_pipe, worker_pipe = multiprocessing.Pipe()
            coordinator_pipes.append(coordinator_pipe)
            workers_pipes.append(worker_pipe)
            
            start = i * part_size_bytes
            end = start + part_size_bytes
            process = multiprocessing.Process(target=apply_filter, args=(image_parts[i], shared_array, start, end, filter_num, worker_pipe))
            workers.append(process)
            
        else:    
            coordinator = multiprocessing.Process(target=coordinate, args=(coordinator_pipes, shared_array, width, height, workers))    
            coordinator_list.append(coordinator)
            coordinator.start()
        
    for process in workers:
        process.start()
        
    for process in workers:
        process.join()
    coordinator.join()

    image.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read and apply mathematical filters on an image.")
    parser.add_argument("path", type=str, help="Path of an image.")
    parser.add_argument("--processes", type=int, help="Number of processes.", default=2)
    args = parser.parse_args()
    if args.processes < 2:
        print("Error: Invalid value. Processes cannot be less than 2.")
    else:
        main(args.path, args.processes)
        