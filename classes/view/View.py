import time
import tkinter.filedialog
from os import path
import threading

import matplotlib.pyplot as plt
import os
import numpy as np

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.ttk
import tkinter.messagebox
from tkinter import colorchooser
from tkinter.messagebox import askyesno

import matplotlib
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.lines as lines
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backend_bases import MouseButton

from classes.view.controller.Controller import Controller

'''
Class that manages the GUI. 
Every action of the user is passed to the controller and visualize the responses of the controller.
'''

class ViewTk:
    def __init__(self):
        self.controller = Controller()
        self.color = "f00000"

        # Interactive mode for the pyplot graphs (the window displaying the slide)
        plt.ion()
        matplotlib.use("TkAgg")

        # Create windows
        self.main_win = tk.Tk()
        self.main_win.title('SlideTiler')

        self.state = False
        self.main_win.bind("<F11>", self.toggle_fullscreen)
        self.main_win.bind("<Escape>", self.end_fullscreen)
        text_width = 50

        self.screen_width = self.main_win.winfo_screenwidth()
        self.screen_height = self.main_win.winfo_screenheight()
        self.screen_width = min(self.screen_width, 1920)
        self.screen_height = min(self.screen_height, 1080)

        buttons_width = 15

        self.file_title = tk.Button(self.main_win, text='File', fg="#f00", padx=2, pady=2, font=16, width=buttons_width,
                                    command=lambda: self.toggle_view(0))
        self.roi_title = tk.Button(self.main_win, text='Roi', fg="#f00", padx=2, pady=2, font=16,
                                   width=buttons_width,
                                   command=lambda: self.toggle_view(1))
        self.tile_title = tk.Button(self.main_win, text='Tile', fg="#f00", padx=2, pady=2, font=16, width=buttons_width,
                                    command=lambda: self.toggle_view(2))
        self.filter_title = tk.Button(self.main_win, text='Filters', fg="#f00", padx=2, pady=2, font=16,
                                      width=buttons_width, command=lambda: self.toggle_view(3))
        #self.save_title = tk.Button(self.main_win, text='Save', fg="#f00", padx=2, pady=2, font=16, width=15,
        #                            command=lambda: self.toggle_view(4))
        self.hide_all = tk.Button(self.main_win, text='Hide all', fg="#f00", padx=2, pady=2, font=16, width=buttons_width,
                                  command=lambda: self.toggle_view(-1))
        self.settings_label = tk.Label(self.main_win, text='Settings', fg="#f00", padx=2, pady=2, font=16, width=buttons_width)

        # Labels
        padd_val = 4
        self.file_in_label = tk.Label(self.main_win, text='Source slide', pady=padd_val)
        self.file_out_label = tk.Label(self.main_win, text='Output path slide', pady=padd_val)
        self.pyr_selection_label = tk.Label(self.main_win, text='Saving Zoom', pady=padd_val)
        self.tile_size_label = tk.Label(self.main_win, text='Size (pixels)', pady=padd_val)
        self.tile_meters_label = tk.Label(self.main_win, text='1 pixel = ', pady=padd_val)
        self.tile_ratio_label = tk.Label(self.main_win, text='Roi intersection: ', pady=padd_val)
        self.tile_layer_label = tk.Label(self.main_win, text='Saving zoom:', pady=padd_val)
        self.stardist_bound_label = tk.Label(self.main_win, text='Min cell space:', pady=padd_val)
        self.zoom_text = tk.Label(self.main_win, text='x1', pady=padd_val)
        self.save_label = tk.Label(self.main_win, text='Saving Label: ', pady=padd_val)
        self.format_label = tk.Label(self.main_win, text='Format: ', pady=padd_val)
        self.next_file_label = tk.Label(self.main_win, text='Next file: ', pady=padd_val)
        self.previous_file_label = tk.Label(self.main_win, text='Previous file', pady=padd_val)
        self.layer_zoom_label = tk.Label(self.main_win, text='Zoom: ', pady=padd_val)
        self.ar_label = tk.Label(self.main_win, text='Add/Remove label: ', pady=padd_val)
        self.annotation_id_label = tk.Label(self.main_win, text='ID: ', pady=padd_val)
        self.annotation_id_remove_label = tk.Label(self.main_win, text='ID: ', pady=padd_val)
        self.annotation_name_label = tk.Label(self.main_win, text='name: ', pady=padd_val)
        self.annotation_color_label = tk.Label(self.main_win, text='color: ', pady=padd_val)
        self.tiles_color_label = tk.Label(self.main_win, text='tiles color: ', pady=padd_val)
        self.roi_label = tk.Label(self.main_win, text='Roi: ', pady=padd_val)
        self.roi_number_label = tk.Label(self.main_win, text='-1/-1: ', pady=padd_val)
        self.view_dimension_label = tk.Label(self.main_win, text='view_dimensions: ', pady=padd_val)
        self.draw_tiles_label = tk.Label(self.main_win, text='Draw Tiles: ', pady=padd_val)
        self.draw_roi_label = tk.Label(self.main_win, text='Show All: ', pady=padd_val)
        #self.draw_tiles_label = tk.Label(self.main_win, text='Show Tiles: ', pady=padd_val)

        # Checkbox
        self.draw_tiles_state = tk.BooleanVar()
        self.draw_tiles_state.set(False)
        self.draw_tiles_check = tk.Checkbutton(self.main_win, text='', variable=self.draw_tiles_state,
                                               command=self.draw_tiles_check)
        self.old_rois_state = tk.BooleanVar()
        self.old_rois_state.set(True)
        self.old_rois_check = tk.Checkbutton(self.main_win, text='Show rois',
                                             variable=self.old_rois_state, command=self.old_rois)

        # Spin box
        default_tile_size = tk.IntVar()
        default_tile_size.set(383)
        self.tile_size_spinbox = tk.Spinbox(from_=50, to=800, width=8, textvariable=default_tile_size,
                                            command=self.show_conversion)
        default_tile_ratio = tk.IntVar()
        default_tile_ratio.set(100)
        self.tile_ratio_spinbox = tk.Spinbox(from_=1, to=100, width=8, textvariable=default_tile_ratio,
                                             state='readonly')
        self.filter_bound = tk.IntVar()
        self.filter_bound.set(0)
        self.filter_spinbox = tk.Spinbox(from_=0, to=100, width=8, textvariable=self.filter_bound)
        self.layer_selection_spinbox = tk.Spinbox(from_=0, to=0, width=10)
        self.tile_layer = tk.IntVar()
        self.tile_layer.set(0)
        self.tile_layer_spinbox = tk.Spinbox(from_=0, to=0, width=8, textvariable=self.tile_layer,
                                             command=self.show_conversion, state='readonly')

        # Entry
        self.file_in_text = tk.Entry(self.main_win, width=text_width)
        self.file_out_text = tk.Entry(self.main_win, width=text_width)
        self.modify_label_text = tk.Entry(self.main_win, width=buttons_width + 5)
        self.add_id_text = tk.Entry(self.main_win, width=buttons_width + 5)
        self.add_name_text = tk.Entry(self.main_win, width=buttons_width + 5)
        self.remove_id_text = tk.Entry(self.main_win, width=buttons_width + 5)

        # Options menu
        self.labels = self.controller.get_labels()
        self.variable_labels = tk.StringVar(self.main_win)
        self.variable_labels.set(self.labels[0])  # default value
        self.last_value = self.labels[0]
        self.menu_labels = tk.OptionMenu(self.main_win, self.variable_labels, *self.labels, command=self.set_annotation)
        self.menu_labels.config(width=buttons_width)
        self.formats = ["png", "jpg"]
        self.variable = tk.StringVar(self.main_win)
        self.variable.set(self.formats[0])  # default value
        self.menu = tk.OptionMenu(self.main_win, self.variable, *self.formats)
        self.menu.config(width=buttons_width)

        # Buttons
        self.file_in_button = tk.Button(self.main_win, text='Browse...', width=buttons_width, command=self.file_in_browse)
        self.file_out_button = tk.Button(self.main_win, text='Browse...', width=buttons_width, command=self.file_out_browse)
        self.open_slide_button = tk.Button(self.main_win, text='Open slide', width=buttons_width, command=self.open_slide)
        self.close_slide_button = tk.Button(self.main_win, text='Close slide', width=buttons_width, command=self.close_slide)
        self.draw_roi_button = tk.Button(self.main_win, text='Draw ROI', width=buttons_width, command=self.start_draw_roi)
        self.reset_roi_button = tk.Button(self.main_win, text='Reset ROI', width=buttons_width, command=self.reset_roi)
        self.modify_start = tk.Button(self.main_win, text='Modify Point', width=buttons_width, command=self.modify_roi)
        self.modify_stop = tk.Button(self.main_win, text='Modify Stop', width=buttons_width, command=self.stop_modify_roi)
        self.stardist_button = tk.Button(self.main_win, text='Execute Filter', width=buttons_width, command=self.execute_filters)
        self.remove_tiles_start = tk.Button(self.main_win, text='Remove Tiles', width=buttons_width, command=self.remove_tiles)
        self.add_tiles_start = tk.Button(self.main_win, text='Add Tiles', width=buttons_width, command=self.add_tiles)
        self.modify_tiles_stop = tk.Button(self.main_win, text='Stop', width=2*buttons_width, command=self.stop_tiles)
        self.next_file = tk.Button(self.main_win, text='Next', width=buttons_width, command=self.get_next_file)
        self.previous_file = tk.Button(self.main_win, text='Previous', width=buttons_width, command=self.get_previous_file)
        self.add_label_button = tk.Button(self.main_win, text='Add Label', width=buttons_width, command=self.add_label)
        self.remove_label_button = tk.Button(self.main_win, text='Remove Label', width=buttons_width, command=self.remove_label)
        self.undo = tk.Button(self.main_win, text='Undo', width=buttons_width, command=self.roi_back)
        self.redo = tk.Button(self.main_win, text='Redo', width=buttons_width, command=self.roi_forward)
        self.generate_save_button = tk.Button(self.main_win, text='Generate+Save tiles', command=self.generate_save_tiles)
        self.annotation_color_button = tk.Button(self.main_win, text='color', width=buttons_width, command=lambda: self.choose_color(0))
        self.tile_color_button = tk.Button(self.main_win, text='color', width=buttons_width, command=lambda: self.choose_color(1))
        self.add_roi_button = tk.Button(self.main_win, text='Add Roi', width=buttons_width, command=self.add_roi)
        self.next_roi_button = tk.Button(self.main_win, text='Next Roi', width=buttons_width, command=self.next_roi)
        self.previous_roi_button = tk.Button(self.main_win, text='Previous Roi', width=buttons_width, command=self.previous_roi)
        self.remove_roi_button = tk.Button(self.main_win, text='Remove Roi', width=buttons_width, command=self.remove_roi)
        self.apply_filter_button = tk.Button(self.main_win, text='Apply Filter', width=buttons_width, command=self.apply_filter)
        self.reset_filter_button = tk.Button(self.main_win, text='Reset Filter', width=buttons_width, command=self.reset_filter)
        self.ruler_button = tk.Button(self.main_win, text='Ruler', command=self.ruler)
        self.save_tiles_button = tk.Button(self.main_win, text='Save active Roi', width=buttons_width, command=self.save_tiles)
        self.generate_tiles_button = tk.Button(self.main_win, text='Generate tiles', width=buttons_width, command=self.generate_tiles)
        self.save_all_tiles_button = tk.Button(self.main_win, text='Save all Roi', width=buttons_width, command=self.save_all_tiles)
        self.generate_all_tiles_button = tk.Button(self.main_win, text='Generate tiles all Roi', width=buttons_width, command=self.generate_all_tiles)
        self.rotate_left_button = tk.Button(self.main_win, text='Rotate L', command=self.rotate_left)
        self.rotate_right_button = tk.Button(self.main_win, text='Rotate R', command=self.rotate_right)

        # Scale
        self.zoom = tk.Scale(self.main_win, length=540, from_=0, to=9, command=self.scale_handler, showvalue=False)

        # separators
        self.input_separator = ttk.Separator(self.main_win, orient=tk.HORIZONTAL)
        self.thumbnail_separator = ttk.Separator(self.main_win, orient=tk.VERTICAL)
        self.roi1_separator = ttk.Separator(self.main_win, orient=tk.VERTICAL)
        self.roi2_separator = ttk.Separator(self.main_win, orient=tk.VERTICAL)
        self.roi3_separator = ttk.Separator(self.main_win, orient=tk.VERTICAL)
        self.roi4_separator = ttk.Separator(self.main_win, orient=tk.VERTICAL)

        # Create canvas
        self.canvas = None
        self.figure_dpi = 100
        self.x0 = 0
        self.x1 = 0
        self.y0 = 0
        self.y1 = 0
        self.figure = None
        self.axes = None
        self.image_size_x = 0
        self.image_size_y = 0

        # Set positions of objects
        self.figure_dpi = 100
        self.image_size_x, self.image_size_y = self.controller.get_windows_dimensions()
        self.window_size_x = self.image_size_x / self.figure_dpi
        self.window_size_y = self.image_size_y / self.figure_dpi
        self.figure = plt.Figure([self.window_size_x, self.window_size_y])
        self.canvas = FigureCanvasTkAgg(self.figure, self.main_win)
        self.axes = self.figure.add_axes([0, 0, 1, 1])
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['bottom'].set_visible(False)
        self.axes.spines['left'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        #self.axes.imshow(np.zeros((self.image_size_y, self.image_size_x, 3)))
        #self.canvas.get_tk_widget().grid(column=1, row=8, columnspan=9, rowspan=2)
        #self.canvas.draw()

        self.set_positions()

        # Canvas Objects
        self.move_artist = None
        self.modify_artist = []
        self.roi_artist = None
        self.tile_artist = []
        self.modify_tiles_artist = []
        self.remove_artist = []
        self.add_artists = []
        self.black_image = np.ones((self.image_size_y, self.image_size_x, 3))
        self.image = None
        self.thumbnails = None
        self.old_roi_artist = []
        self.thumbnails_image = None
        self.full_image = None
        self.value = 0

        # Set view list by type
        self.file_manager = [self.file_in_label, self.file_in_text, self.file_in_button, self.next_file,
                             self.next_file_label, self.previous_file, self.previous_file_label, self.file_out_label,
                             self.file_out_text, self.file_out_button, self.open_slide_button, self.close_slide_button,
                             self.input_separator, self.settings_label, self.save_label, self.menu_labels,
                             self.annotation_id_label, self.add_id_text, self.annotation_name_label,
                             self.add_name_text, self.annotation_color_label, self.annotation_color_button,
                             self.add_label_button, self.annotation_id_remove_label, self.remove_id_text,
                             self.remove_label_button, self.tiles_color_label, self.tile_color_button,
                             self.thumbnail_separator]
        self.roi_manager = [self.old_rois_check, self.roi1_separator, self.roi_label, self.roi_number_label,
                            self.roi2_separator, self.add_roi_button, self.roi3_separator, self.draw_roi_button,
                            self.modify_start, self.undo, self.roi4_separator, self.pyr_selection_label,
                            self.draw_roi_label, self.next_roi_button, self.previous_roi_button, self.remove_roi_button,
                            self.reset_roi_button, self.modify_stop, self.redo, self.menu_labels,
                            self.generate_save_button, self.input_separator]
        self.tiles_manager = [self.tile_size_spinbox, self.tile_ratio_spinbox, self.tile_layer_spinbox,
                              self.draw_tiles_check, self.pyr_selection_label, self.tile_size_label,
                              self.tile_meters_label, self.tile_ratio_label, self.tile_layer_label,
                              self.layer_zoom_label, self.remove_tiles_start, self.add_tiles_start,
                              self.modify_tiles_stop, self.generate_tiles_button, self.save_label, self.draw_tiles_label,
                              self.generate_all_tiles_button, self.save_all_tiles_button]
        self.filter_manager = [self.stardist_button, self.filter_spinbox, self.stardist_bound_label,
                               self.apply_filter_button, self.reset_filter_button]

        self.save_manager = [self.save_tiles_button, self.add_label_button, self.remove_label_button, self.menu,
                             self.menu_labels,
                             self.modify_label_text, self.save_label, self.format_label, self.ar_label]

        # Start by showing input files
        self.toggle_view(0)

    def add_label(self):
        id = self.add_id_text.get()
        name = self.add_name_text.get()
        self.controller.add_label(id, name, self.color)

        self.add_id_text.delete(0, 'end')
        self.add_name_text.delete(0, 'end')

        self.update_options()

    def remove_label(self):
        id = self.remove_id_text.get()
        self.controller.remove_label(id)
        self.remove_id_text.delete(0, 'end')

        self.update_options()

    def update_options(self):
        self.labels = self.controller.get_labels()
        self.variable_labels.set('')
        self.menu_labels ['menu'].delete(0, 'end')
        for label in self.labels:
            self.menu_labels['menu'].add_command(label=label, command=tk._setit(self.variable_labels, label, self.set_annotation))#, command=tk._setit(var, choice))
        self.variable_labels.set(self.labels[0])
    def open_slide(self):
        self.reset_roi()
        self.close_slide()

        w = self.canvas.get_tk_widget()
        w.destroy()


        print("Opening slide in path: ", self.file_in_text.get())

        self.controller.open_slide(self.file_in_text.get(),  self.file_out_text.get())

        self.image_size_x, self.image_size_y = self.controller.get_windows_dimensions()
        self.figure_dpi = 100
        self.window_size_x = self.image_size_x / self.figure_dpi
        self.window_size_y = self.image_size_y / self.figure_dpi
        self.figure = plt.Figure([self.window_size_x, self.window_size_y])
        self.canvas = FigureCanvasTkAgg(self.figure, self.main_win)
        self.axes = self.figure.add_axes([0, 0, 1, 1])
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['bottom'].set_visible(False)
        self.axes.spines['left'].set_visible(False)
        self.axes.spines['right'].set_visible(False)

        self.x0 = self.axes.get_position().x0
        self.x1 = self.axes.get_position().x1
        self.y0 = self.axes.get_position().y0
        self.y1 = self.axes.get_position().y1

        self.canvas.mpl_connect('button_press_event', self.mouse_click_handler)
        self.canvas.mpl_connect('scroll_event', self.mouse_wheel_handler)
        self.canvas.mpl_connect('motion_notify_event', self.mouse_move_handler)
        self.canvas.mpl_connect('key_press_event', self.key_press_handler)
        self.canvas.mpl_connect('button_release_event', self.mouse_release_handler)

        if self.value != 0:
            self.canvas.get_tk_widget().grid(column=1, row=8, columnspan=9, rowspan=5)
        else:
            self.canvas.get_tk_widget().grid(column=1, row=12, columnspan=9, rowspan=5)

        self.update_slide(self.controller.get_image())
        self.set_zoom()
        self.show_conversion()
        self.roi_number_label.configure(text=self.controller.get_active_id_label())
        _, maxl, _, _ = self.controller.get_level()
        self.tile_layer_spinbox.config(to=maxl)
        self.canvas.get_tk_widget().bind("<Leave>", self.remove_move_line)

        f1, f2 = self.controller.get_near_files(self.file_in_text.get())

        self.previous_file_label.configure(text="Previous file: " + f1)
        self.next_file_label.configure(text="Next file: " + f2)

    def file_in_browse(self):
        filename = tkinter.filedialog.askopenfilename(initialdir='/home/leonardo/Documents',
                                                      filetypes=[("tif files", "*.tif"), ("svs files", "*.svs"),
                                                                 ("ndpi files", "*.ndpi"), ("all files", "*.*")])
        self.file_in_text.configure(state=tk.NORMAL)
        self.file_in_text.delete(0, "end")
        self.file_in_text.insert(0, filename)

        self.file_out_text.configure(state=tk.NORMAL)
        if len(self.file_out_text.get()) == 0:
            self.file_out_text.insert(0, os.path.dirname(filename))

    def file_out_browse(self):
        filename = tkinter.filedialog.askdirectory(initialdir=path.dirname(self.file_in_text.get()))
        self.file_out_text.configure(state=tk.NORMAL)
        self.file_out_text.delete(0, "end")
        self.file_out_text.insert(0, filename)

    def update_slide(self, image):
        if self.image is not None:
            self.image.remove()
            self.image = None
        self.image = self.axes.imshow(image)
        self.canvas.draw()

    def close_slide(self):
        if self.image is not None:
            self.reset_roi()
            self.image.remove()
            self.image = None

        self.controller.close_slide()
        for artist in self.old_roi_artist:
            artist.remove()
        self.old_roi_artist = []
        self.canvas.draw()

    def mouse_click_handler(self, event):
        event.x /= self.image_size_x
        event.y /= self.image_size_y
        out = self.controller.click_event(event)
        if out is not None:
            tk.messagebox.showinfo("Measure", "Dimension = "+str(out[0])+" millimeters / "+str(out[1])+" pixels \n")

        self.draw_roi_canvas()
        if self.move_artist is not None:
            self.move_artist.remove()
            self.move_artist = None
        self.draw_point_canvas()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.canvas.draw()

    def mouse_release_handler(self, event):
        event.x /= self.image_size_x
        event.y /= self.image_size_y

        self.controller.release_event(event)

        self.draw_roi_canvas()
        if self.move_artist is not None:
            self.move_artist.remove()
            self.move_artist = None
        self.draw_tiles()
        self.draw_point_canvas()
        self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.canvas.draw()

    def mouse_wheel_handler(self, event):
        event.x /= self.image_size_x
        event.y /= self.image_size_y
        self.controller.wheel_event(event)
        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.set_zoom()
        self.canvas.draw()

    def mouse_move_handler(self, event):
        event.x /= self.image_size_x
        event.y /= self.image_size_y
        line = self.controller.move_event(event)
        if self.move_artist is not None:
            self.move_artist.remove()
            self.move_artist = None
        if line[0] != -1:
            self.move_artist = self.figure.add_artist(lines.Line2D([line[0][0], line[1][0]], [line[0][1], line[1][1]]))

        self.draw_roi_canvas()
        self.draw_point_canvas()
        if event.button is MouseButton.MIDDLE:
            #self.draw_tiles()
            self.remove_all_tiles()
        else:
            self.draw_tiles()
            self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.canvas.draw()

    def key_press_handler(self, event):
        event.x /= self.image_size_x
        event.y /= self.image_size_y
        self.controller.key_event(event)

        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.set_zoom()
        self.canvas.draw()


    def scale_handler(self, event):
        self.controller.set_zoom(self.zoom.get())
        self.draw_roi_canvas()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.draw_point_canvas()
        self.update_slide(self.controller.get_image())
        self.set_zoom()
        self.canvas.draw()
    def remove_move_line(self, event):
        a = 1
    def add_roi(self):
        self.controller.add_roi()
        self.start_draw_roi()
        self.roi_number_label.configure(text=self.controller.get_active_id_label())
        self.set_annotation(self.last_value)
    def remove_roi(self):

        answer = askyesno("Remove roi", "If you confirm all data of the roi will be removed")
        if answer:
            self.controller.remove_roi()
            self.roi_number_label.configure(text=self.controller.get_active_id_label())
            self.draw_roi_canvas()
            self.draw_point_canvas()
            self.draw_tiles()
            self.canvas.draw()
    def start_draw_roi(self):
        self.controller.draw_roi()
        self.roi_number_label.configure(text=self.controller.get_active_id_label())
    def next_roi(self):
        self.controller.select_next_roi()
        self.roi_number_label.configure(text=self.controller.get_active_id_label())
        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()
    def previous_roi(self):
        self.controller.select_previous_roi()
        self.roi_number_label.configure(text=self.controller.get_active_id_label())
        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()
    def reset_roi(self):
        self.controller.reset_roi()
        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()
    def modify_roi(self):
        self.controller.start_modify_roi()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()
    def stop_modify_roi(self):
        self.controller.stop_modify_roi()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()
    def roi_back(self):
        print("back")
        self.controller.rollback()
        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()
    def roi_forward(self):
        self.controller.rollforward()
        self.draw_roi_canvas()
        self.draw_point_canvas()
        self.draw_tiles()
        self.canvas.draw()

    def set_annotation(self, label):
        print("Changed label to: ", label)
        self.last_value = label
        self.controller.set_label(label)
        self.draw_roi_canvas()
        self.draw_tiles()
        self.canvas.draw()

    def old_rois(self):
        self.draw_roi_canvas()
        self.canvas.draw()
    def show_conversion(self):

        meters = self.controller.convert_to_meters(self.tile_layer_spinbox.get(), 1)
        meters = float(meters)
        self.tile_meters_label.configure(text="1 pixel = " + str(meters) + " micron")

        currl, maxl, max_zoom, downsample = self.controller.get_level(level=int(self.tile_layer.get()))

        value = max_zoom / downsample
        self.layer_zoom_label.configure(text="Zoom: x" + str(round(value, 2)))

    def save_tiles(self):
        print("Start saving Tiles")
        extension = self.variable.get()
        self.controller.save(extension)

    def save_all_tiles(self):
        print("Start saving Tiles")
        extension = self.variable.get()
        self.controller.save_all(extension)

    def generate_tiles(self):
        self.controller.generate_tiles(int(self.tile_size_spinbox.get()), int(self.tile_layer_spinbox.get()), int(self.tile_ratio_spinbox.get()))
        self.draw_tiles()
        self.canvas.draw()

    def generate_all_tiles(self):
        self.controller.generate_all_tiles(int(self.tile_size_spinbox.get()), int(self.tile_layer_spinbox.get()), int(self.tile_ratio_spinbox.get()))
        self.draw_tiles()
        self.canvas.draw()

    def remove_tiles(self):
        self.controller.remove_tiles_in_roi()
    def add_tiles(self):
        self.controller.add_tiles_in_roi()
    def stop_tiles(self):
        self.controller.stop_tiles()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.canvas.draw()
    def get_next_file(self):
        actual_file = self.file_in_text.get()
        if len(actual_file) > 0:
            new_previous, new_next, new_file = self.controller.get_next_file(actual_file)
            self.next_file_label.configure(text="Next file: " + new_next)
            self.previous_file_label.configure(text="Previous file: " + new_previous)
            self.file_in_text.delete(0, len(self.file_in_text.get()))
            self.file_in_text.insert(0, new_file)
    def get_previous_file(self):
        actual_file = self.file_in_text.get()
        if len(actual_file) > 0:
            new_previous, new_next, new_file = self.controller.get_next_file(actual_file)
            self.next_file_label.configure(text="Next file: " + new_next)
            self.previous_file_label.configure(text="Previous file: " + new_previous)
            self.file_in_text.delete(0, len(self.file_in_text.get()))
            self.file_in_text.insert(0, new_file)
    def rotate_left(self):
        self.controller.rotate_left()
        self.draw_roi_canvas()
        if self.move_artist is not None:
            self.move_artist.remove()
            self.move_artist = None
        self.draw_point_canvas()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.canvas.draw()
    def rotate_right(self):
        self.controller.rotate_right()
        self.draw_roi_canvas()
        if self.move_artist is not None:
            self.move_artist.remove()
            self.move_artist = None
        self.draw_point_canvas()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.update_slide(self.controller.get_image())
        self.canvas.draw()

    def generate_save_tiles(self):
        self.generate_tiles()
        self.save_tiles()
    def reset_filter(self):
        self.controller.reset_filter()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.canvas.draw()
    def apply_filter(self):
        self.controller.apply_filter()
        self.draw_tiles()
        self.draw_modify_tiles()
        self.canvas.draw()

    def execute_filters(self):
        newWindow = tk.Toplevel()
        # sets the title of the
        # Toplevel widget
        newWindow.title("Computing Filtering")
        # sets the geometry of toplevel
        newWindow.geometry("400x200")

        # A Label widget to show in toplevel
        tk.Label(newWindow, text="Wait while computing the filter", font=18).grid(sticky="NW")

        newWindow.update_idletasks()
        newWindow.update()

        self.controller.filter_image(float(self.filter_bound.get()) / 100)

        self.draw_tiles()
        self.draw_modify_tiles()
        self.canvas.draw()
        #self.close_windows()

        newWindow.destroy()

    def ruler(self):
        self.controller.start_measure()

    def set_zoom(self):
        currl, maxl, max_zoom, downsample = self.controller.get_level()
        self.zoom.configure(to=maxl)
        self.zoom.set(currl)
        value = max_zoom / downsample
        self.zoom_text.configure(text="x" + str(round(value, 2)))

    def draw_roi_canvas(self):
        # The Line2D artist needs all the x be packed into an array - the same for y

        active, others, color_active, colors = self.controller.get_roi(get_all=self.old_rois_state.get())

        if self.roi_artist is not None:
            self.roi_artist.remove()
            self.roi_artist = None

        for artist in self.old_roi_artist:
            artist.remove()
        self.old_roi_artist = []

        if len(active) > 0:
            self.roi_artist = self.figure.add_artist(lines.Line2D([i[0] for i in active], [i[1] for i in active],
                                                                  color=color_active))
        if len(others) > 0:
            for i in range(len(others)):
                array = np.array(others[i])
                self.old_roi_artist.append(self.figure.add_artist(patches.Polygon(array, color=colors[i],
                                                                                  closed=True, alpha=0.35)))

    def draw_point_canvas(self):
        if len(self.modify_artist) > 0:
            self.modify_artist[0].remove()
            self.modify_artist[1].remove()
            self.modify_artist = []

        point = self.controller.get_modify_point()
        if len(point) > 0:

            x, y = point
            self.modify_artist.append(self.figure.add_artist(matplotlib.patches.Circle(
                (x, y), radius=0.01, color='orange')))
            self.modify_artist.append(self.figure.add_artist(matplotlib.patches.Circle(
                (x, y), radius=0.005, color='black')))

    def remove_all_tiles(self):
        if len(self.tile_artist) > 0:
            for curr_artist in self.tile_artist:
                curr_artist.remove()
            self.tile_artist = []

        if len(self.modify_tiles_artist) > 0:
            for curr_artist in self.modify_tiles_artist:
                curr_artist.remove()
            self.modify_tiles_artist = []

    def draw_tiles_check(self):
        self.draw_tiles()
        self.draw_modify_tiles()
        self.canvas.draw()

    def draw_tiles(self):
        if len(self.tile_artist) > 0:
            for curr_artist in self.tile_artist:
                curr_artist.remove()
            self.tile_artist = []

        # If checkbox is checked
        if self.draw_tiles_state.get():

            active_patches = self.controller.get_tiles()

            if len(active_patches) < 1:
                return

            point = active_patches[0][:2]
            curr_w = active_patches[0][2]
            curr_h = active_patches[0][3]

            i = 1
            while i < len(active_patches):
                if not ((point[0] == active_patches[i][0]) | (abs(point[0] - active_patches[i][0]) / curr_w > 1.5)):
                    break
                i += 1
            if i < len(active_patches):
                curr_w = abs(point[0] - active_patches[i][0])

            i = 1
            while i < len(active_patches):
                if not ((point[1] == active_patches[i][1]) | (abs(point[1] - active_patches[i][1]) / curr_h > 1.5)):
                    break
                i += 1
            if i < len(active_patches):
                curr_h = abs(point[1] - active_patches[i][1])

            for key, curr_patch in enumerate(active_patches):
                # print('Coordinate: ' + str((curr_patch[0], curr_patch[1], curr_patch[2], curr_patch[3])))
                if (curr_patch[0] <= 1) & (curr_patch[0] + curr_patch[2] >= 0) & (curr_patch[1] <= 1) & \
                        (curr_patch[1] + curr_patch[3] >= 0):
                    curr_artist = self.figure.add_artist(patches.Rectangle((curr_patch[0], curr_patch[1]), curr_w,
                                                                           curr_h, fill=False, linestyle='-',
                                                                           color='red'))
                    self.tile_artist.append(curr_artist)

    def draw_modify_tiles(self):
        if len(self.modify_tiles_artist) > 0:
            for curr_artist in self.modify_tiles_artist:
                curr_artist.remove()
            self.modify_tiles_artist = []
        # draw roi
        roi_selection = self.controller.get_modify_roi()

        if len(roi_selection) > 1:
            self.modify_tiles_artist.append(
                self.figure.add_artist(lines.Line2D(roi_selection[0], roi_selection[1], color="gray")))
        # draw the tiles

        # If checkbox is checked
        if self.draw_tiles_state.get():

            active_patches = self.controller.get_modify_tiles()

            if len(active_patches) < 1:
                return

            point = active_patches[0][:2]
            curr_w = active_patches[0][2]
            curr_h = active_patches[0][3]

            for curr_patch in active_patches:
                # print('Coordinate: ' + str((curr_patch[0], curr_patch[1], curr_patch[2], curr_patch[3])))
                if (curr_patch[0] <= 1) & (curr_patch[0] + curr_patch[2] >= 0) & (curr_patch[1] <= 1) & \
                        (curr_patch[1] + curr_patch[3] >= 0):
                    curr_artist = self.figure.add_artist(patches.Rectangle((curr_patch[0], curr_patch[1]), curr_w,
                                                                           curr_h, fill=False, linestyle='-',
                                                                           color='black', ))
                    self.modify_tiles_artist.append(curr_artist)

    def choose_color(self, s):
        # variable to store hexadecimal code of color
        color_code = colorchooser.askcolor(title="Choose color")
        if s == 0:
            self.color = color_code[1]
        else:
            self.controller.set_tiles_color(color_code[1])

    def toggle_view(self, value):
        for e in self.file_manager + self.roi_manager + self.tiles_manager + self.filter_manager + self.save_manager:
            e.grid_remove()

        self.value = value
        #self.thumbnails_canvas.get_tk_widget().grid_remove()

        if value != 0:
            self.rotate_left_button.grid(column=0, row=8)
            self.rotate_right_button.grid(column=0, row=9)
            self.ruler_button.grid(column=0, row=10)
            self.zoom_text.grid(column=0, row=11, pady=(20, 0))
            self.zoom.grid(column=0, row=12, pady=(0, 0), padx=0)
            self.canvas.get_tk_widget().grid(column=1, row=8, columnspan=9, rowspan=5)
            self.canvas.draw()
        else:
            self.rotate_left_button.grid(column=0, row=12)
            self.rotate_right_button.grid(column=0, row=13)
            self.ruler_button.grid(column=0, row=14)
            self.zoom_text.grid(column=0, row=15, pady=(20, 0))
            self.zoom.grid(column=0, row=16, pady=(0, 0), padx=0)
            self.canvas.get_tk_widget().grid(column=1, row=12, columnspan=9, rowspan=5)
            self.canvas.draw()

        if value == 0:
            self.show_file_manager()
        elif value == 1:
            self.show_roi_manager()
        elif value == 2:
            self.show_tile_manger()
        elif value == 3:
            self.show_filter_manager()
            # self.popupmsg("These function may be very slow if computed on CPU.")
            tk.messagebox.showinfo("Warning.", "These functions may be very slow on CPU.\nWe suggest to use a "
                                               "Nvidia GPU with Cuda")
        #elif value == 4:
            #self.show_save_manager()

    def set_positions(self):
        curr_row = 0
        self.file_title.grid(row=curr_row, column=0, columnspan=2)
        self.roi_title.grid(row=curr_row, column=2, columnspan=2)
        self.tile_title.grid(row=curr_row, column=4, columnspan=2)
        self.filter_title.grid(column=6, row=curr_row, columnspan=2)
        #self.save_title.grid(column=5, row=curr_row)
        self.hide_all.grid(row=curr_row, column=8, columnspan=2)

        curr_row += 1
        ttk.Separator(self.main_win, orient=tk.HORIZONTAL).grid(column=0, row=curr_row, columnspan=8, sticky='we',
                                                                pady=5, padx=5)

        curr_row += 6
        #self.separators.append(ttk.Separator(self.main_win, orient=tk.HORIZONTAL).grid(column=0, row=curr_row,
        #                                                                               columnspan=8, sticky='we',
        #                                                                               pady=5, padx=5))

        #curr_row += 1
        #self.zoom_text.grid(column=0, row=curr_row, pady=(20, 0))

        #curr_row += 1
        #self.zoom.grid(column=0, row=curr_row, pady=(0, 0), padx=0)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.main_win.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.main_win.attributes("-fullscreen", False)
        return "break"

    def show_file_manager(self):
        row_number = 2
        col_span = 3
        # row
        self.file_in_label.grid(column=0, row=row_number)
        self.file_in_text.grid(column=1, row=row_number, columnspan=col_span)
        self.file_in_button.grid(column=4, row=row_number)

        # row
        row_number += 1
        self.next_file.grid(column=0, row=row_number)
        self.next_file_label.grid(column=1, row=row_number, columnspan=col_span)
        self.previous_file.grid(column=4, row=row_number)
        self.previous_file_label.grid(column=5, row=row_number, columnspan=col_span)

        # row
        row_number += 1
        self.file_out_label.grid(column=0, row=row_number)
        self.file_out_text.grid(column=1, row=row_number, columnspan=col_span)
        self.file_out_button.grid(column=4, row=row_number)

        self.open_slide_button.grid(column=5, row=row_number)
        self.close_slide_button.grid(column=6, row=row_number)

        #row
        row_number += 1
        self.input_separator.grid(column=0, row=row_number, sticky='we', pady=(5, 5), padx=0, columnspan=7)

        # row
        row_number += 1
        self.settings_label.grid(column=0, row=row_number, columnspan=3)

        # row
        row_number += 1
        self.save_label.grid(column=0, row=row_number)
        self.menu_labels.grid(column=1, row=row_number)

        # row
        row_number += 1
        self.annotation_id_label.grid(column=0, row=row_number)
        self.add_id_text.grid(column=1, row=row_number)
        self.annotation_name_label.grid(column=2, row=row_number)
        self.add_name_text.grid(column=3, row=row_number)
        self.annotation_color_label.grid(column=4, row=row_number)
        self.annotation_color_button.grid(column=5, row=row_number)
        self.add_label_button.grid(column=6, row=row_number)

        # row
        row_number += 1
        self.annotation_id_remove_label.grid(column=0, row=row_number)
        self.remove_id_text.grid(column=1, row=row_number)
        self.remove_label_button.grid(column=6, row=row_number)

        # row
        row_number += 1

        # row
        row_number += 1
        self.tiles_color_label.grid(column=0, row=row_number)
        self.tile_color_button.grid(column=1, row=row_number)
        self.format_label.grid(column=3, row=row_number)
        self.menu.grid(column=4, row=row_number)

    def show_roi_manager(self):

        self.old_rois_check.grid(column=0, row=2)
        self.roi1_separator.grid(column=1, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.roi_label.grid(column=2, row=2)
        self.roi_number_label.grid(column=3, row=2)
        self.roi2_separator.grid(column=4, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.add_roi_button.grid(column=5, row=2)
        self.roi3_separator.grid(column=6, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.draw_roi_button.grid(column=7, row=2)
        self.modify_start.grid(column=8, row=2)
        self.undo.grid(column=9, row=2)
        self.roi4_separator.grid(column=10, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.pyr_selection_label.grid(column=11, row=2)

        self.draw_roi_label.grid(column=0, row=3)
        self.next_roi_button.grid(column=2, row=3)
        self.previous_roi_button.grid(column=3, row=3)
        self.remove_roi_button.grid(column=5, row=3)
        self.reset_roi_button.grid(column=7, row=3)
        self.modify_stop.grid(column=8, row=3)
        self.redo.grid(column=9, row=3)
        self.menu_labels.grid(column=11, row=3)
        self.generate_save_button.grid(column=12, row=3)

        self.input_separator.grid(column=0, row=4, sticky='we', pady=(5, 5), padx=0, columnspan=12)

    def show_tile_manger(self):
        self.roi_label.grid(column=0, row=2)
        self.roi_number_label.grid(column=1, row=2)
        self.roi1_separator.grid(column=2, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.draw_tiles_check.grid(row=2, column=3)
        self.roi2_separator.grid(column=4, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.tile_layer_label.grid(row=2, column=5)
        self.tile_layer_spinbox.grid(row=2, column=6)
        self.layer_zoom_label.grid(row=2, column=7)
        self.tile_meters_label.grid(row=2, column=8)
        self.roi3_separator.grid(column=9, row=2, ipady=20, padx=10, pady=10, rowspan=2)
        self.add_tiles_start.grid(row=2, column=10)
        self.remove_tiles_start.grid(row=2, column=11)

        self.next_roi_button.grid(column=0, row=3)
        self.previous_roi_button.grid(column=1, row=3)
        self.draw_tiles_label.grid(column=3, row=3)
        self.tile_ratio_label.grid(row=3, column=5)
        self.tile_ratio_spinbox.grid(row=3, column=6)
        self.tile_size_label.grid(row=3, column=7)
        self.tile_size_spinbox.grid(row=3, column=8)
        self.modify_tiles_stop.grid(row=3, column=10, columnspan=2)

        self.generate_tiles_button.grid(row=4, column=0, columnspan=2)
        self.generate_all_tiles_button.grid(row=4, column=2, columnspan=2)
        self.save_tiles_button.grid(column=5, row=4, columnspan=2)
        self.save_all_tiles_button.grid(column=7, row=4, columnspan=2)

    def show_filter_manager(self):
        self.stardist_bound_label.grid(column=0, row=2)
        self.filter_spinbox.grid(column=1, row=2)
        #self.stardist_filter_check.grid(column=2, row=2)
        #self.artifact_filter_check.grid(column=3, row=2)
        self.stardist_button.grid(column=4, row=2)
        self.apply_filter_button.grid(column=5, row=2)
        self.reset_filter_button.grid(column=6, row=2)

    def loop(self):
        self.main_win.mainloop()


def test_main_win_class():
    mw = ViewTk()
    mw.loop()

def start_windows():
    print("INSIDE")
    newWindow = tk.Toplevel()
    # sets the title of the
    # Toplevel widget
    newWindow.title("New Window")
    # sets the geometry of toplevel
    newWindow.geometry("200x200")

    # A Label widget to show in toplevel
    tk.Label(newWindow, text = "Wait").grid(row=0, column=0)
    pb = ttk.Progressbar(
        newWindow,
        orient='horizontal',
        mode='indeterminate',
        length=280
    )
    pb.grid(column=0, row=1, columnspan=2, padx=10, pady=20)
    pb.start()

    return newWindow


