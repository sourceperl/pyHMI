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
    def __init__(self, tk_parent, head_str=''):
        self.tk_parent = tk_parent
        self.items_list = []
        self.head_str = head_str
        self._ref_tk_lbl = []

    def add(self, name, tag, alarm=False, **tk_label_args):
        self.items_list.append({'name': name, 'tag': tag, 'alarm': alarm, 'tk_args': tk_label_args})

    def build(self):
        # head
        i_row = 0
        if self.head_str:
            tk.Label(self.tk_parent, text=self.head_str).grid(row=i_row)
            i_row += 1
        # body
        for d_item in self.items_list:
            l = tk.Label(self.tk_parent, d_item['tk_args'], text=d_item['name'])
            l.grid(row=i_row, column=0)
            i_row += 1
            self._ref_tk_lbl.append({'label': l, 'tag': d_item['tag'], 'alarm': d_item['alarm']})

    def update(self):
        for d in self._ref_tk_lbl:
            if d['alarm']:
                d['label'].configure(background=color_tag_alarm(d['tag']))
            else:
                d['label'].configure(background=color_tag_state(d['tag']))


class HMIAnalogList(object):
    def __init__(self, tk_parent):
        self.tk_parent = tk_parent
        self.items_list = []
        self._ref_tk_lbl = []

    def add(self, name, tag, unit='', fmt='%s', **tk_label_args):
        self.items_list.append({'name': name, 'tag': tag, 'unit': unit, 'fmt': fmt, 'tk_args': tk_label_args})

    def build(self):
        for i, d_item in enumerate(self.items_list):
            tk.Label(self.tk_parent, text=d_item['name']).grid(padx=10, pady=2, row=i, column=0)
            l = tk.Label(self.tk_parent, d_item['tk_args'])
            l.grid(padx=10, row=i, column=1)
            tk.Label(self.tk_parent, text=d_item['unit']).grid(padx=5, sticky=tk.W, row=i, column=2)
            self._ref_tk_lbl.append({'label': l, 'tag': d_item['tag'], 'fmt': d_item['fmt']})

    def update(self):
        for d in self._ref_tk_lbl:
            color_label(d['label'], d['tag'], fmt=d['fmt'])
