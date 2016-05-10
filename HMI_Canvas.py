from tkinter import *
from tkinter import font

# some const
# Canvas Pipe width
PIPE_WIDTH = 6
# COLOR
RED = '#bc3f3c'
GREEN = '#51c178'
GRAY = '#2d2d2d'
BLUE = '#589df6'
WHITE = '#ffffff'
ORANGE = '#be9117'
PINK = 'hot pink'
BLACK = 'black'


def state_color(tag):
    return (PINK, WHITE, GREEN)[not tag.err and tag.val + 1]


def alarm_color(tag):
    return (PINK, WHITE, RED)[not tag.err and tag.val + 1]


def valve_color(tag_fdc_o, tag_fdc_c):
    return (PINK, WHITE, GREEN, RED, ORANGE)[
        not (tag_fdc_o.err or tag_fdc_c.err) and (tag_fdc_o.val + tag_fdc_c.val * 2 + 1)]


class SimpleValve(object):
    def __init__(self, canvas):
        """
        SimpleValve draw valves (func draw_valve) on canvas. You name it an animate it with open/close/move/error.
        Default valve size is 40x30 you can change it with zoom params.

        :param canvas: Tk canvas to draw
        """
        self.canvas = canvas

    def draw_valve(self, x, y, name, label=None, align='h', zoom=1.0):
        z = float(zoom)
        def_font = font.Font(size=int(12 * z))
        args = {'fill': ORANGE, 'outline': ORANGE, 'tag': name}
        if align in ('H', 'h'):
            self.canvas.create_rectangle(x - 30 * z, y - 20 * z, x + 30 * z, y + 20 * z, fill=GRAY, outline=GRAY)
            self.canvas.create_polygon(x - 30 * z, y - 20 * z, x, y, x - 30 * z, y + 20 * z, **args)
            self.canvas.create_polygon(x + 30 * z, y - 20 * z, x, y, x + 30 * z, y + 20 * z, **args)
            if label is not None:
                self.canvas.create_text(x, y + 35 * z, text=str(label), font=def_font, fill=WHITE)
        elif align in ('V', 'v'):
            self.canvas.create_rectangle(x - 20 * z, y - 30 * z, x + 20 * z, y + 30 * z, fill=GRAY, outline=GRAY)
            self.canvas.create_polygon(x - 20 * z, y - 30 * z, x, y, x + 20 * z, y - 30 * z, **args)
            self.canvas.create_polygon(x - 20 * z, y + 30 * z, x, y, x + 20 * z, y + 30 * z, **args)
            if label is not None:
                self.canvas.create_text(x + 35 * z, y, text=str(label), font=def_font, fill=WHITE)

    def open(self, name):
        self.canvas.itemconfigure(name, fill=GREEN, outline=GREEN)

    def close(self, name):
        self.canvas.itemconfigure(name, fill=RED, outline=RED)

    def move(self, name):
        self.canvas.itemconfigure(name, fill=WHITE, outline=WHITE)

    def error(self, name):
        self.canvas.itemconfigure(name, fill=ORANGE, outline=ORANGE)

    def animate(self, name, fdc_open, fdc_close):
        if fdc_open.err or fdc_close.err:
            c_color = PINK
        else:
            c_color = (WHITE, GREEN, RED, ORANGE)[fdc_open.val + fdc_close.val * 2]
        self.canvas.itemconfigure(name, fill=c_color, outline=c_color)


class FlowValve(object):
    def __init__(self, canvas):
        """
        FlowValve draw valves (func draw_valve) on canvas. You name it an animate it with open/close/move/error.
        Default valve size is 40x30 you can change it with zoom params.

        :param canvas: Tk canvas to draw
        """
        self.canvas = canvas
        self.v_pos = 0.0

    def draw_valve(self, x, y, name, align='h', label=None, zoom=1.0):
        z = float(zoom)
        def_font = font.Font(size=int(12 * z))
        head_name = str(name) + '__HEAD'
        v_args = {'fill': ORANGE, 'outline': ORANGE, 'tag': name}
        c_args = {'fill': RED, 'outline': RED, 'tag': head_name}
        if align in ('H', 'h'):
            # background
            self.canvas.create_rectangle(x - 30 * z, y - 20 * z, x + 30 * z, y + 20 * z, fill=GRAY, outline=GRAY)
            # head
            self.canvas.create_rectangle(x - 4 * z, y, x + 4 * z, y - 20 * z, **c_args)
            self.canvas.create_oval((x - 10 * z, y - 16 * z), (x + 10 * z, y - 36 * z), **c_args)
            # body
            self.canvas.create_polygon(x - 30 * z, y - 20 * z, x, y, x - 30 * z, y + 20 * z, **v_args)
            self.canvas.create_polygon(x + 30 * z, y - 20 * z, x, y, x + 30 * z, y + 20 * z, **v_args)
            if label is not None:
                self.canvas.create_text(x, y + 35 * z, text=str(label), font=def_font, fill=WHITE)
        elif align in ('V', 'v'):
            # background
            self.canvas.create_rectangle(x - 20 * z, y - 30 * z, x + 20 * z, y + 30 * z, fill=GRAY, outline=GRAY)
            # head
            # self.canvas.create_rectangle(x - 4 * z, y, x + 4 * z, y - 20 * z, **c_args)
            # self.canvas.create_oval((x - 10 * z, y - 16 * z), (x + 10 * z, y - 36 * z), **c_args)
            # body
            self.canvas.create_polygon(x - 20 * z, y - 30 * z, x, y, x + 20 * z, y - 30 * z, **v_args)
            self.canvas.create_polygon(x - 20 * z, y + 30 * z, x, y, x + 20 * z, y + 30 * z, **v_args)
            if label is not None:
                self.canvas.create_text(x + 35 * z, y, text=str(label), font=def_font, fill=WHITE)

    def open(self, name):
        self.canvas.itemconfigure(name, fill=GREEN, outline=GREEN)

    def close(self, name):
        self.canvas.itemconfigure(name, fill=RED, outline=RED)

    def move(self, name):
        self.canvas.itemconfigure(name, fill=WHITE, outline=WHITE)

    def error(self, name):
        self.canvas.itemconfigure(name, fill=ORANGE, outline=ORANGE)

    def set_pos(self, name, v_pos):
        head_name = str(name) + '__HEAD'
        self.v_pos = sorted([0.0, float(v_pos), 100.0])[1]
        if 0.0 <= self.v_pos <= 15.0:
            self.canvas.itemconfigure(head_name, fill=RED, outline=RED)
        elif 15.0 < self.v_pos < 85.0:
            self.canvas.itemconfigure(head_name, fill=WHITE, outline=WHITE)
        elif 85.0 <= self.v_pos <= 100.0:
            self.canvas.itemconfigure(head_name, fill=GREEN, outline=GREEN)


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
        self.can = Canvas(master, width=width, height=height)
        self.can.configure(bg=GRAY)
        self.simple_valve = SimpleValve(self.can)
        self.flow_valve = FlowValve(self.can)
        self.debug = bool(debug)

    def add_button(self, name, x_pos, y_pos, **kwargs):
        self.d_widget[name] = {'type': 'button', 'x_pos': x_pos, 'y_pos': y_pos, 'args': kwargs}
        return True

    def add_s_valve(self, name, x_pos, y_pos, label=None, align='h', zoom=1.0):
        self.d_widget[name] = {'type': 's_valve', 'x_pos': x_pos, 'y_pos': y_pos, 'label': label, 'align': align,
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
        Build the HMI canvas with all industrial widget populate on-it. Call this after all add_xxx functions.

        """
        # draw pipes
        for key in {k for k, v in self.d_widget.items() if v['type'] is 'pipe'}:
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
        for key in {k for k, v in self.d_widget.items() if v['type'] is 'point'}:
            self.can.create_oval(self.d_widget[key]['x_pos'] - PIPE_WIDTH, self.d_widget[key]['y_pos'] - PIPE_WIDTH,
                                 self.d_widget[key]['x_pos'] + PIPE_WIDTH, self.d_widget[key]['y_pos'] + PIPE_WIDTH,
                                 fill=BLUE, outline=BLUE)
            # point debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw buttons
        for key in {k for k, v in self.d_widget.items() if v['type'] is 'button'}:
            self.d_widget[key]['obj'] = Button(self.can, **self.d_widget[key]['args'])
            self.can.create_window(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'],
                                   window=self.d_widget[key]['obj'])
        # draw simple valves
        for key in {k for k, v in self.d_widget.items() if v['type'] is 's_valve'}:
            self.simple_valve.draw_valve(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], name=key,
                                         label=self.d_widget[key]['label'], align=self.d_widget[key]['align'],
                                         zoom=self.d_widget[key]['zoom'])
            # simple valve debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw flow valves
        for key in {k for k, v in self.d_widget.items() if v['type'] is 'f_valve'}:
            self.flow_valve.draw_valve(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], name=key,
                                       label=self.d_widget[key]['label'], align=self.d_widget[key]['align'],
                                       zoom=self.d_widget[key]['zoom'])
            # simple valve debug label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        # draw value box
        for key in {k for k, v in self.d_widget.items() if v['type'] is 'value'}:
            # draw text for compute coords
            self.d_widget[key]['id_txt'] = self.can.create_text(
                (self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos']),
                text=self.d_widget[key]['prefix'] + ' ' + '#' * self.d_widget[key][
                    'size'] + ' ' +
                     self.d_widget[key]['suffix'], font=self.d_widget[key]['font'],
                fill=GREEN)
            (x0, y0, x1, y1) = self.can.bbox(self.d_widget[key]['id_txt'])
            # draw background
            self.can.create_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), fill=GRAY, outline=GRAY)
            # redraw text over background
            self.d_widget[key]['id_txt'] = self.can.create_text(
                (self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos']),
                text=self.d_widget[key]['prefix'] + ' ' + '#' * self.d_widget[key][
                    'size'] + ' ' +
                     self.d_widget[key]['suffix'], font=self.d_widget[key]['font'],
                fill=GREEN)
            # draw red outline
            self.can.create_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), outline=RED, width=2)
            # value box label
            if self.debug is True:
                self.can.create_text(self.d_widget[key]['x_pos'], self.d_widget[key]['y_pos'], text=key,
                                     font=font.Font(size=14), fill=WHITE)
        self.can.pack(side=TOP)

    def update_vbox(self):
        for key in {k for k, v in self.d_widget.items() if v['type'] is 'value'}:
            v_key = self.d_widget[key]
            if not v_key['get_value']().err:
                self.can.itemconfig(v_key['id_txt'], text=v_key['prefix'] + ' ' +
                                                          v_key['fmt'].format(v_key['get_value']().val) + ' ' +
                                                          v_key['suffix'], fill=GREEN)
            else:
                self.can.itemconfig(v_key['id_txt'], text=v_key['prefix'] + ' ' +
                                                          v_key['fmt'].format(v_key['get_value']().val) + ' ' +
                                                          v_key['suffix'], fill=PINK)
