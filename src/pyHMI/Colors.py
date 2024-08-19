from typing import Optional
import tkinter as tk
from .Tag import Tag


# some const
# Canvas Pipe width
PIPE_WIDTH = 6
# Colors
BLACK = 'black'
BLUE = '#589df6'
GRAY = '#2d2d2d'
GREEN = '#51c178'
ORANGE = '#be9117'
PINK = 'hot pink'
RED = '#bc3f3c'
VIOLET = 'dark violet'
WHITE = '#ffffff'
YELLOW = 'yellow2'
# Default colors
STATE_COLOR = (PINK, WHITE, GREEN)
ALARM_COLOR = (PINK, WHITE, RED)
VALVE_COLOR = (PINK, WHITE, GREEN, RED, ORANGE, VIOLET)
VALVE_ERR = 0
VALVE_MOVE = 1
VALVE_OPEN = 2
VALVE_CLOSE = 3
VALVE_INC = 4
VALVE_DEF = 5


# some class
class UIColors:
    """Default User Interface colors palette."""
    # COM status
    btn_com_valid = GREEN
    btn_com_error = PINK
    txt_com_valid = BLACK
    txt_com_error = PINK
    # UIBoolItem, UIAnalogItem
    bg_item_blank = WHITE
    bg_item_state = GREEN
    bg_item_alarm = RED
    # Dialog box
    dial_bg_warn = RED


class SynColors:
    """Default Synoptic colors palette."""
    # global
    bg = GRAY
    debug = WHITE
    error = PINK
    # SynValve and SynFlowValve
    valve_label = WHITE
    valve_blank = WHITE
    valve_open = GREEN
    valve_close = RED
    valve_mismatch = ORANGE
    valve_default = VIOLET
    # SynPipe and SynPoint
    pipe = BLUE
    # SynValue
    value_outline = RED
    value_label = GREEN

    def valve(self, open: Optional[bool] = None, close: Optional[bool] = None, default:  Optional[bool] = None):
        # unset bool args default value is False
        if default:
            return self.valve_default
        if open and close:
            return self.valve_mismatch
        elif not open and close:
            return self.valve_close
        elif open and not close:
            return self.valve_open
        else:
            return self.valve_blank

    def tags_valve(self, tag_open: Optional[Tag] = None, tag_close: Optional[Tag] = None,
                   tag_default: Optional[Tag] = None):
        # unset tag have False default value
        tag_open = tag_open if tag_open else Tag(False)
        tag_close = tag_close if tag_close else Tag(False)
        tag_default = tag_default if tag_default else Tag(False)
        # return error color if any tag have error flag set
        if tag_open.error or tag_close.error or tag_default.error:
            return self.error
        else:
            return self.valve(tag_open.value, tag_close.value, tag_default.value)


# older stuff, keep here for compatibility issues
def color_tag_state(tag: Tag):
    return STATE_COLOR[not tag.error and tag.value + 1]


def color_tag_alarm(tag: Tag):
    return ALARM_COLOR[not tag.error and tag.value + 1]


def color_tags_valve(tag_open: Optional[Tag] = None, tag_close: Optional[Tag] = None):
    # unset tag default value is False
    tag_open = tag_open if tag_open else Tag(False)
    tag_close = tag_close if tag_close else Tag(False)
    return VALVE_COLOR[not (tag_open.error or tag_close.error) and (tag_open.value + tag_close.value * 2 + 1)]


def color_valve(open: Optional[bool] = None, close: Optional[bool] = None):
    # unset bool args default value is False
    return VALVE_COLOR[bool(open) + bool(close) * 2 + 1]


def color_label(tk_label: tk.Label, tag: Tag, fmt: str = '%s'):
    tk_label.configure(text=fmt % tag.value, background=PINK if tag.error else WHITE)


class HMIBoolList(object):
    def __init__(self, tk_parent, head_str='', lbl_args=None, grid_args=None):
        self.tk_parent = tk_parent
        self.frame = tk.Frame(tk_parent)
        self.frame.pack(anchor=tk.CENTER)
        self.items_list = []
        self.head_str = head_str
        self._ref_tk_lbl = []
        self._lbl_args = {} if lbl_args is None else lbl_args
        self._grid_args = {} if grid_args is None else grid_args

    def add(self, label_0, tag, label_1=None, state=True, alarm=False, lbl_args=None, grid_args=None):
        if label_1 is None:
            label_1 = label_0
        if lbl_args is None:
            lbl_args = {}
        if grid_args is None:
            grid_args = {}
        self.items_list.append(
            {'label_0': label_0, 'tag': tag, 'label_1': label_1, 'state': state, 'alarm': alarm, 'lbl_args': lbl_args,
             'grid_args': grid_args})

    def build(self):
        # head
        i_row = 0
        if self.head_str:
            tk.Label(self.frame, self._lbl_args, text=self.head_str).grid(self._grid_args, row=i_row)
            i_row += 1
        # body
        for d_item in self.items_list:
            d_item['lbl_args'].update(self._lbl_args)
            d_item['grid_args'].update(self._grid_args)
            l = tk.Label(self.frame, d_item['lbl_args'], text=d_item['label_1'], background=WHITE)
            l.grid(d_item['grid_args'], row=i_row, column=0)
            i_row += 1
            self._ref_tk_lbl.append({'tk_label': l, 'tag': d_item['tag'], 'label_0': d_item['label_0'],
                                     'label_1': d_item['label_1'], 'state': d_item['state'], 'alarm': d_item['alarm']})

    def update(self):
        for d in self._ref_tk_lbl:
            # set color
            if d['alarm']:
                d['tk_label'].configure(background=color_tag_alarm(d['tag']))
            elif d['state']:
                d['tk_label'].configure(background=color_tag_state(d['tag']))
            # set text
            if d['tag'].val:
                d['tk_label'].configure(text=d['label_1'])
            else:
                d['tk_label'].configure(text=d['label_0'])


class HMIAnalogList(object):
    def __init__(self, tk_parent, lbl_args=None, grid_args=None):
        self.tk_parent = tk_parent
        self.frame = tk.Frame(tk_parent)
        self.frame.pack(anchor=tk.CENTER)
        self.items_list = []
        self._ref_tk_lbl = []
        self._lbl_args = {} if lbl_args is None else lbl_args
        self._grid_args = {} if grid_args is None else grid_args

    def add(self, name, tag, unit='', fmt='%s', lbl_args=None, grid_args=None):
        if lbl_args is None:
            lbl_args = {}
        if grid_args is None:
            grid_args = {}
        self.items_list.append(
            {'name': name, 'tag': tag, 'unit': unit, 'fmt': fmt, 'lbl_args': lbl_args, 'grid_args': grid_args})

    def build(self):
        for i, d_item in enumerate(self.items_list):
            d_item['lbl_args'].update(self._lbl_args)
            d_item['grid_args'].update(self._grid_args)
            tk.Label(self.frame, text=d_item['name']).grid(d_item['grid_args'], padx=10, pady=2, row=i, column=0)
            l = tk.Label(self.frame, d_item['lbl_args'])
            l.grid(d_item['grid_args'], padx=10, row=i, column=1)
            tk.Label(self.frame, text=d_item['unit']).grid(d_item['grid_args'], padx=5, sticky=tk.W, row=i, column=2)
            self._ref_tk_lbl.append({'label': l, 'tag': d_item['tag'], 'fmt': d_item['fmt']})

    def update(self):
        for d in self._ref_tk_lbl:
            color_label(d['label'], d['tag'], fmt=d['fmt'])


class HMIButtonList(object):
    def __init__(self, tk_parent, dim=1, btn_args=None, grid_args=None):
        self.tk_parent = tk_parent
        self.frame = tk.Frame(tk_parent)
        self.frame.pack(anchor=tk.CENTER)
        self.dim = dim
        self.items_list = []
        self._ref_tk_btn = []
        self._btn_args = {} if btn_args is None else btn_args
        self._grid_args = {} if grid_args is None else grid_args

    def add(self, name, tag_valid=None, cmd=None, btn_args=None, grid_args=None):
        if btn_args is None:
            btn_args = {}
        if grid_args is None:
            grid_args = {}
        self.items_list.append({'name': name, 'tag_v': tag_valid, 'cmd': cmd, 'btn_args': btn_args,
                                'grid_args': grid_args})

    def build(self):
        for i, d_item in enumerate(self.items_list):
            d_item['btn_args'].update(self._btn_args)
            d_item['grid_args'].update(self._grid_args)
            b = tk.Button(self.frame, d_item['btn_args'], text=d_item['name'], command=d_item['cmd'])
            b.grid(d_item['grid_args'], row=int(i / self.dim), column=i % self.dim)
            self._ref_tk_btn.append({'button': b, 'tag_v': d_item['tag_v']})

    def update(self):
        for d in self._ref_tk_btn:
            if d.get('tag_v'):
                d['button'].configure(state='normal' if d['tag_v'].val else 'disabled')
