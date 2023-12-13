import os
import glob

from classes.view.controller.model.Roi import Roi

'''
Class that manages the saving of the tiles.
It creates a structured directory
It also reads the data to keep track of past annotations.
'''
class Saver:
    def __init__(self, path, name):
        self.out_path = path
        self.name = name
        self.existing_data = False

        self.set_existing_data()

    def write(self, image, roi, layer_factor, extension):
        if not self.existing_data:
            self.create_directory_structure()

        # self.existing_data = True
        roi_id = str(roi.get_id())

        # write roi info
        file_roi = open(os.path.join(self.out_path, self.name, "descriptions/roi.csv"), "a")
        file_roi.write(roi_id + ";")
        file_roi.write(str(roi.get_annotation()[0]) + ";" + str(roi.get_annotation()[1]) + ";"
                       + str(roi.get_annotation()[2]) + ";" + str(roi.get_tiles_layer()) + ";")
        for point in roi.get_roi():
            file_roi.write("[" + str(point[1]) + "," + str(point[0]) + "]")
        file_roi.write("\n")
        file_roi.close()

        # write tiles info and images
        if roi.get_tiles() is not None:
            self.write_tiles(image, roi.get_tiles(), roi_id, roi.get_annotation(), roi.get_tile_size(),
                             roi.get_tiles_layer(), layer_factor, extension)

    def write_tiles(self, image, tiles, roi_id, annotation, dimensions, layer, layer_factor, extension):
        if not self.existing_data:
            self.create_directory_structure()
        image_path = os.path.join(self.out_path, self.name, "images/")
        file_tiles = open(os.path.join(self.out_path, self.name, "descriptions/tiles.csv"), "a")
        number = 0

        w = dimensions / layer_factor
        h = dimensions / layer_factor
        w = int(w)
        h = int(h)

        class_id = annotation[0]
        class_name = annotation[1]

        image_w = image.level_dimensions[0][0]
        image_h = image.level_dimensions[0][1]

        for i in range(tiles.shape[0]):
            for j in range(tiles.shape[1]):
                if tiles[i, j] == 0:
                    continue

                file_tiles.write(roi_id + ";")
                file_tiles.write(str(number) + ";" + str(class_id) + ";")
                file_tiles.write(str(layer) + ";")

                pos_x = i * dimensions
                pos_y = j * dimensions

                file_tiles.write(str(pos_x) + ";" + str(pos_y) + ";" + str(j) + ";" + str(i) + ";")
                file_tiles.write(str(dimensions) + ";" + str(dimensions) + ";")
                file_tiles.write(str(image_w) + ";" + str(image_h))

                file_tiles.write("\n")

                curr_image = image.read_region((pos_x, pos_y), int(layer), (w, h))
                if extension == "jpg":
                    curr_image = curr_image.convert('RGB')
                curr_image.save(os.path.join(image_path, self.name + "_roi" + roi_id + "_" + str(number).zfill(8) + "." + str(extension)))

                number += 1

        file_tiles.close()

    def remove(self, roi_id):
        if not self.existing_data:
            self.create_directory_structure()
        self.remove_from_file("roi", roi_id)
        self.remove_from_file("tiles", roi_id)

        files = glob.glob(os.path.join(self.out_path, self.name, "images", self.name + "_roi" + str(roi_id) + "_*.*"))
        for file in files:
            os.remove(file)

    def remove_from_file(self, name, id):
        if not self.existing_data:
            self.create_directory_structure()
        file_copy = open(os.path.join(self.out_path, self.name, "descriptions", name+"_copy.csv"), "w")
        file = open(os.path.join(self.out_path, self.name, "descriptions", name+".csv"), "r")
        for line in file:
            if line.split(";")[0] != str(id):
                file_copy.write(line)

        file.close()
        file_copy.close()

        os.remove(os.path.join(self.out_path, self.name, "descriptions", name+".csv"))
        os.rename(os.path.join(self.out_path, self.name, "descriptions", name+"_copy.csv"), os.path.join(self.out_path, self.name, "descriptions", name+".csv"))

    def rewrite(self, image, roi, layer_factor, extension):
        if not self.existing_data:
            self.create_directory_structure()
        self.remove(roi.get_id())
        self.write(image, roi, layer_factor, extension)

    def rewrite_tiles(self, image, roi, layer_factor, extension):
        if not self.existing_data:
            self.create_directory_structure()
        self.remove_from_file("tiles", roi.get_id())
        self.write_tiles(image, roi.get_tiles(), roi.get_id(), roi.get_annotation(), roi.get_tiles_dimensions(),
                         roi.get_tiles_layer(), layer_factor, extension)

    def change_directory(self, path, name):
        self.existing_data = False
        self.out_path = path
        self.name = name
        self.set_existing_data()

    def read(self):
        if self.existing_data:
            rois, roi_index = self.read_rois()

            if len(rois) > 0:
                file = open(os.path.join(self.out_path, self.name, "descriptions", "tiles.csv"), "r")
                first_line = True

                for line in file:
                    if first_line:
                        first_line = False
                        continue

                    params = line.split(";")

                    roi_id = int(params[0])
                    x = int(params[6])
                    y = int(params[7])
                    dimension_x = int(params[8])
                    dimension_y = int(params[9])
                    image_w = int(params[10])
                    image_h = int(params[11])

                    roi_array_id = roi_index.index(roi_id)

                    if not rois[roi_array_id].tiles_exist():
                        tiles = rois[roi_array_id].generate_empty_tiles([image_w, image_h], dimension_x) #, [dimension_y, dimension_x])
                        rois[roi_array_id].set_tiles(tiles)
                        rois[roi_array_id].set_tile_size(dimension_x)
                    rois[roi_array_id].add_tile(x, y)

            return rois

        else:
            return []

    def read_rois(self):
        if self.existing_data:
            rois = []
            roi_index = []

            file = open(os.path.join(self.out_path, self.name, "descriptions", "roi.csv"), "r")
            first_line = True

            for line in file:
                if first_line:
                    first_line = False
                    continue
                params = line.split(";")

                roi_id = int(params[0])
                annotation = [params[1], params[2], params[3]]
                layer = int(params[4])

                roi = Roi(roi_id)
                roi.set_annotation(annotation[0], annotation[1], annotation[2])
                roi.set_tiles_layer(layer)

                roi_index.append(roi_id)

                points = params[5][1:].split("[")
                for point in points:
                    point = point[:-1]
                    x, y = point.split(",")
                    if y[-1] == "]":
                        y = y[:-1]

                    roi.add_point([int(float(x)), int(float(y))])

                roi.close_roi()
                rois.append(roi)

            file.close()

            return rois, roi_index

        return [], []

    def set_existing_data(self):
        if os.path.exists(os.path.join(self.out_path, self.name)):
            self.existing_data = True

    def create_directory_structure(self):
        if not os.path.exists(os.path.join(self.out_path, self.name)):
            print("Creating output directories")
            # Create directories
            os.mkdir(os.path.join(self.out_path, self.name))
            os.mkdir(os.path.join(self.out_path, self.name, "images/"))
            os.mkdir(os.path.join(self.out_path, self.name, "descriptions/"))

            # create tiles_file
            file = open(os.path.join(self.out_path, self.name, "descriptions", "tiles.csv"), "w")
            file.write("Roi_id;Tile_Number;class_id;layer;abs_position_x;abs_position_y;discrete_position_x"
                       ";discrete_position_y;dimension_x;dimension_y;image_dimension_x;image_dimension_y\n")
            file.close()
            file = open(os.path.join(self.out_path, self.name, "descriptions", "roi.csv"), "w")
            file.write("ID;class_name;class_id;class_color;tiles_layer;roi_points\n")
            file.close()
            self.existing_data = True

        else:
            print("Exists")
