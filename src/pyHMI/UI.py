import tkinter as tk
from typing import Callable, List, Optional

from .Colors import UIColors
from .Tag import Tag


# some class
class UIContext:
    def __init__(self):
        self.colors = UIColors()
        self.update_ms = 500


ui_def_ctx = UIContext()


class UIFrameWidget:
    def __init__(self, master: tk.Widget, ctx: UIContext):
        # args
        self.master = master
        self.ctx = ctx
        # public
        self.frame = tk.Frame(self.master)
        # setup auto-refresh of update method (on-visibility and every update_ms)
        self.frame.bind('<Visibility>', lambda evt: self.update())
        self._auto_update()

    def _auto_update(self):
        if self.ctx.update_ms is None:
            self.frame.after(ms=1000, func=self._auto_update)
        else:
            if self.frame.winfo_ismapped():
                self.update()
            self.frame.after(ms=self.ctx.update_ms, func=self._auto_update)

    def update(self):
        pass


class UIBoolItem:
    def __init__(self, b_list: 'UIBoolListFrame', label_0: str, tag: Optional[Tag] = None, label_1: str = '',
                 state: bool = True, alarm: bool = False) -> None:
        # public
        self.b_list = b_list
        self.label_0 = label_0
        self.tag = tag
        self.label_1 = label_1
        self.state = state
        self.alarm = alarm
        # init tk labels
        self.tk_lbl_value = tk.Label(self.b_list.frame, text=self.label_0)
        # init default grid args
        self.tk_g_args_value_d = dict()

    def map(self, at_row: int):
        # map it with grids
        self.tk_lbl_value.grid(row=at_row, column=0, **self.tk_g_args_value_d)

    def update(self):
        if self.tag:
            # set label background color if tag value is True (GREEN for "state" item and RED for "alarm" item)
            bg_color = self.b_list.ctx.colors.bg_item_blank
            if self.tag.value:
                bg_color = self.b_list.ctx.colors.bg_item_alarm if self.alarm else self.b_list.ctx.colors.bg_item_state
            self.tk_lbl_value.configure(background=bg_color)
            # if label_1 is in use, update text widget resource
            if self.label_1:
                self.tk_lbl_value.configure(text=self.label_1 if self.tag.value else self.label_0)
            # update label foreground color if tag error flag is set
            f_color = self.b_list.ctx.colors.txt_com_error if self.tag.error else self.b_list.ctx.colors.txt_com_valid
            self.tk_lbl_value.configure(foreground=f_color)


class UIBoolListFrame(UIFrameWidget):
    """An helper to map a UI array of bool values (auto-refresh by update method)."""

    def __init__(self, master: tk.Widget, ctx: UIContext = ui_def_ctx, head_str: str = ''):
        super().__init__(master, ctx)
        # public
        self.items: List[UIBoolItem] = []
        # init tk labels
        self.tk_lbl_head = tk.Label(self.frame, text=head_str) if head_str else None
        # init grid args
        self.tk_g_args_head_d = dict()

    def add(self, label_0: str, tag: Optional[Tag] = None, label_1: str = '',
            state: bool = True, alarm: bool = False) -> UIBoolItem:
        bool_item = UIBoolItem(self, label_0=label_0, tag=tag, label_1=label_1, state=state, alarm=alarm)
        self.items.append(bool_item)
        return bool_item

    def build(self) -> tk.Frame:
        # add header label if set
        row_offset = 0
        if self.tk_lbl_head:
            self.tk_lbl_head.grid(row=0, **self.tk_g_args_head_d)
            row_offset += 1
        # add bool values from internal list
        for row, bool_item in enumerate(self.items):
            bool_item.map(at_row=row_offset + row)
        # return frame to directly map it with pack or other
        return self.frame

    def update(self):
        for bool_item in self.items:
            bool_item.update()


class UIAnalogItem:
    def __init__(self, a_list: 'UIAnalogListFrame', name: str, tag: Tag, unit: str = '', fmt: str = '') -> None:
        # public
        self.a_list = a_list
        self.name = name
        self.tag = tag
        self.unit = unit
        self.fmt = fmt
        # init tk labels
        self.tk_lbl_name = tk.Label(self.a_list.frame, text=self.name)
        self.tk_lbl_value = tk.Label(self.a_list.frame, background=self.a_list.ctx.colors.bg_item_blank)
        self.tk_lbl_unit = tk.Label(self.a_list.frame, text=self.unit)
        # init default grid args
        self.tk_g_args_name_d = dict(padx=10, pady=2)
        self.tk_g_args_value_d = dict(padx=10)
        self.tk_g_args_unit_d = dict(padx=5, sticky=tk.W)

    def map(self, at_row: int) -> None:
        # map it with grids
        self.tk_lbl_name.grid(row=at_row, column=0, **self.tk_g_args_name_d)
        self.tk_lbl_value.grid(row=at_row, column=1, **self.tk_g_args_value_d)
        self.tk_lbl_unit.grid(row=at_row, column=2, **self.tk_g_args_unit_d)

    def update(self) -> None:
        # format tag value
        try:
            value = f'{self.tag.value:{self.fmt}}'
            # replace default thousand separator ("2_000" -> "2 000")
            if isinstance(self.tag.value, (int, float)):
                value = value.replace('_', ' ')
        except ValueError:
            value = 'fmt error'
        # apply to tk label
        fg_color = self.a_list.ctx.colors.txt_com_error if self.tag.error else self.a_list.ctx.colors.txt_com_valid
        self.tk_lbl_value.configure(text=value, foreground=fg_color)


class UIAnalogListFrame(UIFrameWidget):
    """An helper to map a UI array of analog values (auto-refresh by update method)."""

    def __init__(self, master: tk.Widget, ctx: UIContext = ui_def_ctx) -> None:
        super().__init__(master, ctx)
        # public
        self.items: List[UIAnalogItem] = []

    def add(self, name: str, tag: Tag, unit: str = '', fmt: str = '') -> UIAnalogItem:
        analog_item = UIAnalogItem(self, name=name, tag=tag, unit=unit, fmt=fmt)
        self.items.append(analog_item)
        return analog_item

    def build(self) -> tk.Frame:
        # add analog values from internal list
        for row, analog_item in enumerate(self.items):
            analog_item.map(at_row=row)
        # return frame to directly map it with pack or other
        return self.frame

    def update(self) -> None:
        for analog_item in self.items:
            analog_item.update()


class UIButtonItem:
    def __init__(self, b_list: 'UIButtonListFrame', name: str, tag_valid: Optional[Tag] = None,
                 cmd: Optional[Callable] = None) -> None:
        # public
        self.b_list = b_list
        self.name = name
        self.tag_valid = tag_valid
        self.cmd = cmd
        # init tk labels
        self.tk_but = tk.Button(self.b_list.frame, text=self.name)
        if self.cmd:
            self.tk_but.configure(command=self.cmd)
        # init default grid args
        self.tk_but_g_args_d = dict()

    def map(self, at_row: int, at_column: int = 0) -> None:
        # map it with grids
        self.tk_but.grid(row=at_row, column=at_column, **self.tk_but_g_args_d)

    def update(self) -> None:
        if self.tag_valid:
            if self.tag_valid.value:
                self.tk_but.configure(state='normal')
            else:
                self.tk_but.configure(state='disabled')


class UIButtonListFrame(UIFrameWidget):
    """An helper to map a UI array of tk buttons (auto-refresh by update method)."""

    def __init__(self, master=None, ctx: UIContext = ui_def_ctx, n_cols: int = 1) -> None:
        super().__init__(master, ctx)
        # args
        self.n_cols = n_cols
        # public
        self.items: List[UIButtonItem] = []

    def add(self, name: str, tag_valid: Optional[Tag] = None, cmd: Optional[Callable] = None) -> UIButtonItem:
        button_item = UIButtonItem(self, name=name, tag_valid=tag_valid, cmd=cmd)
        self.items.append(button_item)
        return button_item

    def build(self) -> tk.Frame:
        # add analog values from internal list
        for row, button_item in enumerate(self.items):
            button_item.map(at_row=row // self.n_cols, at_column=row % self.n_cols)
        # return frame to directly map it with pack or other
        return self.frame

    def update(self) -> None:
        for button_item in self.items:
            button_item.update()
