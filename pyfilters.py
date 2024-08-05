import argparse
import multiprocessing
from PIL import Image
from scipy import ndimage

class InvalidValueException(Exception):
    pass

def split_image(image, num_parts, width, height):
    image_parts = []
    part_height = height // num_parts
    for i in range(num_parts):
        area = (0, i * part_height, width, (i * part_height) + part_height)
        image_part = image.crop(area)
        image_parts.append(image_part)
        
    return image_parts

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
    
    worker_pipe.send("Filter applied.")
    worker_pipe.close()
    
def coordinate_combine(pipes, shared_array, width, height, workers):
    for coordinator_pipe in pipes:
        coordinator_pipe.recv()
        coordinator_pipe.close()

    current_height = 0
    result_image = Image.new("RGB", (width, height)) 
    part_size_bytes = width * (height // len(workers)) * 3    
    for i in range(len(workers)):
        start = i * part_size_bytes
        end = start + part_size_bytes
        image_part = Image.frombytes("RGB", (width, height // len(workers)), bytes(shared_array[start:end]))   
        result_image.paste(image_part, (0, current_height))
        current_height += (height // len(workers))
        
    result_image.show()
    result_image.save("image.png")
    
def main(path, processes):
    image = Image.open(path)
    width = image.size[0]
    height = image.size[1]    
    image_parts = split_image(image, processes - 1, width, height)
        
    print("FILTERS")
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
    
    pipes = []    
    workers = []
    total_size_bytes = width * height * 3
    shared_array = multiprocessing.Array("B", total_size_bytes)
    part_size_bytes = width * (height // (processes - 1)) * 3
    
    for i in range(processes):
        if i < processes - 1:
            coordinator_pipe, worker_pipe = multiprocessing.Pipe()
            start = i * part_size_bytes
            end = start + part_size_bytes
            process = multiprocessing.Process(target=apply_filter, args=(image_parts[i], shared_array, start, end, filter_num, worker_pipe))
            workers.append(process)
            pipes.append(coordinator_pipe)
    
        else:    
            coordinator = multiprocessing.Process(target=coordinate_combine, args=(pipes, shared_array, width, height, workers))    
            coordinator.start()
        
    for process in workers:
        process.start()
        process.join()
    coordinator.join()

    image.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read and apply mathematical filters on an image.")
    parser.add_argument("path", type=str, help="Path of an image.")
    parser.add_argument("--processes", type=int, help="Number of processes.", default=multiprocessing.cpu_count())
    args = parser.parse_args()
    if args.processes < 2:
        print("Error: Invalid value. Processes cannot be less than 2.")
    else:
        if args.path:
            main(args.path, args.processes)
        else:
            print("Error: Invalid path.")