import tkinter as tk
from tkinter.font import Font
from typing import Optional

from .Colors import SynColors
from .Tag import Tag


class SynWidget:
    def __init__(self, synoptic: 'Synoptic', name: str):
        # public
        self.synoptic = synoptic
        self.name = name
        # add a Tk canvas shortcut
        self.tk_canvas = self.synoptic.tk_canvas
        # add this widget to Synoptic
        self.synoptic.record_widget(self)

    def build(self):
        pass

    def update(self):
        pass


class SynButton(SynWidget):
    def __init__(self, synoptic: 'Synoptic', name: str, x: int, y: int) -> None:
        # init mother class
        SynWidget.__init__(self, synoptic, name)
        # process args as public properties
        self.x = x
        self.y = y
        # public vars
        self.tk_button = tk.Button(self.tk_canvas)

    def build(self):
        self.tk_canvas.create_window((self.x, self.y), window=self.tk_button)


class SynValve(SynWidget):
    def __init__(self, synoptic: 'Synoptic', name: str, x: int, y: int, label: Optional[str] = None,
                 align: str = 'h', zoom: float = 1.0, motor: bool = False,
                 tag_open: Optional[Tag] = None, tag_close: Optional[Tag] = None,
                 tag_motor_open: Optional[Tag] = None, tag_motor_close: Optional[Tag] = None,
                 tag_default: Optional[Tag] = None):
        """
        SimpleValve draw valves (func draw_valve) on canvas.
        Default valve size is 40x30 you can change it with zoom params.
        """
        # init mother class
        SynWidget.__init__(self, synoptic, name)
        # process args as public properties
        self.x = x
        self.y = y
        self.label = label
        self.align = align
        self.zoom = zoom
        self.motor = motor
        self.tag_open = tag_open
        self.tag_close = tag_close
        self.tag_motor_open = tag_motor_open
        self.tag_motor_close = tag_motor_close
        self.tag_default = tag_default
        # public vars
        self.tk_font = Font(size=round(12 * self.zoom))

    def build(self):
        # build horizontal or vertical valve
        if self.align == 'h':
            # background
            self.tk_canvas.create_rectangle(self.x - 30 * self.zoom, self.y - 20 * self.zoom,
                                            self.x + 30 * self.zoom, self.y + 20 * self.zoom,
                                            fill=self.synoptic.colors.bg, outline=self.synoptic.colors.bg)
            # head (motor)
            if self.motor:
                self.tk_canvas.create_rectangle(self.x - 4 * self.zoom, self.y, self.x +
                                                4 * self.zoom, self.y - 20 * self.zoom,
                                                fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                                tags=self.name + '_HEAD')
                self.tk_canvas.create_rectangle(self.x - 10 * self.zoom, self.y - 16 * self.zoom,
                                                self.x + 10 * self.zoom, self.y - 26 * self.zoom,
                                                fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                                tags=self.name + '_HEAD')
            # body
            self.tk_canvas.create_polygon(self.x - 30 * self.zoom, self.y - 20 * self.zoom,
                                          self.x, self.y, self.x - 30 * self.zoom, self.y + 20 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            self.tk_canvas.create_polygon(self.x + 30 * self.zoom, self.y - 20 * self.zoom,
                                          self.x, self.y, self.x + 30 * self.zoom, self.y + 20 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            if self.label:
                self.tk_canvas.create_text(self.x, self.y + 35 * self.zoom,
                                           text=self.label, font=self.tk_font, fill=self.synoptic.colors.valve_label)
        elif self.align == 'v':
            # background
            self.tk_canvas.create_rectangle(self.x - 20 * self.zoom, self.y - 30 * self.zoom,
                                            self.x + 20 * self.zoom, self.y + 30 * self.zoom,
                                            fill=self.synoptic.colors.bg, outline=self.synoptic.colors.bg)
            # head (motor)
            if self.motor:
                self.tk_canvas.create_rectangle(self.x, self.y - 4 * self.zoom,
                                                self.x - 20 * self.zoom, self.y + 4 * self.zoom,
                                                fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                                tags=self.name + '_HEAD')
                self.tk_canvas.create_rectangle(self.x - 16 * self.zoom, self.y - 10 * self.zoom,
                                                self.x - 26 * self.zoom, self.y + 10 * self.zoom,
                                                fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                                tags=self.name + '_HEAD')
            # body
            self.tk_canvas.create_polygon(self.x - 20 * self.zoom, self.y - 30 * self.zoom,
                                          self.x, self.y, self.x + 20 * self.zoom, self.y - 30 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            self.tk_canvas.create_polygon(self.x - 20 * self.zoom, self.y + 30 * self.zoom,
                                          self.x, self.y, self.x + 20 * self.zoom, self.y + 30 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            if self.label:
                self.tk_canvas.create_text(self.x + 35 * self.zoom, self.y,
                                           text=self.label, font=self.tk_font, fill=self.synoptic.colors.valve_label)
        else:
            raise ValueError('bad value for align argument')

    def update(self):
        self.tag_anim(self.tag_open, self.tag_close, self.tag_motor_open, self.tag_motor_close, self.tag_default)

    def set_valve_color(self, color: str):
        self.tk_canvas.itemconfigure(self.name, fill=color, outline=color)

    def set_motor_color(self, color: str):
        self.tk_canvas.itemconfigure(self.name + '_HEAD', fill=color, outline=color)

    def anim(self, open: Optional[bool] = None, close: Optional[bool] = None,
             motor_open: Optional[bool] = None, motor_close: Optional[bool] = None,
             default: Optional[bool] = None):
        # update the valve body if at least one the open or close args is set
        if open is not None or close is not None:
            self.set_valve_color(self.synoptic.colors.valve(open, close))
        # update the valve motor if at least one of the motor_open, motor_close or default args is set
        if motor_open is not None or motor_close is not None or default is not None:
            self.set_motor_color(self.synoptic.colors.valve(motor_open, motor_close, default))

    def tag_anim(self, tag_open: Optional[Tag] = None, tag_close: Optional[Tag] = None,
                 tag_motor_open: Optional[Tag] = None, tag_motor_close: Optional[Tag] = None,
                 tag_default: Optional[Tag] = None):
        # update the valve body if at least one the open or close args is set
        if tag_open or tag_close:
            self.set_valve_color(self.synoptic.colors.tags_valve(tag_open, tag_close))
        # update the valve motor if at least one of the motor_open, motor_close or default args is set
        if tag_motor_open or tag_motor_close or tag_default:
            self.set_motor_color(self.synoptic.colors.tags_valve(tag_motor_open, tag_motor_close, tag_default))


class SynFlowValve(SynWidget):
    def __init__(self, synoptic: 'Synoptic', name: str, x: int, y: int, label: Optional[str] = None,
                 align: str = 'h', zoom: float = 1.0,
                 tag_open: Optional[Tag] = None, tag_close: Optional[Tag] = None,
                 tag_motor_open: Optional[Tag] = None, tag_motor_close: Optional[Tag] = None,
                 tag_default: Optional[Tag] = None):
        """
        SynFlowValve draw valves (func draw_valve) on canvas.
        Default valve size is 40x30 you can change it with zoom params.
        """
        # init mother class
        SynWidget.__init__(self, synoptic, name)
        # process args as public properties
        self.x = x
        self.y = y
        self.label = label
        self.align = align
        self.zoom = zoom
        self.tag_open = tag_open
        self.tag_close = tag_close
        self.tag_motor_open = tag_motor_open
        self.tag_motor_close = tag_motor_close
        self.tag_default = tag_default
        # public vars
        self.tk_font = Font(size=round(12 * self.zoom))

    def build(self):
        h_args = {'fill': self.synoptic.colors.error, 'outline': self.synoptic.colors.error, 'tag': self.name + '_HEAD'}
        # build horizontal or vertical valve
        if self.align == 'h':
            # background
            self.tk_canvas.create_rectangle(self.x - 30 * self.zoom, self.y - 20 * self.zoom,
                                            self.x + 30 * self.zoom, self.y + 20 * self.zoom,
                                            fill=self.synoptic.colors.bg, outline=self.synoptic.colors.bg)
            # head
            self.tk_canvas.create_rectangle(self.x - 4 * self.zoom, self.y, self.x +
                                            4 * self.zoom, self.y - 20 * self.zoom,
                                            fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                            tags=self.name+'_HEAD')
            self.tk_canvas.create_oval(self.x - 10 * self.zoom, self.y - 16 * self.zoom,
                                       self.x + 10 * self.zoom, self.y - 36 * self.zoom,
                                       fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                       tags=self.name+'_HEAD')
            # body
            self.tk_canvas.create_polygon(self.x - 30 * self.zoom, self.y - 20 * self.zoom,
                                          self.x, self.y, self.x - 30 * self.zoom, self.y + 20 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            self.tk_canvas.create_polygon(self.x + 30 * self.zoom, self.y - 20 * self.zoom,
                                          self.x, self.y, self.x + 30 * self.zoom, self.y + 20 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            # add a label
            if self.label:
                self.tk_canvas.create_text(self.x, self.y + 35 * self.zoom,
                                           text=self.label, font=self.tk_font,
                                           fill=self.synoptic.colors.valve_label)
        elif self.align == 'v':
            # background
            self.tk_canvas.create_rectangle(self.x - 20 * self.zoom, self.y - 30 * self.zoom,
                                            self.x + 20 * self.zoom, self.y + 30 * self.zoom,
                                            fill=self.synoptic.colors.bg, outline=self.synoptic.colors.bg)
            # head
            self.tk_canvas.create_rectangle(self.x, self.y - 4 * self.zoom, self.x -
                                            20 * self.zoom, self.y + 4 * self.zoom,
                                            fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                            tags=self.name+'_HEAD')
            self.tk_canvas.create_oval(self.x - 16 * self.zoom, self.y - 10 * self.zoom,
                                       self.x - 36 * self.zoom, self.y + 10 * self.zoom,
                                       fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                       tags=self.name+'_HEAD')
            # body
            self.tk_canvas.create_polygon(self.x - 20 * self.zoom, self.y - 30 * self.zoom,
                                          self.x, self.y, self.x + 20 * self.zoom, self.y - 30 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            self.tk_canvas.create_polygon(self.x - 20 * self.zoom, self.y + 30 * self.zoom,
                                          self.x, self.y, self.x + 20 * self.zoom, self.y + 30 * self.zoom,
                                          fill=self.synoptic.colors.error, outline=self.synoptic.colors.error,
                                          tags=self.name)
            # add a label
            if self.label:
                self.tk_canvas.create_text(self.x + 35 * self.zoom, self.y,
                                           text=self.label, font=self.tk_font,
                                           fill=self.synoptic.colors.valve_label)
        else:
            raise ValueError('bad value for align argument')

    def update(self):
        self.tag_anim(self.tag_open, self.tag_close, self.tag_motor_open, self.tag_motor_close, self.tag_default)

    def set_valve_color(self, color: str):
        self.tk_canvas.itemconfigure(self.name, fill=color, outline=color)

    def set_motor_color(self, color: str):
        self.tk_canvas.itemconfigure(self.name + '_HEAD', fill=color, outline=color)

    def anim(self, open: Optional[bool] = None, close: Optional[bool] = None,
             motor_open: Optional[bool] = None, motor_close: Optional[bool] = None,
             default: Optional[bool] = None):
        # update the valve body if at least one the open or close args is set
        if open is not None or close is not None:
            self.set_valve_color(self.synoptic.colors.valve(open, close))
        # update the valve motor if at least one of the motor_open, motor_close or default args is set
        if motor_open is not None or motor_close is not None or default is not None:
            self.set_motor_color(self.synoptic.colors.valve(motor_open, motor_close, default))

    def tag_anim(self, tag_open: Optional[Tag] = None, tag_close: Optional[Tag] = None,
                 tag_motor_open: Optional[Tag] = None, tag_motor_close: Optional[Tag] = None,
                 tag_default: Optional[Tag] = None):
        # update the valve body if at least one the open or close args is set
        if tag_open or tag_close:
            self.set_valve_color(self.synoptic.colors.tags_valve(tag_open, tag_close))
        # update the valve motor if at least one of the motor_open, motor_close or default args is set
        if tag_motor_open or tag_motor_close or tag_default:
            self.set_motor_color(self.synoptic.colors.tags_valve(tag_motor_open, tag_motor_close, tag_default))


class SynPoint(SynWidget):
    def __init__(self, synoptic: 'Synoptic', name: str, x: int, y: int) -> None:
        # init mother class
        SynWidget.__init__(self, synoptic, name)
        # process args as public properties
        self.x = x
        self.y = y

    def build(self):
        self.tk_canvas.create_oval(self.x - self.synoptic.geo.pipe_width, self.y - self.synoptic.geo.pipe_width,
                                   self.x + self.synoptic.geo.pipe_width, self.y + self.synoptic.geo.pipe_width,
                                   fill=self.synoptic.colors.pipe, outline=self.synoptic.colors.pipe)
        if self.synoptic.debug:
            self.tk_canvas.create_text(self.x, self.y, text=self.name, font=Font(size=14),
                                       fill=self.synoptic.colors.debug)


class SynPipe(SynWidget):
    def __init__(self, synoptic: 'Synoptic', name: str, from_name: str, to_name: str) -> None:
        # init mother class
        SynWidget.__init__(self, synoptic, name)
        # process args as public properties
        self.from_name = from_name
        self.to_name = to_name

    def build(self):
        x_from = self.synoptic.widgets[self.from_name].x
        y_from = self.synoptic.widgets[self.from_name].y
        x_to = self.synoptic.widgets[self.to_name].x
        y_to = self.synoptic.widgets[self.to_name].y
        # draw only angle of 90° for multi-line
        if (x_from != x_to) and (y_from != y_to):
            # compute offset to avoid edge effect
            offset = self.synoptic.geo.pipe_width / 2 if y_from < y_to else -self.synoptic.geo.pipe_width / 2
            self.tk_canvas.create_line((x_from, y_from), (x_from, y_to + offset),
                                       width=self.synoptic.geo.pipe_width, fill=self.synoptic.colors.pipe)
            self.tk_canvas.create_line((x_from, y_to), (x_to, y_to), width=self.synoptic.geo.pipe_width,
                                       fill=self.synoptic.colors.pipe)
        else:
            self.tk_canvas.create_line((x_from, y_from), (x_to, y_to), width=self.synoptic.geo.pipe_width,
                                       fill=self.synoptic.colors.pipe)
        # pipe debug label
        if self.synoptic.debug:
            avg_x = abs(x_from - x_to) / 2 + min(x_from, x_to)
            avg_y = abs(y_from - y_to) / 2 + min(y_from, y_to)
            self.tk_canvas.create_text(avg_x, avg_y, text=self.name, font=Font(size=14),
                                       fill=self.synoptic.colors.debug)


class SynValue(SynWidget):
    def __init__(self, synoptic: 'Synoptic', name: str, x: int, y: int, tag: Tag, size: int = 4, prefix: str = '',
                 suffix: str = '', fmt: str = '.2f', box: bool = True, tk_font: Optional[Font] = None) -> None:
        # init mother class
        SynWidget.__init__(self, synoptic, name)
        # process args as public properties
        self.x = x
        self.y = y
        self.tag = tag
        self.size = size
        self.prefix = prefix
        self.suffix = suffix
        self.fmt = fmt
        self.box = box
        if tk_font:
            self.tk_font = tk_font
        else:
            self.tk_font = Font(size=10)
        # public vars
        self.id_txt = None

    def build(self):
        blank_value = '#' * self.size
        blank_txt = f'{self.prefix} {blank_value} {self.suffix}'
        # draw text for compute text box coordinates
        tmp_id_txt = self.tk_canvas.create_text((self.x, self.y), text=blank_txt, font=self.tk_font)
        x0, y0, x1, y1 = self.tk_canvas.bbox(tmp_id_txt)
        # draw background
        self.tk_canvas.create_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5),
                                        fill=self.synoptic.colors.bg, outline=self.synoptic.colors.bg)
        # redraw text over background
        self.id_txt = self.tk_canvas.create_text((self.x, self.y), text=blank_txt, font=self.tk_font,
                                                 fill=self.synoptic.colors.value_label)
        # draw red outline
        if self.box:
            self.tk_canvas.create_rectangle((x0 - 5, y0 - 5, x1 + 5, y1 + 5), width=2,
                                            outline=self.synoptic.colors.value_outline)
        # value box label
        if self.synoptic.debug:
            self.tk_canvas.create_text((self.x, self.y), text=self.name, font=Font(size=14),
                                       fill=self.synoptic.colors.debug)

    def update(self):
        if self.id_txt:
            # format tag value
            try:
                value = f'{self.tag.value:{self.fmt}}'
                # replace default thousands separator ("2_000" -> "2 000")
                if isinstance(self.tag.value, (int, float)):
                    value = value.replace('_', ' ')
            except ValueError:
                value = 'fmt error'
            # apply to tk canvas
            color = self.synoptic.colors.error if self.tag.error else self.synoptic.colors.value_label
            self.tk_canvas.itemconfig(self.id_txt, text=f'{self.prefix} {value} {self.suffix}', fill=color)


class SynGeo:
    """Default geometric values."""
    # SynPipe and SynPoint
    pipe_width = 6


class Synoptic:
    def __init__(self, master=None, width: int = 400, height: int = 400, update_ms: int = 500, debug: bool = False):
        """
        Synoptic class: build and update a Tk canvas with all kind of industrial widget.

        :param master: Tk parent
        :param width: canvas width in pixels (default is 400)
        :param height: canvas height in pixels (default is 400)
        :param update_ms: refresh rate in ms (default is 500)
        :param debug: debug mode display all widgets names on canvas (default is False)
        """
        # args
        self.master = master
        self.width = width
        self.height = height
        self.update_ms = update_ms
        self.debug = debug
        # default colors palette
        self.colors = SynColors()
        # default geometry
        self.geo = SynGeo()
        # init Tk canvas
        self.tk_canvas = tk.Canvas(self.master, width=width, height=height)
        # dict of widgets mapped on this synoptic
        self.widgets = {}
        # setup auto-refresh of update method (on-visibility and every update_ms)
        self.tk_canvas.bind('<Visibility>', lambda evt: self.update())
        if self.update_ms:
            self._auto_update()

    def _auto_update(self):
        if self.tk_canvas.winfo_ismapped():
            self.update()
        self.tk_canvas.after(ms=self.update_ms, func=self._auto_update)

    def record_widget(self, widget: SynWidget):
        # check widget name duplicate
        if widget.name in self.widgets:
            raise ValueError(f'Widget "{widget.name}" already exist.')
        # record current widget in synoptic
        self.widgets[widget.name] = widget

    def build(self, pack_args: Optional[dict] = None, grid_args: Optional[dict] = None,
              place_args: Optional[dict] = None):
        # mutable args
        if pack_args is None:
            pack_args = {}
        if grid_args is None:
            grid_args = {}
        if place_args is None:
            place_args = {}
        # first draw all pipes
        for widget in self.widgets.values():
            if isinstance(widget, SynPipe):
                widget.build()
        # draw other objects over pipes
        for widget in self.widgets.values():
            if isinstance(widget, (SynButton, SynValve, SynFlowValve, SynPoint, SynValue)):
                widget.build()
        # apply background color
        self.tk_canvas.configure(background=self.colors.bg)
        # pack canvas
        if place_args:
            self.tk_canvas.place(**place_args)
        elif grid_args:
            self.tk_canvas.grid(**grid_args)
        else:
            self.tk_canvas.pack(**pack_args)

    def update(self):
        for widget in self.widgets.values():
            widget.update()
