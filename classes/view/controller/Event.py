import datetime
from matplotlib.backend_bases import MouseButton

'''
Control the action to each event triggered by the user (clicks, mouse moves).
events: 
- keys: + and - zoom in or out
- arrows: move inside the slide or change modifying point
- wheel rotation: zoom in or out
- wheel/left button press and move: move inside the slide
- left click: interact to add points 
- mouse move: show the line of the roi that the user is creating 
'''
class Event:
    def __init__(self):
        self.scroll_time = datetime.datetime.now()
        self.middle_button_active = False
        self.left_button_active = False
        self.middle_button_time = datetime.datetime.now()
        self.left_button_time = datetime.datetime.now()
        self.left_button_time_active = datetime.datetime.now()
        self.press_time = 100000
        self.middle_button_position = [0, 0]
        self.left_button_position = [0, 0]
        self.ar_active = False
        self.ar_time = datetime.datetime.now()

        self.step = 100

    def key(self, event, roi_modifying):

        level_increment = 0
        x_increment = 0
        y_increment = 0
        modify_index_increment = 0

        if (event.key == "+") | (event.key == "-"):
            if event.key == "+":
                level_increment = -1
            else:
                level_increment = 1

        elif roi_modifying:
            if (event.key == "right") | (event.key == "left"):
                if event.key == "right":
                    modify_index_increment = 1
                else:
                    modify_index_increment = -1
        else:
            if (event.key == "right") | (event.key == "left") | (event.key == "up") | (event.key == "down"):

                if event.key == "right":
                    x_increment = self.step
                elif event.key == "left":
                    x_increment = - self.step
                elif event.key == "up":
                    y_increment = - self.step
                else:
                    y_increment = self.step

        return level_increment, [x_increment, y_increment], modify_index_increment

    def wheel(self, event):
        # print(event)
        level_increment = 0
        x_perc_increment = 0
        y_perc_increment = 0

        time = datetime.datetime.now()
        diff = time - self.scroll_time
        if (diff.seconds > 0) | (diff.microseconds > 300000):

            if event.button == "up":
                level_increment = -1
            elif event.button == "down":
                level_increment = 1

            self.scroll_time = time

        return level_increment, [x_perc_increment, y_perc_increment]

    def click(self, event, add_remove_flag):
        stop_button = False
        point_x = -1
        point_y = -1

        if event.button is MouseButton.LEFT:
            point_x = event.x
            point_y = event.y

            if add_remove_flag:
                self.ar_active = True
                self.ar_time = datetime.datetime.now()
            else:
                self.left_button_active = True
                self.left_button_time = datetime.datetime.now()
                self.left_button_time_active = datetime.datetime.now()
                self.left_button_position = [event.x, event.y]

        elif event.button is MouseButton.RIGHT:
            stop_button = True
            point_x = event.x
            point_y = event.y

        elif event.button is MouseButton.MIDDLE:
            self.middle_button_active = True
            self.middle_button_time = datetime.datetime.now()
            self.middle_button_position = [event.x, event.y]

        return stop_button, [point_x, point_y]

    def click_release(self, event):
        time = datetime.datetime.now()
        diff = time - self.left_button_time_active

        self.middle_button_active = False

        if self.ar_active:
            self.ar_active = False

        if self.left_button_active:

            if diff.seconds == 0 and diff.microseconds < self.press_time*2:
                self.left_button_active = False

                point_x = event.x
                point_y = event.y
                return [point_x, point_y]
            else:
                self.left_button_active = False

        return [-1, -1]

    def move(self, event, drawing_flag, measure_flag):
        x_increment = 0
        y_increment = 0

        x_modify = -1
        y_modify = -1

        x_move = -1
        y_move = -1

        if drawing_flag or measure_flag:

            x_move = event.x
            y_move = 1 - event.y

        elif self.ar_active:
            # Check time to trigger event
            time = datetime.datetime.now()
            diff = time - self.ar_time
            if (diff.seconds > 0) | (diff.microseconds > 100000):

                x_modify = event.x
                y_modify = 1 - event.y

                self.ar_time = time

        if self.middle_button_active or self.left_button_active:

            # Check time to trigger event
            time = datetime.datetime.now()
            if self.middle_button_active:
                diff = time - self.middle_button_time
                if (diff.seconds > 0) | (diff.microseconds > self.press_time / 2):
                    # move image
                    diff_x = self.middle_button_position[0] - event.x
                    diff_y = self.middle_button_position[1] - event.y
                    x_increment = diff_x * 1000
                    y_increment = - diff_y * 1000

                    # Update values
                    self.middle_button_time = time
                    self.middle_button_position = [event.x, event.y]
            else:
                diff = time - self.left_button_time
                if (diff.seconds > 0) | (diff.microseconds > self.press_time / 2):
                    # move image
                    diff_x = self.left_button_position[0] - event.x
                    diff_y = self.left_button_position[1] - event.y
                    x_increment = diff_x * 1000
                    y_increment = - diff_y * 1000

                    # Update values
                    self.left_button_time = time
                    self.left_button_position = [event.x, event.y]

        return [x_move, y_move], [x_increment, y_increment], [x_modify, y_modify]
