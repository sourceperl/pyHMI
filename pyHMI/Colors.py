# -*- coding: utf-8 -*-

import tkinter as tk

# some const
# Canvas Pipe width
PIPE_WIDTH = 6
# Colors
RED = '#bc3f3c'
GREEN = '#51c178'
GRAY = '#2d2d2d'
BLUE = '#589df6'
WHITE = '#ffffff'
ORANGE = '#be9117'
PINK = 'hot pink'
BLACK = 'black'
VIOLET = 'dark violet'
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


# colors functions
def color_tag_state(tag):
    return STATE_COLOR[not tag.err and tag.val + 1]


def color_tag_alarm(tag):
    return ALARM_COLOR[not tag.err and tag.val + 1]


def color_tags_valve(tag_fdc_o, tag_fdc_c):
    return VALVE_COLOR[not (tag_fdc_o.err or tag_fdc_c.err) and (tag_fdc_o.val + tag_fdc_c.val * 2 + 1)]


def color_valve(tag_fdc_o, tag_fdc_c):
    return VALVE_COLOR[tag_fdc_o + tag_fdc_c * 2 + 1]


def color_label(tk_label, tag, fmt='%s'):
    tk_label.configure(text=fmt % tag.val, background=PINK if tag.err else WHITE)


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
