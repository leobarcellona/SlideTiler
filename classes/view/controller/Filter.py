import math

import time
import os
from multiprocessing import Pool
import tensorflow as tf
import sys
import threading
from tqdm import tqdm

#os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

if tf.test.gpu_device_name():
    print('GPU found')
else:
    print("No GPU found")

from skimage.filters import edges

from stardist.models import StarDist2D
from stardist.plot import render_label
from csbdeep.utils import normalize
import numpy as np
import matplotlib.pyplot as plt


'''
Class that filter the tiles. Now it filters using stardist. Could be expanded with other functionalities 
'''

class Filter:
    def __init__(self, image=None):
        self.image = image
        self.model = StarDist2D.from_pretrained('2D_versatile_he')

    def stardist(self):
        start = time.time()
        #pool = Pool(24)
        step_size = 1000
        threads = 10
        t_list = []
        height = int(73728 / 6)
        width = int(69632 / 6)
        step_h = height/step_size
        step_w = width/step_size

        steps = int(step_h * step_w)
        print("steps: ", steps, " w: ", step_w, "h", step_h)

        curr_image = self.image.read_region((0, 0), 0, (width, height))
        curr_image = np.asarray(curr_image)
        #labels, _ = self.model.predict_instances(normalize(curr_image[:, :, :3]))
        to_segment = normalize(curr_image[:, :, :3])
        labels, _ = self.model.predict_instances(to_segment, n_tiles=self.model._guess_n_tiles(to_segment))

        plt.subplot(1, 3, 1)
        plt.imshow(curr_image)
        plt.axis("off")
        plt.title("input image")

        plt.subplot(1, 3, 2)
        plt.imshow(render_label(labels, img=curr_image))
        plt.axis("off")
        plt.title("prediction + input overlay")

        plt.subplot(1, 3, 3)
        plt.imshow(render_label(labels))
        plt.axis("off")
        plt.title("prediction")
        plt.show(block=True)

        end = time.time()
        print("elapsed_time")
        print(end - start)

    def compute_roi_segmentation(self, roi_slice, width, height):
        curr_image = np.asarray(roi_slice)
        print(height)
        print(width)
        labels = np.zeros((height, width))
        to_segment = normalize(curr_image[:, :, :3])

        step_size = 1024
        threads = 4
        t_list = []
        step_h = math.ceil(height / step_size)
        step_w = math.ceil(width / step_size)

        steps = int(step_h * step_w)
        if steps < 4:
            threads = 1
        print("steps: ", steps, " w: ", step_w, "h", step_h)

        for val in range(threads):
            t_list.append(threading.Thread(target=self.execute_test, args=(to_segment, self.model, val, step_w, steps, step_size, threads, labels, )))
            t_list[-1].start()

        for i in range(len(t_list)):
            t_list[i].join()

        return labels

    def filter_roi(self, roi, roi_slice, width, height, min_w, min_h, ratio):
        segmentation = roi.get_segmentation()
        if len(segmentation) == 0:
            segmentation = self.compute_roi_segmentation(roi_slice, width, height)
            roi.set_segmentation(segmentation)

        size = roi.get_tile_size()
        tiles = roi.get_tiles()
        remove_tiles = np.zeros(tiles.shape)

        coordinates = np.nonzero(tiles)

        for i in range(len(coordinates[0])):
            y = int((coordinates[1][i]) * size - min_h)
            x = int(coordinates[0][i] * size - min_w)

            cell = segmentation[y:y+size, x:x+size]
            black = cell == 0

            cell_proportion = 1 - np.count_nonzero(black) / (cell.shape[0] * cell.shape[1])

            if cell_proportion < ratio:
                remove_tiles[coordinates[0][i], coordinates[1][i]] = 1

        return remove_tiles

    @staticmethod
    def execute_test(image, model, id, steps_w, steps, step_s, threads, full_image):
        # steps per ogni thread
        th_steps = int(steps / threads)

        #step di partenza
        start_step = id * th_steps
        print(start_step)
        #per ogni step
        for j, v in tqdm(enumerate(range(th_steps))):
            #calcola step del thread
            i = start_step + j

            #calcola posizione nell'immagine
            h = int(i / steps_w)
            w = int(i - h * steps_w)

            print("cell_dimensions")
            print("w: ", w * step_s)
            print("h: ", h * step_s)
            cell = image[h * step_s:h * step_s + step_s, w * step_s: w * step_s + step_s, :]

            #print(cell.shape)
            lab, _ = model.predict_instances(cell, show_tile_progress=False)
            full_image[h * step_s : h * step_s + step_s, w * step_s : w * step_s + step_s] = lab

        curr_image = 0
