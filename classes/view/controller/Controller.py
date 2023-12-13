from classes.view.controller.Zoom import Zoom
from classes.view.controller.Filter import Filter
from classes.view.controller.Event import Event

from classes.view.controller.model.Saver import Saver
from classes.view.controller.model.Configurator import Configurator
from classes.view.controller.model.Roi import Roi

import os
import os.path as osp
import numpy as np
import matplotlib.pyplot as plt

import platform
dirname, filename = os.path.split(os.path.abspath(__file__))
if platform.system() == 'Windows':
    with os.add_dll_directory(dirname[0:dirname.rfind("\\")] + "\\openslide-win64\\bin"):
        import openslide
else:
    import openslide


'''
Class for controlling the interaction of the user with the GUI and the data
It uses three support classes: 
- Zoom: keep track of the dimension of the pyramid layers of the slide. It also converts coordinate from one layer to another or to the GUI coordinates
- Event: associate an action to each event triggered by the user (clicks, mouse moves). 
- Filter: manages filters to apply. At the moment contains a stardist filter.
'''
class Controller:
    def __init__(self):

        self.rois = []
        self.active_roi_id = -1

        self.roll_back_roi = []
        self.roll_back_id = -1
        self.roll_back_limit = 10

        self.zoom_controller = None
        self.event_controller = Event()
        self.filter_controller = Filter()
        self.saver_controller = None

        self.roi_modifying_flag = False
        self.roi_modifying_index = 0
        self.add_flag = False
        self.remove_flag = False
        self.roi_drawing_flag = False
        self.modify_tiles_roi = []
        self.modify_tiles = None
        self.filter_flag = False
        self.measure_flag = False
        self.measure_point = None

        self.configuration_model = Configurator(osp.join(""))

        self.image = None

        self.configurations = dict()
        self.read_configuration()

    '''
    Functions for visualizing and measure
    '''

    def start_measure(self):
        self.measure_flag = True

    def convert_to_meters(self, layer, pixels):
        return self.zoom_controller.convert_to_meters(layer, pixels)

    def get_windows_dimensions(self):
        dimension = self.configurations["canvas_dimension"][0]
        return [int(dimension[0]), int(dimension[1])]

    def get_level(self, level=None):
        return self.zoom_controller.get_level(level=level)

    def set_zoom(self, scale):
        if self.zoom_controller is not None:
            self.zoom_controller.zoom(scale)

    def rotate_left(self):
        self.zoom_controller.rotate_left()

    def rotate_right(self):
        self.zoom_controller.rotate_right()

    '''
    Functions to manage labels
    '''

    def get_labels(self):
        labels = self.configurations["labels"]
        returned_values = []

        for i in range(len(labels)):
            returned_values.append("id: " + labels[i][0].rstrip() + " - " + labels[i][1].rstrip())

        return returned_values

    def set_label(self, annotation):
        if self.active_roi_id != -1:
            labels = self.configurations["labels"]
            for i in range(len(labels)):
                if annotation == "id: " + labels[i][0].rstrip() + " - " + labels[i][1].rstrip():
                    self.rois[self.active_roi_id].set_annotation(labels[i][0], labels[i][1], labels[i][2])
                    break

    def add_label(self, ann_id, name, color):
        print(self.configurations)
        if ann_id.isnumeric() and len(name) > 0:
            self.configurations["labels"].append([str(ann_id), str(name), str(color)])
            self.configuration_model.set_parameters(self.configurations)
            self.configuration_model.write()
            print(self.configurations)

    def remove_label(self, id):
        new_labels = []
        for label in self.configurations["labels"]:
            if label[0] != str(id):
                new_labels.append(label)

        self.configurations["labels"] = new_labels
        self.configuration_model.set_parameters(self.configurations)
        self.configuration_model.write()

    '''
    Functions to open/close slides and save
    '''

    def open_slide(self, input, output):
        print(input)
        self.image = openslide.OpenSlide(input)
        self.zoom_controller = Zoom(self.image, self.get_windows_dimensions())

        name = osp.basename(input).split(".")[0]
        self.saver_controller = Saver(output, name)
        self.rois = self.saver_controller.read()
        self.filter_controller = Filter(image=self.image)
        print("ROIS loaded: ", self.rois)
        if len(self.rois) > 0:
            self.active_roi_id = 0

    def close_slide(self):
        self.image = None

        self.zoom_controller = None
        self.event_controller = Event()
        self.filter_controller = Filter()
        self.saver_controller = None

        self.roi_modifying_flag = False
        self.roi_modifying_index = 0
        self.add_flag = False
        self.remove_flag = False
        self.roi_drawing_flag = False
        self.modify_tiles_roi = []
        self.modify_tiles = None

        self.rois = []
        self.active_roi_id = -1

    def save(self, extension, ids=None):

        if ids is None:
            ids = self.active_roi_id

        if ids != -1:
            print("Saving ", np.count_nonzero(self.rois[ids].get_tiles()), " patches (before filters)")
            layer_factor = self.zoom_controller.get_layer_factor(self.rois[ids].get_tiles_layer())
            self.saver_controller.rewrite(self.image, self.rois[ids], layer_factor, extension)

    def save_all(self, extension):
        for i in range(len(self.rois)):
            self.save(extension, ids=i)

    def get_thumbnails(self):
        return self.zoom_controller.get_thumbnails()

    def get_image(self):
        image = self.zoom_controller.get_visualization()
        direction = self.zoom_controller.get_direction()
        if direction != 0:
            image = np.rot90(image, direction)
        return image

    def change_output(self, input, output):
        if output == "":
            output = self.configurations["out_path"][0]

        name = osp.basename(input).split(".")[0]
        self.saver_controller = Saver(output, name)
        self.rois = self.saver_controller.read()

        if len(self.rois) > 0:
            self.active_roi_id = 0

        self.configurations["out_path"] = output
        self.configuration_model.set_parameters(self.configurations)
        self.configuration_model.write()

    def read_configuration(self):
        self.configurations = self.configuration_model.get_parameters()
        print(self.configurations)


    '''
    Functions to manage ROIs
    '''

    def get_roi(self, get_all=False):
        active_roi = []
        rois = []
        color = "#00000d"
        other_colors = []

        if self.active_roi_id != -1:
            for point in self.rois[self.active_roi_id].get_roi():
                active_roi.append(self.zoom_controller.compute_canvas_position([point[1], point[0]]))
            if self.rois[self.active_roi_id].is_closed():
                point = self.rois[self.active_roi_id].get_roi()[0]
                active_roi.append(self.zoom_controller.compute_canvas_position([point[1], point[0]]))

            color = self.rois[self.active_roi_id].get_annotation()[2]

        if get_all:
            for i in range(len(self.rois)):
                if i == self.active_roi_id:
                    continue
                roi = []
                for point in self.rois[i].get_roi():
                    roi.append(self.zoom_controller.compute_canvas_position([point[1], point[0]]))
                rois.append(roi)
                other_colors.append(self.rois[i].get_annotation()[2])

        return active_roi, rois, color, other_colors

    def get_modify_roi(self):
        x = []
        y = []

        for a, b in self.modify_tiles_roi:
            v1, v2 = self.zoom_controller.compute_canvas_position([b, a])
            x.append(v1)
            y.append(v2)

        return [x, y]


    def start_modify_roi(self):
        if self.active_roi_id != -1 and len(self.rois[self.active_roi_id].get_roi()) > 0:
            self.roi_drawing_flag = False
            self.roi_modifying_flag = True
            self.roi_modifying_index = 0
            print("Modifying")

    def add_roi(self):
        if len(self.rois) > 0:
            idx = self.rois[-1].get_id() + 1
        else:
            idx = 0
        self.rois.append(Roi(idx))
        self.active_roi_id = len(self.rois) - 1

    def draw_roi(self):
        if self.active_roi_id != -1:
            self.roi_drawing_flag = True
        else:
            self.add_roi()
            self.roi_drawing_flag = True
        self.rois[self.active_roi_id].open_roi()

    def reset_roi(self):
        if self.active_roi_id != -1:
            self.rois[self.active_roi_id] = Roi(self.rois[self.active_roi_id].get_id())
            self.update_rollback()

    def stop_draw_roi(self):
        self.roi_drawing_flag = False

    def remove_roi(self):
        if self.active_roi_id != -1:
            self.saver_controller.remove(self.rois[self.active_roi_id].get_id())
            if self.active_roi_id > 0:
                self.rois = self.rois[:self.active_roi_id] + self.rois[self.active_roi_id + 1:]
                self.active_roi_id -= 1
            elif self.active_roi_id == 0:
                self.rois = self.rois[1:]
                self.active_roi_id = len(self.rois) - 1

    def select_next_roi(self):
        if len(self.rois) > 1:
            self.active_roi_id += 1
            self.active_roi_id = self.active_roi_id % len(self.rois)
            self.reset_rollback()

    def select_previous_roi(self):

        if len(self.rois) > 1:
            self.active_roi_id -= 1
            self.active_roi_id = self.active_roi_id % len(self.rois)
            self.reset_rollback()

    def stop_modify_roi(self):
        self.roi_modifying_flag = False
        self.roi_modifying_index = 0

    def get_modify_point(self):
        point = []
        if self.active_roi_id != -1 and self.roi_modifying_flag:
            if self.roi_modifying_index % 2 == 0:

                point = self.rois[self.active_roi_id].get_roi()[int(self.roi_modifying_index/2)]

            else:
                roi_points = self.rois[self.active_roi_id].get_roi()
                p1 = int(self.roi_modifying_index/2)
                p2 = (p1 + 1) % len(roi_points)
                point = [(roi_points[p1][0] + roi_points[p2][0])/2, (roi_points[p1][1] + roi_points[p2][1])/2]

            point = self.zoom_controller.compute_canvas_position([point[1], point[0]])

        return point

    def get_active_roi(self):
        return self.active_roi_id

    def get_roi_numbers(self):
        return len(self.rois)

    def get_active_id_label(self):
        if len(self.rois) == 0:
            return "-1/-1"

        return str(self.active_roi_id+1)+"/"+str(len(self.rois))


    '''
    Functions to manage tiles
    '''
    def set_tiles_color(self, color):

        self.configurations["tiles_color"] = [color]
        self.configuration_model.set_parameters(self.configurations)
        self.configuration_model.write()

    def generate_tiles(self, size, layer, ratio, idg=None):
        if idg is None:
            idg = self.active_roi_id

        if idg != -1:
            # computa vera dimension del layer
            real_size = int(self.zoom_controller.convert_dimension(size, layer))
            if real_size == -1:
                return

            image_dimension = self.zoom_controller.get_dimension()
            ratio = float(ratio) / 100

            self.rois[idg].generate_tiles(real_size, layer, ratio, np.array(image_dimension))

        else:
            print("not active")

    def generate_all_tiles(self, size, layer, ratio):
        for i in range(len(self.rois)):
            self.generate_tiles(size, layer, ratio, idg=i)

    def get_tiles(self):
        tiles = []
        if self.active_roi_id != -1:
            size = self.rois[self.active_roi_id].get_tile_size()
            size_canvas = self.zoom_controller.compute_canvas_dimension([size, size])
            coordinates = np.nonzero(self.rois[self.active_roi_id].get_tiles())

            y_increment = 1
            x_increment = 0
            direction = self.zoom_controller.get_direction()
            if direction == 1:
                y_increment = 0
                x_increment = 0
                temp = size_canvas[0]
                size_canvas[0] = size_canvas[1]
                size_canvas[1] = temp

            elif direction == 2:
                y_increment = 0
                x_increment = 1
            elif direction == 3:
                y_increment = 1
                x_increment = 1
                temp = size_canvas[0]
                size_canvas[0] = size_canvas[1]
                size_canvas[1] = temp

            for i in range(len(coordinates[0])):
                y = float(coordinates[1][i] + y_increment) * size
                x = float(coordinates[0][i] + x_increment) * size

                x, y = self.zoom_controller.compute_canvas_position([x, y])

                if 0 <= x <= 1 and 0 <= y <= 1:
                    tiles.append([x, y, size_canvas[0], size_canvas[1]])

        return tiles

    def get_modify_tiles(self):
        tiles = []
        if self.active_roi_id != -1 and (self.add_flag or self.remove_flag or self.filter_flag):
            size = self.rois[self.active_roi_id].get_tile_size()
            size_canvas = self.zoom_controller.compute_canvas_dimension([size, size])
            coordinates = np.nonzero(self.modify_tiles)

            for i in range(len(coordinates[0])):
                y = float(coordinates[1][i] + 1) * size
                x = float(coordinates[0][i]) * size

                x, y = self.zoom_controller.compute_canvas_position([x, y])

                if 0 <= x <= 1 and 0 <= y <= 1:
                    tiles.append([x, y, size_canvas[0], size_canvas[1]])

        return tiles

    def remove_tiles_in_roi(self):
        self.stop_tiles()
        self.modify_tiles_roi = []
        self.modify_tiles = self.rois[self.active_roi_id].generate_empty_tiles(self.zoom_controller.get_dimension())
        self.remove_flag = True

    def add_tiles_in_roi(self):
        self.stop_tiles()
        self.modify_tiles_roi = []
        self.modify_tiles = self.rois[self.active_roi_id].generate_empty_tiles(self.zoom_controller.get_dimension())
        self.add_flag = True

    def stop_tiles(self):
        self.add_flag = False
        self.remove_flag = False
        self.filter_flag = False
        self.modify_tiles_roi = []
        self.modify_tiles = []

    '''
    Functions to manage filters
    '''

    def reset_filter(self):
        if self.filter_flag:
            self.filter_flag = False
            self.modify_tiles = []

    def apply_filter(self):
        if self.filter_flag:
            if self.active_roi_id != -1:
                self.rois[self.active_roi_id].remove_tiles(self.modify_tiles)
                self.stop_tiles()


    def filter_image(self, ratio):
        if self.active_roi_id != -1:
            min_points, max_points = self.rois[self.active_roi_id].get_boundaries()
            min_points = min_points.astype(int)
            max_points = max_points.astype(int)

            dimension = max_points - min_points

            roi_slice = self.image.read_region((int(min_points[1]), int(min_points[0])), 0,
                                               (int(dimension[1]), int(dimension[0])))
            self.modify_tiles = self.filter_controller.filter_roi(self.rois[self.active_roi_id], roi_slice,
                                                                  dimension[1], dimension[0], min_points[1],
                                                                  min_points[0], ratio)

            if (np.count_nonzero(self.modify_tiles)) > 0:
                self.filter_flag = True



    '''
    Functions to controll the events
    '''

    def key_event(self, event):
        flag_roi_modifying = self.roi_modifying_flag and len(self.rois[self.active_roi_id].get_roi()) > 0
        level_increment, pos_increment, modify_index_increment = self.event_controller.key(event, flag_roi_modifying)

        self.zoom_controller.increment_zoom(level_increment)
        self.zoom_controller.change_position(pos_increment)

        self.roi_modifying_index += modify_index_increment
        if self.active_roi_id != -1:
            if self.roi_modifying_index >= 2 * len(self.rois[self.active_roi_id].get_roi()):
                self.roi_modifying_index = 0
            elif self.roi_modifying_index < 0:
                self.roi_modifying_index = 2 * len(self.rois[self.active_roi_id].get_roi()) - 1

    def click_event(self, event):
        add_remove = (self.add_flag or self.remove_flag) and (not self.measure_flag)

        stop_button, point = self.event_controller.click(event, add_remove)

        if stop_button:
            self.roi_drawing_flag = False
            if self.active_roi_id != -1:
                self.rois[self.active_roi_id].close_roi()
            if self.add_flag:
                self.rois[self.active_roi_id].add_tiles(self.modify_tiles)
                self.stop_tiles()
            elif self.remove_flag:
                self.rois[self.active_roi_id].remove_tiles(self.modify_tiles)
                self.stop_tiles()
            else:
                # change active roi if possible
                point = self.zoom_controller.compute_absolute_position(point)
                for k, roi in enumerate(self.rois):
                    if roi.is_inside(point):
                        self.active_roi_id = k
                        break

        if point[0] != -1:
            point = self.zoom_controller.compute_absolute_position(point)

            if add_remove:
                x = point[0]
                y = point[1]
                self.modify_tiles_roi.append([y, x])
                print(self.modify_tiles_roi)
                if len(self.modify_tiles_roi) > 1:
                    p1 = self.modify_tiles_roi[-2].copy()
                    p2 = self.modify_tiles_roi[-1].copy()

                    tiles = self.rois[self.active_roi_id].get_tiles_from_line([p1, p2], only_active=self.remove_flag)
                    self.modify_tiles += tiles
            elif self.measure_flag:
                if self.measure_point is None:
                    self.measure_point = point
                else:
                    mis = self.zoom_controller.measure(self.measure_point, point)
                    mis[0] /= 1000
                    self.measure_point = None
                    self.measure_flag = False
                    return mis

    def release_event(self, event):
        point = self.event_controller.click_release(event)
        if point[0] != -1:
            point = self.zoom_controller.compute_absolute_position(point)

            if self.roi_drawing_flag and not self.rois[self.active_roi_id].is_closed():
                self.rois[self.active_roi_id].add_point(point)
                self.update_rollback()

            elif self.roi_modifying_flag:
                self.roi_modifying_index = self.rois[self.active_roi_id].change_point(self.roi_modifying_index, point)
                self.update_rollback()

    def move_event(self, event):
        start_line = -1
        end_line = -1

        move, pos_increment, modify = self.event_controller.move(event, self.roi_drawing_flag, self.measure_flag)
        self.zoom_controller.change_position(pos_increment)

        if move[0] != -1:

            if self.roi_drawing_flag and self.active_roi_id != -1 and len(self.rois[self.active_roi_id].get_roi()) > 0:
                last_point = self.rois[self.active_roi_id].get_roi()[-1]
                start_line = self.zoom_controller.compute_canvas_position([last_point[1], last_point[0]])
                end_line = [move[0], 1-move[1]]

            elif self.measure_point is not None:

                start_line = self.zoom_controller.compute_canvas_position(self.measure_point)
                end_line = [move[0], 1 - move[1]]

        if modify[0] != -1:
            modify[1] = 1 - modify[1]
            point = self.zoom_controller.compute_absolute_position(modify)
            x = point[0]
            y = point[1]
            self.modify_tiles_roi.append([y, x])

            if len(self.modify_tiles_roi) > 1:
                tiles = self.rois[self.active_roi_id].get_tiles_from_line([self.modify_tiles_roi[-2],
                                                                           self.modify_tiles_roi[-1]],
                                                                          only_active=self.remove_flag)
                self.modify_tiles += tiles
        return [start_line, end_line]

    def wheel_event(self, event):
        level_increment, pos_perc_increment = self.event_controller.wheel(event)

        # increment = self.zoom_controller.compute_canvas_position(pos_perc_increment)

        # print(increment)
        # print(level_increment)
        if level_increment != 0:
            self.zoom_controller.increment_zoom(level_increment)
        #else:
        #    self.zoom_controller.change_position(increment)


    '''
    Functions to rollback (remove last actions)
    '''

    def update_rollback(self):
        self.roll_back_roi = self.roll_back_roi[:self.roll_back_id + 1]

        if len(self.roll_back_roi) > self.roll_back_limit:
            self.roll_back_roi = self.roll_back_roi[1:]

        self.roll_back_roi.append(self.rois[self.active_roi_id].get_roi().copy())
        self.roll_back_id = len(self.roll_back_roi) - 1

    def reset_rollback(self):
        self.roll_back_roi = []
        self.roll_back_id = -1

    def rollback(self):
        roll_back_dim = len(self.roll_back_roi)
        if roll_back_dim > 0 and self.roll_back_id > 0:
            self.roll_back_id -= 1
            self.rois[self.active_roi_id].set_roi(self.roll_back_roi[self.roll_back_id])

    def rollforward(self):
        roll_back_dim = len(self.roll_back_roi)
        if self.roll_back_id <= roll_back_dim - 2:
            self.roll_back_id += 1
            self.rois[self.active_roi_id].set_roi(self.roll_back_roi[self.roll_back_id])

    '''
    Manage files path
    '''

    def get_near_files(self, input):
        _, extension = osp.splitext(input)
        name = osp.basename(input)
        path = osp.dirname(input)

        files = [each for each in os.listdir(path) if each.endswith(extension)]
        files.sort()

        index = files.index(name)
        prev_index = index - 1
        if prev_index < 0:
            prev_index = 0
        succ_index = (index + 1) % len(files)

        return files[prev_index], files[succ_index]

    def get_next_file(self, input):
        _, extension = osp.splitext(input)
        name = osp.basename(input)
        path = osp.dirname(input)

        files = [each for each in os.listdir(path) if each.endswith(extension)]
        files.sort()

        index = files.index(name)
        succ_index = (index + 1) % len(files)
        new_succ_index = (index + 2) % len(files)

        new_file = osp.join(path, files[succ_index])

        return name, files[new_succ_index], new_file

    def get_previous(self, input):
        _, extension = osp.splitext(input)
        name = osp.basename(input)
        path = osp.dirname(input)

        files = [each for each in os.listdir(path) if each.endswith(extension)]
        files.sort()

        index = files.index(name)
        prec_index = (index - 1) % len(files)
        new_prec_index = (index - 2) % len(files)

        new_file = osp.join(path,  files[prec_index])

        return files[new_prec_index], name, new_file
