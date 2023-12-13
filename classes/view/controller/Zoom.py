import math

import sys

'''
Class that keep track of the dimension of the pyramid layers of the slide. 
It also converts coordinate from one layer to another or to the GUI coordinates
'''
class Zoom:
    def __init__(self, image, dimesions):
        self.image = image
        self.direction = 0

        self.position_x = 0
        self.position_y = 0
        self.vis_image_w = dimesions[0]
        self.vis_image_h = dimesions[1]
        self.canvas_dimension_y = self.vis_image_h
        self.canvas_dimension_x = self.vis_image_w

        self.dimensions = self.image.level_dimensions
        self.downsamples = self.image.level_downsamples
        self.max_level = self.image.level_count - 1

        self.first_level = self.max_level
        for i in range(self.max_level, -1, -1):
            if self.dimensions[i][0] > dimesions[0] and self.dimensions[i][1] > dimesions[1]:
                break
            self.first_level = i
        self.curr_level = self.first_level

        self.curr_image_w = self.dimensions[self.curr_level][0]
        self.curr_image_h = self.dimensions[self.curr_level][1]

        self.max_zoom_increment = 1
        for i in range(len(self.downsamples) - 1):
            if self.downsamples[i + 1] / self.downsamples[i] > self.max_zoom_increment:
                self.max_zoom_increment = self.downsamples[i + 1] / self.downsamples[i]

        for k, v in self.image.properties.items():
            print("key: ", k, " value: ", v)

        self.max_zoom_increment = self.image.properties.get("openslide.objective-power")

        if self.max_zoom_increment is None:
            for k, v in self.image.properties.items():
                if k.endswith("AppMag"):
                    self.max_zoom_increment = v
                    break

        print("MAX INCREMENT: ", self.max_zoom_increment)

        self.mppx = self.image.properties.get("openslide.mpp-x")
        self.mppy = self.image.properties.get("openslide.mpp-y")

    def convert_to_meters(self, layer, pixels):
        dim = float(pixels)
        dim *= float(self.mppx) * self.downsamples[int(layer)]

        return dim

    def compute_canvas_position(self, pos):

        #pos = self.compute_direction(pos)

        x = ((pos[0]/self.downsamples[self.curr_level]) - self.position_x)/self.canvas_dimension_x
        y = 1 - (((pos[1])/self.downsamples[self.curr_level]) - self.position_y)/self.canvas_dimension_y

        x, y = self.compute_direction([x, y])


        return [x, y]

    def compute_absolute_position(self, pos, corner0=None, corner1=None):

        pos = self.compute_inverse_direction(pos)

        #x, y = self.compute_direction([x, y])

        x = (self.position_x + pos[0] * self.canvas_dimension_x) * self.downsamples[self.curr_level]
        y = (self.position_y + (1 - pos[1]) * self.canvas_dimension_y) * self.downsamples[self.curr_level]

        return [x, y]

    def get_level(self, level=None):
        if level is None:
            level = self.curr_level
        return level, self.max_level, float(self.max_zoom_increment), self.downsamples[level]

    def increment_zoom(self, increment):
        if increment != 0:
            new_scale = self.curr_level + increment
            if new_scale >= 0 and new_scale <= self.max_level:
                self.zoom(new_scale)

    def change_position(self, pos):

        pos = self.compute_direction_pos(pos)

        self.position_x += pos[0]
        self.position_x = min(self.position_x, (self.curr_image_h - self.canvas_dimension_x))
        self.position_x = max(self.position_x, 1)

        self.position_y += pos[1]
        self.position_y = min(self.position_y, (self.curr_image_w - self.canvas_dimension_y))
        self.position_y = max(self.position_y, 1)

    def zoom(self, scale):

        ratio = self.downsamples[scale] / self.downsamples[self.curr_level]
        ratio = round(ratio, 2)

        if sys.platform == "Windows" and ratio == 1:
            return

        prev_level = self.curr_level
        self.curr_level = scale

        self.position_x = (self.position_x / ratio)
        self.position_y = (self.position_y / ratio)

        if ratio < 1:

            r = self.downsamples[prev_level] / self.downsamples[scale]

            for i in range(int(r / 2)):
                self.position_x += (self.canvas_dimension_x / 2) * (i + 1)
                self.position_y += (self.canvas_dimension_y / 2) * (i + 1)

            self.position_x = min(self.position_x, self.dimensions[self.curr_level][0] - self.canvas_dimension_x)
            self.position_y = min(self.position_y, self.dimensions[self.curr_level][1] - self.canvas_dimension_y)

        elif ratio > 1:

            r = ratio

            for i in range(int(r / 2)):
                self.position_x -= (self.canvas_dimension_x / 4) / (i + 1)
                self.position_y -= (self.canvas_dimension_y / 4) / (i + 1)

        self.position_x = max(self.position_x, 0)
        self.position_y = max(self.position_y, 0)

        self.position_x = int(self.position_x)
        self.position_y = int(self.position_y)

        # the new position is previous position divided or multiplied by 2*2
        # previous + dimension of vis image * ratio * ratio
        if self.position_x > (self.curr_image_w / ratio - self.canvas_dimension_x):
            self.position_x = int(self.curr_image_w / ratio - self.canvas_dimension_x)
        if self.position_y > (self.curr_image_h / ratio - self.canvas_dimension_y):
            self.position_y = int(self.curr_image_h / ratio - self.canvas_dimension_y)

        self.position_x = max(0, self.position_x)
        self.position_y = max(0, self.position_y)

        self.curr_image_w = self.dimensions[self.curr_level][1]
        self.curr_image_h = self.dimensions[self.curr_level][0]

        self.change_position([0, 0])

    def get_visualization_parameters(self):

        return (int(self.position_x * self.downsamples[self.curr_level]),
                int(self.position_y * self.downsamples[self.curr_level])), \
            self.curr_level, \
            (self.canvas_dimension_x, self.canvas_dimension_y)

    def get_visualization(self):
        return self.image.read_region(
            (
                int(self.position_x * self.downsamples[self.curr_level]),
                int(self.position_y * self.downsamples[self.curr_level])
            ),
            self.curr_level,
            (self.canvas_dimension_x, self.canvas_dimension_y))

    def get_thumbnails(self):
        return self.image.get_thumbnail((400, 400))

    def convert_dimension(self, size, layer):
        if 0 <= layer < len(self.downsamples):
            return size * self.downsamples[layer]

        return -1

    def get_dimension(self, layer=0):
        return self.dimensions[layer]

    def compute_canvas_dimension(self, size):
        s1 = size[0] / self.dimensions[0][0] * (
                    self.dimensions[self.curr_level][0] / self.canvas_dimension_x)
        s2 = size[1] / self.dimensions[0][0] * (
                    self.dimensions[self.curr_level][0] / self.canvas_dimension_y)
        return [s1, s2]

    def get_layer_factor(self, layer):
        return self.dimensions[0][0] / self.dimensions[layer][0]

    def measure(self, p1, p2):
        pixels = math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
        return [round(self.convert_to_meters(0, pixels),  2), round(pixels, 2)]

    def rotate_left(self):
        self.direction += 1
        self.direction = self.direction % 4

        temp = self.canvas_dimension_y
        self.canvas_dimension_y = self.canvas_dimension_x
        self.canvas_dimension_x = temp

    def rotate_right(self):
        self.direction -= 1
        self.direction = self.direction % 4

        temp = self.canvas_dimension_y
        self.canvas_dimension_y = self.canvas_dimension_x
        self.canvas_dimension_x = temp

    def compute_direction(self, pos):

        if self.direction == 1 or self.direction == 3:
            temp = pos[0]
            pos[0] = pos[1]
            pos[1] = temp

        if self.direction == 2 or self.direction == 1:
            pos[0] = 1 - pos[0]

        if self.direction == 2 or self.direction == 3:
            pos[1] = 1 - pos[1]

        return pos

    def compute_inverse_direction(self, pos):

        if self.direction == 1 or self.direction == 3:
            temp = pos[0]
            pos[0] = pos[1]
            pos[1] = temp

        if self.direction == 2 or self.direction == 1:
            pos[1] = 1 - pos[1]

        if self.direction == 2 or self.direction == 3:
            pos[0] = 1 - pos[0]

        return pos

    def compute_direction_pos(self, pos):

        if self.direction == 1 or self.direction == 3:
            temp = pos[0]
            pos[0] = pos[1]
            pos[1] = temp

        if self.direction == 2 or self.direction == 1:
            pos[0] *= -1

        if self.direction == 2 or self.direction == 3:
            pos[1] *= -1

        return pos

    def get_direction(self):
        return self.direction