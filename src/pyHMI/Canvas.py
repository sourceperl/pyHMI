import tkinter as tk
from tkinter import font

from .Colors import (
    BLUE,
    GRAY,
    GREEN,
    PINK,
    PIPE_WIDTH,
    RED,
    VALVE_COLOR,
    VALVE_DEF,
    VALVE_ERR,
    WHITE,
    color_tags_valve,
    color_valve,
)


class SimpleValve(object):
    def __init__(self, canvas):
        """
        SimpleValve draw valves (func draw_valve) on canvas.
        Default valve size is 40x30 you can change it with zoom params.

        :param canvas: Tk canvas to draw
        """
        self.canvas = canvas

    def draw_valve(self, x, y, name, label=None, align='h', zoom=1.0):
        zm = float(zoom)
        def_font = font.Font(size=int(12 * zm))
        args = {'fill': VALVE_COLOR[VALVE_ERR], 'outline': VALVE_COLOR[VALVE_ERR], 'tag': name}
        if align in ('H', 'h'):
            # background
            self.canvas.create_rectangle(x - 30 * zm, y - 20 * zm, x + 30 * zm, y + 20 * zm, fill=GRAY, outline=GRAY)
            # body
            self.canvas.create_polygon(x - 30 * zm, y - 20 * zm, x, y, x - 30 * zm, y + 20 * zm, **args)
            self.canvas.create_polygon(x + 30 * zm, y - 20 * zm, x, y, x + 30 * zm, y + 20 * zm, **args)
            if label is not None:
                self.canvas.create_text(x, y + 35 * zm, text=str(label), font=def_font, fill=WHITE)
        elif align in ('V', 'v'):
            # background
            self.canvas.create_rectangle(x - 20 * zm, y - 30 * zm, x + 20 * zm, y + 30 * zm, fill=GRAY, outline=GRAY)
            # body
            self.canvas.create_polygon(x - 20 * zm, y - 30 * zm, x, y, x + 20 * zm, y - 30 * zm, **args)
            self.canvas.create_polygon(x - 20 * zm, y + 30 * zm, x, y, x + 20 * zm, y + 30 * zm, **args)
            if label is not None:
                self.canvas.create_text(x + 35 * zm, y, text=str(label), font=def_font, fill=WHITE)

    def anim(self, name, fdc_open, fdc_close):
        color = color_valve(fdc_open, fdc_close)
        self.canvas.itemconfigure(name, fill=color, outline=color)

    def tag_anim(self, name, tag_fdc_open, tag_fdc_close):
        color = color_tags_valve(tag_fdc_open, tag_fdc_close)
        self.canvas.itemconfigure(name, fill=color, outline=color)


class MotorValve(object):
    def __init__(self, canvas):
        """
        MotorValve draw valves (func draw_valve) on canvas.
        Default valve size is 40x30 you can change it with zoom params.

        :param canvas: Tk canvas to draw
        """
        self.canvas = canvas

    def draw_valve(self, x, y, name, label=None, align='h', zoom=1.0):
        zm = float(zoom)
        def_font = font.Font(size=int(12 * zm))
        head_name = str(name) + '_HEAD'
        v_args = {'fill': VALVE_COLOR[VALVE_ERR], 'outline': VALVE_COLOR[VALVE_ERR], 'tag': name}
        h_args = {'fill': VALVE_COLOR[VALVE_ERR], 'outline': VALVE_COLOR[VALVE_ERR], 'tag': head_name}
        if align in ('H', 'h'):
            # background
            self.canvas.create_rectangle(x - 30 * zm, y - 20 * zm, x + 30 * zm, y + 20 * zm, fill=GRAY, outline=GRAY)
            # head
            self.canvas.create_rectangle(x - 4 * zm, y, x + 4 * zm, y - 20 * zm, **h_args)
            self.canvas.create_rectangle((x - 10 * zm, y - 16 * zm), (x + 10 * zm, y - 26 * zm), **h_args)
            # body
            self.canvas.create_polygon(x - 30 * zm, y - 20 * zm, x, y, x - 30 * zm, y + 20 * zm, **v_args)
            self.canvas.create_polygon(x + 30 * zm, y - 20 * zm, x, y, x + 30 * zm, y + 20 * zm, **v_args)
            if label is not None:
                self.canvas.create_text(x, y + 35 * zm, text=str(label), font=def_font, fill=WHITE)
        elif align in ('V', 'v'):
            # background
            self.canvas.create_rectangle(x - 20 * zm, y - 30 * zm, x + 20 * zm, y + 30 * zm, fill=GRAY, outline=GRAY)
            # head
            self.canvas.create_rectangle(x, y - 4 * zm, x - 20 * zm, y + 4 * zm, **h_args)
            self.canvas.create_rectangle((x - 16 * zm, y - 10 * zm), (x - 26 * zm, y + 10 * zm), **h_args)
            # body
            self.canvas.create_polygon(x - 20 * zm, y - 30 * zm, x, y, x + 20 * zm, y - 30 * zm, **v_args)
            self.canvas.create_polygon(x - 20 * zm, y + 30 * zm, x, y, x + 20 * zm, y + 30 * zm, **v_args)
            if label is not None:
                self.canvas.create_text(x + 35 * zm, y, text=str(label), font=def_font, fill=WHITE)

    def anim(self, name, fdc_open, fdc_close):
        color = color_valve(fdc_open, fdc_close)
        self.canvas.itemconfigure(name, fill=color, outline=color)

    def tag_anim(self, name, tag_fdc_open, tag_fdc_close):
        color = color_tags_valve(tag_fdc_open, tag_fdc_close)
        self.canvas.itemconfigure(name, fill=color, outline=color)

    def motor_anim(self, name, motor_open, motor_close):
        color = color_valve(motor_open, motor_close)
        self.canvas.itemconfigure(str(name) + '_HEAD', fill=color, outline=color)

    def motor_tag_anim(self, name, tag_motor_open, tag_motor_close, tag_default=None):
        color = color_tags_valve(tag_motor_open, tag_motor_close)
        if tag_default:
            color = color if not tag_default.val else VALVE_COLOR[VALVE_DEF]
        self.canvas.itemconfigure(name + '_HEAD', fill=color, outline=color)


class FlowValve(object):
    def __init__(self, canvas):
        """
        FlowValve draw valves (func draw_valve) on canvas.
        Default valve size is 40x30 you can change it with zoom params.

        :param canvas: Tk canvas to draw
        """
        self.canvas = canvas
        self.v_pos = 0.0

    def draw_valve(self, x, y, name, align='h', label=None, zoom=1.0):
        zm = float(zoom)
        def_font = font.Font(size=int(12 * zm))
        head_name = str(name) + '_HEAD'
        v_args = {'fill': VALVE_COLOR[VALVE_ERR], 'outline': VALVE_COLOR[VALVE_ERR], 'tag': name}
        h_args = {'fill': VALVE_COLOR[VALVE_ERR], 'outline': VALVE_COLOR[VALVE_ERR], 'tag': head_name}
        if align in ('H', 'h'):
            # background
            self.canvas.create_rectangle(x - 30 * zm, y - 20 * zm, x + 30 * zm, y + 20 * zm, fill=GRAY, outline=GRAY)
            # head
            self.canvas.create_rectangle(x - 4 * zm, y, x + 4 * zm, y - 20 * zm, **h_args)
            self.canvas.create_oval((x - 10 * zm, y - 16 * zm), (x + 10 * zm, y - 36 * zm), **h_args)
            # body
            self.canvas.create_polygon(x - 30 * zm, y - 20 * zm, x, y, x - 30 * zm, y + 20 * zm, **v_args)
            self.canvas.create_polygon(x + 30 * zm, y - 20 * zm, x, y, x + 30 * zm, y + 20 * zm, **v_args)
            if label is not None:
                self.canvas.create_text(x, y + 35 * zm, text=str(label), font=def_font, fill=WHITE)
        elif align in ('V', 'v'):
            # background
            self.canvas.create_rectangle(x - 20 * zm, y - 30 * zm, x + 20 * zm, y + 30 * zm, fill=GRAY, outline=GRAY)
            # head
            self.canvas.create_rectangle(x, y - 4 * zm, x - 20 * zm, y + 4 * zm, **h_args)
            self.canvas.create_oval((x - 16 * zm, y - 10 * zm), (x - 36 * zm, y + 10 * zm), **h_args)
            # body
            self.canvas.create_polygon(x - 20 * zm, y - 30 * zm, x, y, x + 20 * zm, y - 30 * zm, **v_args)
            self.canvas.create_polygon(x - 20 * zm, y + 30 * zm, x, y, x + 20 * zm, y + 30 * zm, **v_args)
            if label is not None:
                self.canvas.create_text(x + 35 * zm, y, text=str(label), font=def_font, fill=WHITE)

    def anim(self, name, fdc_open, fdc_close):
        self.set_color(name, color_valve(fdc_open, fdc_close))

    def tag_anim(self, name, tag_fdc_open, tag_fdc_close):
        self.set_color(name, color_tags_valve(tag_fdc_open, tag_fdc_close))

    def set_color(self, name, color):
        self.canvas.itemconfigure(name, fill=color, outline=color)

    def motor_anim(self, name, motor_open, motor_close):
        self.motor_set_color(name, color_valve(motor_open, motor_close))

    def motor_tag_anim(self, name, tag_motor_open, tag_motor_close):
        self.motor_set_color(name, color_tags_valve(tag_motor_open, tag_motor_close))

    def motor_set_color(self, name, color):
        self.canvas.itemconfigure(str(name) + '_HEAD', fill=color, outline=color)

    def motor_pos_tag_anim(self, name, tag_v_pos):
        if tag_v_pos.err:
            self.motor_set_color(name, VALVE_COLOR[VALVE_ERR])
        else:
            v_pos = sorted([0.0, float(tag_v_pos.val), 100.0])[1]
            if 0.0 <= v_pos <= 15.0:
                self.motor_anim(name, False, True)
            elif 15.0 < v_pos < 85.0:
                self.motor_anim(name, False, False)
            elif 85.0 <= v_pos <= 100.0:
                self.motor_anim(name, True, False)

    def full_set_color(self, name, color):
        self.set_color(name, color)
        self.motor_set_color(name, color)


class HMICanvas(object):
    def __init__(self, master=None, width=400, height=400, debug=False):
        """
        HMICanvas class: build and update a Tk canvas with all kind of industrial widget
        Set an instance, populate it with add_xxx, build them and refresh with a regular update call

        :param master: Tk parent
        :param width: canvas width (default is 400)
        :param height: canvas height (default is 400)
        :param debug: if set, display all widgets names on canvas
        """
        self.d_widget = {}
        self.can = tk.Canvas(master, width=width, height=height)
        self.can.configure(bg=GRAY)
        self.simple_valve = SimpleValve(self.can)
        self.motor_valve = MotorValve(self.can)
        self.flow_valve = FlowValve(self.can)
        self.debug = bool(debug)

    def add_button(self, name, x_pos, y_pos, **kwargs):
        self.d_widget[name] = {'type': 'button', 'x_pos': x_pos, 'y_pos': y_pos, 'args': kwargs}
        return True

    def add_s_valve(self, name, x_pos, y_pos, label=None, align='h', zoom=1.0):
        self.d_widget[name] = {'type': 's_valve', 'x_pos': x_pos, 'y_pos': y_pos, 'label': label, 'align': align,
                               'zoom': zoom}
        return True

    def add_m_valve(self, name, x_pos, y_pos, label=None, align='h', zoom=1.0):
        self.d_widget[name] = {'type': 'm_valve', 'x_pos': x_pos, 'y_pos': y_pos, 'label': label, 'align': align,
                               'zoom': zoom}
        return True

    def add_f_valve(self, name, x_pos, y_pos, label=None, align='h', zoom=1.0):
        self.d_widget[name] = {'type': 'f_valve', 'x_pos': x_pos, 'y_pos': y_pos, 'label': label, 'align': align,
                               'zoom': zoom}
        return True

    def add_point(self, name, x_pos, y_pos, debug=False):
        self.d_widget[name] = {'type': 'point', 'x_pos': x_pos, 'y_pos': y_pos, 'debug': debug}
        return True

    def add_pipe(self, name, from_name, to_name):
        self.d_widget[name] = {'type': 'pipe', 'from': from_name, 'to': to_name}
        return True

    def add_vbox(self, name, x_pos, y_pos, get_value, size=4, prefix='', suffix='', tk_fmt='{:.2f}', tk_font=None):
        self.d_widget[name] = {'type': 'value', 'x_pos': x_pos, 'y_pos': y_pos, 'get_value': get_value, 'size': size,
                               'prefix': prefix, 'suffix': suffix, 'fmt': tk_fmt, 'font': tk_font}
        return True

    def build(self):
        """
        Build the pyHMI canvas with all industrial widget populate on-it. Call this after all add_xxx functions.

        """
        # draw pipes
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'pipe'}:
            (x_from, y_from) = (
                self.d_widget[self.d_widget[key]['from']]['x_pos'], self.d_widget[self.d_widget[key]['from']]['y_pos'])
            (x_to, y_to) = (
                self.d_widget[self.d_widget[key]['to']]['x_pos'], self.d_widget[self.d_widget[key]['to']]['y_pos'])
            # draw only angle of 90° for multi-line
            if (x_from != x_to) and (y_from != y_to):
                # compute offset to avoid edge effect
                offset = PIPE_WIDTH / 2 if y_from < y_to else -PIPE_WIDTH / 2
                self.can.create_line((x_from, y_from), (x_from, y_to + offset), width=PIPE_WIDTH, fill=BLUE)
                self.can.create_line((x_from, y_to), (x_to, y_to), width=PIPE_WIDTH, fill=BLUE)
            else:
                self.can.create_line((x_from, y_from), (x_to, y_to), width=PIPE_WIDTH, fill=BLUE)
            # pipe debug label
            if self.debug is True:
                avg_x = abs(x_from - x_to) / 2 + min(x_from, x_to)
                avg_y = abs(y_from - y_to) / 2 + min(y_from, y_to)
                self.can.create_text(avg_x, avg_y, text=key, font=font.Font(size=14), fill=WHITE)
        # draw point
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'point'}:
            self.can.create_oval(self.d_widget[key]['x_pos'] - PIPE_WIDTH, self.d_widget[key]['y_pos'] - PIPE_WIDTH,
                                 self.d_widget[key]['x_pos'] + PIPE_WIDTH, self.d_widget[key]['y_pos'] + PIPE_WIDTH,
                                 fill=BLUE, outline=BLUE)
            # point debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw buttons
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'button'}:
            self.d_widget[key]['obj'] = tk.Button(self.can, **self.d_widget[key]['args'])
            self.can.create_window(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'],
                                   window=self.d_widget[key]['obj'])
        # draw simple valves
        for key in {k for k, v in self.d_widget.items() if v['type'] == 's_valve'}:
            self.simple_valve.draw_valve(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], name=key,
                                         label=self.d_widget[key]['label'], align=self.d_widget[key]['align'],
                                         zoom=self.d_widget[key]['zoom'])
            # simple valve debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw motor valves
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'm_valve'}:
            self.motor_valve.draw_valve(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], name=key,
                                        label=self.d_widget[key]['label'], align=self.d_widget[key]['align'],
                                        zoom=self.d_widget[key]['zoom'])
            # simple valve debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw flow valves
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'f_valve'}:
            self.flow_valve.draw_valve(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], name=key,
                                       label=self.d_widget[key]['label'], align=self.d_widget[key]['align'],
                                       zoom=self.d_widget[key]['zoom'])
            # simple valve debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw value box
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'value'}:
            # draw text for compute coords
            self.d_widget[key]['id_txt'] = self.can.create_text(
                (self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos']),
                text=self.d_widget[key]['prefix'] + ' ' + '#' * self.d_widget[key]['size'] + ' ' +
                self.d_widget[key]['suffix'], font=self.d_widget[key]['font'], fill=GREEN)
            (x0, y0, x1, y1) = self.can.bbox(self.d_widget[key]['id_txt'])
            # draw background
            self.can.create_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), fill=GRAY, outline=GRAY)
            # redraw text over background
            self.d_widget[key]['id_txt'] = self.can.create_text(
                (self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos']),
                text=self.d_widget[key]['prefix'] + ' ' + '#' * self.d_widget[key]['size'] + ' ' +
                self.d_widget[key]['suffix'], font=self.d_widget[key]['font'], fill=GREEN)
            # draw red outline
            self.can.create_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), outline=RED, width=2)
            # value box label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        self.can.pack(side=tk.TOP)

    def update_vbox(self):
        for key in {k for k, v in self.d_widget.items() if v['type'] == 'value'}:
            v_key = self.d_widget[key]
            if not v_key['get_value']().err:
                self.can.itemconfig(v_key['id_txt'], text=v_key['prefix'] + ' ' +
                                    v_key['fmt'].format(v_key['get_value']().val) + ' ' +
                                    v_key['suffix'], fill=GREEN)
            else:
                self.can.itemconfig(v_key['id_txt'], text=v_key['prefix'] + ' ' +
                                    v_key['fmt'].format(v_key['get_value']().val) + ' ' +
                                    v_key['suffix'], fill=PINK)
