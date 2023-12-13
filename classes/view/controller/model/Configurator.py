import os
import os.path as osp
from pathlib import Path
import numpy as np

'''
Class to manage the configurations of SlideTiler. If the configuration file is not present it creates it.
'''
class Configurator:
    def __init__(self, path):
        self.name = "config.txt"
        self.path = path
        self.parameters = dict()

        if osp.isfile(osp.join(self.path, self.name)):
            self.read()
        else:
            self.load_default()
            self.write()

    def read(self):
        file = open(osp.join(self.path, self.name), 'r')
        for line in file:
            correct_line, content = self.parse_line(line)
            if correct_line:
                self.parameters[content[0]] = content[1]
        file.close()

    def write(self):
        file = open(osp.join(self.path, self.name), 'w')
        for key, value in self.parameters.items():
            # line of the configuration file
            line = []

            # always start content as array
            line.append("[")

            # check every element of the configurations
            for values in value:

                #if the element is an array ad [ e0 ; ... ; en]
                if isinstance(values, list):
                    line += "["
                    for element in values:
                        line.append(str(element))
                        line.append(";")
                    line[-1] = "]"

                # else append directly the value
                else:
                    line.append(str(value[0]))

            # close the content
            line.append("]")

            # add the key before and convert everything as string
            line = (key+"=")+ "".join(line)

            # write to
            file.write(line+"\n")

        file.close()

    def load_default(self):
        self.parameters = {
            "in_path": [str(Path.home())],
            "out_path": [str(Path.home())],
            "canvas_dimension": [[960, 640]],
            "tiles_color": ["red"],
            "labels": [["0", "False", "#f00000"], ["1", "True", "#0000f0"]]
        }

    def get_parameters(self):
        return self.parameters

    def set_parameters(self, parameters):
        self.parameters = parameters

    @staticmethod
    def parse_line(line):

        # split '=' to distinguish key and value
        split_index = line.find('=')
        if split_index == -1:
            return False, []

        key = line[:split_index]
        value = line[split_index + 1:]

        # parse [content] where content may be an array [e0 ; ... ; en]
        parsed_value = []
        while value[0] == '[':
            array = []
            closed_index = value.find(']')
            split_list = value[value.find('[')+1:closed_index].split(";")
            for split in split_list:
                if split[0] == '[':
                    split = split[1:]
                array.append(split)

            value = value[closed_index + 1:]
            parsed_value.append(array)

        return True, [key, parsed_value]