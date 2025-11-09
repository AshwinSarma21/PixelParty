#!/usr/bin/env python
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import time
import numpy as np
import threading
from multiprocessing import Process,Queue,Pipe

mutex = threading.Lock()
        
image_array = np.array([[(0,0,0) for _ in range(64)] for _ in range(64)])


class SimpleSquare(object):
    def __init__(self):
        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        #options.show_refresh_rate = 1
        options.gpio_slowdown = 2
        self.matrix = RGBMatrix(options = options)

    def usleep(self, value):
        time.sleep(value / 1000000.0)


    def mainloop(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        
        while True:
            for y in range(0, offset_canvas.height):
                for x in range(0, offset_canvas.width):
                    r, g, b = image_array[x,y]
                    offset_canvas.SetPixel(x, y,int(r),int(g),int(b))
            offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
    
    def run(self):
        t1 = threading.Thread(target=self.mainloop)
        t1.start()

def receiveUpdate(pipeR):
    while True:
        global image_array
        #receive and store data over pipe
        x, y, color = pipeR.recv()
        with mutex:
            #crit section: check what we received from pipe and act accordingly
            if x == -1: #x == -1 denotes clearing the matrix
                image_array = np.array([[(0,0,0) for _ in range(64)] for _ in range(64)])
            else:#just update the changed pixels in the array
                image_array[x,y] = color

def led_process(pipeR):
    print("starting LED control")
    simple_square = SimpleSquare()
    simple_square.run()
    threading.Thread(target=receiveUpdate, args=(pipeR,)).start()
    

# Main function
if __name__ == "__main__":

    fart, poop = Pipe()
    led_process(poop)
