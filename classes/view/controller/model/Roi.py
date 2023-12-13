import numpy as np
from shapely.geometry import Polygon, box, Point
import matplotlib.pyplot as plt

'''
Class representing a ROI. 
it contains a set of points delimiting the region and the tiles generated.
The points are stored in a List
The tiles are stored in a numpy array with dimension computed considering the resolution and the tiles size.
A flag keep the track of closure of the ROI
'''

class Roi:
    def __init__(self, identifier):
        self.id = identifier # ROI identifier

        self.points = [] # Points of the region
        self.tiles = None # array of the tiles
        self.tiles_layer = 0 # layer of generation
        self.tile_size = np.zeros(2) #size of the tiles
        self.ratio = 1

        self.closed_flag = False

        self.annotation = [0, "None", "#00000d"] # annotation of the ROI (default None and black)
        self.segmentation = []

    '''
    getter and setter
    '''
    def get_id(self):
        return self.id

    def get_tiles(self):
        return self.tiles

    def set_tiles(self, tiles):
        self.tiles = tiles

    def get_roi(self):
        return self.points

    def get_tiles_layer(self):
        return self.tiles_layer

    def set_tiles_layer(self, layer):
        self.tiles_layer = layer

    def get_tile_size(self):
        return self.tile_size

    def set_tile_size(self, size):
        self.tile_size = size

    def get_ratio(self):
        return self.ratio

    def set_roi(self, points):
        self.points = points
        self.segmentation = []

    def set_segmentation(self, seg):
        self.segmentation = seg

    def get_segmentation(self):
        return self.segmentation

    def get_boundaries(self):
        polygon_points = np.array(self.points)

        # get max an min polygon coordinates
        max_coord = np.max(polygon_points, axis=0)
        min_coord = np.min(polygon_points, axis=0)

        return min_coord, max_coord

    def set_annotation(self, id, name, color):
        self.annotation = [id, name, color]

    def get_annotation(self):
        return self.annotation

    '''
    Functions to check the state
    '''
    def is_closed(self):
        return self.closed_flag

    def is_inside(self, point):
        roi_polygon = Polygon(self.points)
        return roi_polygon.contains(Point(point[1], point[0]))

    '''
    Functions to manage the ROI
    '''

    def add_point(self, point):
        if self.points is None:
            self.points = []

        if self.closed_flag:
            return False

        self.points.append([point[1], point[0]])
        self.segmentation = []

        return True

    def change_point(self, index, point):
        self.segmentation = []
        if (index % 2) == 0:
            self.points[int(index / 2)] = [point[1], point[0]]
            return index
        else:
            new_pos = int(index / 2) + 1
            new_list = []
            for e in self.points[:new_pos]:
                new_list.append(e)
            new_list.append([point[1], point[0]])
            for e in self.points[new_pos:]:
                new_list.append(e)
            self.points = new_list.copy()

            return new_pos * 2

    def remove_point(self, idx):
        self.segmentation = []
        if self.points is not None:
            if idx < len(self.points):
                if idx == 0:
                    self.points = self.points[1:]
                elif idx == len(self.points)-1:
                    self.points = self.points[:-1]
                else:
                    self.points = self.points[:idx] + self.points[idx+1:]

                return True
        return False

    def modify_point(self, idx, point):
        self.segmentation = []
        if self.points is not None:
            if idx < len(self.points):
                self.points[idx] = point
                return True

        return False

    def close_roi(self):
        if self.points is not None:
            if len(self.points) > 2:
                self.closed_flag = True
                return True

        return False

    def open_roi(self):
        self.closed_flag = False

    '''
    Functions to manage the tiles
    '''
    def add_tile(self, x, y):
        self.tiles[y, x] = 1

    def add_tiles(self, tiles):
        if self.tiles is not None:
            self.tiles[tiles > 0] = 1

    def remove_tiles(self, tiles):
        if self.tiles is not None:
            self.tiles[tiles > 0] = 0

    def tiles_exist(self):
        if self.tiles is not None:
            return True
        else:
            return False

    def generate_empty_tiles(self, image_dimension, tile_size=None):
        if tile_size is None:
            tile_size = self.tile_size
        tiles_number = (int(image_dimension[0] / tile_size), int(image_dimension[1] / tile_size))
        print(tiles_number)
        #tiles_number = (image_dimension / tile_size).astype(int)
        return np.zeros(tiles_number)

    def generate_tiles(self, tile_size, layer, ratio, image_dimension):
        if not self.closed_flag:
            return False

        # set roi parameters
        self.tiles_layer = layer
        self.tile_size = tile_size
        self.ration = ratio


        print(ratio)
        # Create the corresponding Shapely Polygon
        polygon_points = np.array(self.points)
        roi_polygon = Polygon(self.points)

        # get max an min polygon coordinates
        max_coord = np.max(polygon_points, axis=0)
        min_coord = np.min(polygon_points, axis=0)

        # get starting and ending index
        pos_start = (min_coord / tile_size).astype(int)
        pos_end = (max_coord / tile_size).astype(int)

        # get tiles number and create an array containing the tiles
        tiles_number = (image_dimension / tile_size).astype(int)
        tiles = np.zeros(tiles_number)

        for tile_x in range(pos_start[0], pos_end[0] + 1):
            for tile_y in range(pos_start[1], pos_end[1] + 1):

                # compute real position of tiles
                x = (tile_x * tile_size)
                y = (tile_y * tile_size)

                # create a box
                curr_box = box(x, y, x + tile_size, y + tile_size)

                # compute intersection area
                intersection_area = roi_polygon.intersection(curr_box).area

                # if intersection area is smaller than the ration add to active tiles
                if intersection_area / (tile_size ** 2) >= ratio:
                    tiles[tile_y, tile_x] = 1

        self.tiles = tiles
        print("Finished generating tiles. Generated ", np.count_nonzero(self.tiles), " tiles")

    def get_tiles_from_line(self, line_points, only_active=False):
        if len(line_points) < 1:
            return

        tiles = np.zeros(self.tiles.shape)
        tile_size = self.tile_size
        roi_polygon = Polygon(self.points)

        for i in range(len(line_points) - 1):

            line_start = line_points[i].copy()
            line_end = line_points[i+1].copy()

            if line_start[1] > line_end[1]:
                a = line_start
                line_start = line_end
                line_end = a

            line_start[0] = int(line_start[0]/self.tile_size)
            line_start[1] = int(line_start[1]/self.tile_size)
            line_end[0] = int(line_end[0]/self.tile_size)
            line_end[1] = int(line_end[1] / self.tile_size)

            coords_start = (line_start)
            coords_end = (line_end)

            print("start: ", coords_start)
            print("end: ", coords_end)

            # orizontal (y1 = y2)
            if line_start[0] == line_end[0]:
                step = 1
                if line_start[1] > line_end[1]:
                    step = -1
                for k in range(line_start[1], line_end[1] + step, step):
                    y = k
                    x = line_start[0]

                    b = box(x * tile_size, y * tile_size, (x + 1) * tile_size,
                            (y + 1) * tile_size)
                    intersection = roi_polygon.intersection(b).area

                    if intersection / (tile_size ** 2) >= self.ratio:
                        tiles[y, x] = 1

            # vertical x1 = x2
            elif line_start[1] == line_end[1]:
                step = 1
                if line_start[0] > line_end[0]:
                    step = -1
                for k in range(line_start[0], line_end[0] + step, step):
                    y = line_start[1]
                    x = k

                    b = box(x * tile_size, y * tile_size, (x + 1) * tile_size,
                            (y + 1) * tile_size)
                    intersection = roi_polygon.intersection(b).area

                    if intersection / (tile_size ** 2) >= self.ratio:
                        tiles[y, x] = 1

            else:
                m = float((line_start[0] - line_end[0])/(line_start[1] - line_end[1]))
                print(m)
                if m > 1 or m < -1:
                    step = int(m/m)
                    for key, value in enumerate(range(line_start[1], line_end[1] + 1)):
                        for j in range(int(abs(m))+1):
                            y = value
                            x = int(line_start[0] + key * m + step * j)

                            if y > line_end[0]:
                                break

                            b = box(x * tile_size, y * tile_size, (x + 1) * tile_size,
                                             (y + 1) * tile_size)
                            intersection = roi_polygon.intersection(b).area

                            if intersection / (tile_size ** 2) >= self.ratio:
                                tiles[y, x] = 1

                else:
                    m = 1/m
                    step = 1
                    if line_start[0] > line_end[0]:
                        step = -1
                    for key, value in enumerate(range(line_start[0], line_end[0] + step, step)):
                        for j in range(int(abs(m)) + 1):
                            y = int(line_start[1] + step * key * m + step * j)
                            x = value

                            b = box(x * tile_size, y * tile_size, (x + 1) * tile_size,
                                    (y + 1) * tile_size)
                            intersection = roi_polygon.intersection(b).area

                            if intersection / (tile_size ** 2) >= self.ratio:
                                tiles[y, x] = 1
        print("Non empty: ", np.count_nonzero(tiles))

        return tiles