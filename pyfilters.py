import argparse
import multiprocessing
import matplotlib.pyplot as plt
from PIL import Image
from scipy import ndimage

class InvalidValueException(Exception):
    pass

def split_image(image, processes):
    image_parts = []
    width = int(image.size[0] / processes)
    height = int(image.size[1])    
    
    for i in range(processes):
        area = (i*width, 0, (i*width) + width, height)
        #print(area)
        #print("Tamaño: " + str(image.size))
        image_part = image.crop(area)
        image_parts.append(image_part)
    
    return image_parts

def apply_filter(image_part, filter_num):
    if filter_num == 1:
        return ndimage.gaussian_filter(image_part, sigma=3)
    elif filter_num == 2:
        return ndimage.median_filter(image_part, size=3)
    elif filter_num == 3:
        return ndimage.sobel(image_part)
    elif filter_num == 4:
        return ndimage.laplace(image_part)
    elif filter_num == 5:
        return ndimage.prewitt(image_part)
    
    plt.imshow(image_part)
    plt.axis("off")
    plt.show()    
    
def main(path, processes):
    image = Image.open(path)
    image_parts = split_image(image, processes)
    
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
            
    workers = []    
    for i in range(processes):
        process = multiprocessing.Process(target=apply_filter, args=(image_parts[i], filter_num))    
        workers.append(process)
        process.start()
    
    for process in workers:
        process.join()
    
    image.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read and apply mathematical filters on an image.")
    parser.add_argument("path", type=str, help="Path of an image.")
    parser.add_argument("--processes", type=int, help="Number of processes.", default=multiprocessing.cpu_count())
    args = parser.parse_args()
    main(args.path, args.processes)