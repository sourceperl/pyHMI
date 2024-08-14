import tkinter as tk
from .UI import ui_def_ctx


class ConfirmDialog(tk.Toplevel):
    def __init__(self, master=None, title: str = '', text: str = '', valid_command=None, **kwargs):
        super().__init__(master, **kwargs)
        # args
        self.dialog_title = title
        self.dialog_text = text
        self.valid_command = valid_command
        # TopLevel setup
        self.transient(master)
        self.grab_set()
        self.title(self.dialog_title)
        # design the dialog box
        self.tk_txt_lbl = tk.Label(self, text=text, bg=self.cget('bg'))
        self.tk_btn_valid = tk.Button(self, text='Validation', command=self.ok)
        self.tk_btn_abort = tk.Button(self, text='Annulation', command=self.cancel)
        self.tk_txt_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        self.tk_btn_valid.grid(row=1, column=0, padx=10, pady=10)
        self.tk_btn_abort.grid(row=1, column=1, padx=10, pady=10)
        # default focus
        self.tk_btn_abort.focus_set()
        # destroy this dialog box on Escape press or after a 45s timeout
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(ms=45_000, func=self.destroy)

    def ok(self):
        if self.valid_command:
            self.valid_command()
        self.destroy()

    def cancel(self):
        self.destroy()


class ValveOpenCloseDialog(tk.Toplevel):
    def __init__(self, master=None, title: str = '', text: str = '', open_command=None, close_command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.transient(master)
        self.grab_set()
        self.title(title)
        self.open_command = open_command
        self.close_command = close_command
        tk.Label(self, text=text).grid(row=0, column=0, columnspan=3, padx=20, pady=20)
        if self.open_command:
            tk.Button(self, text='Ouverture', command=self.open).grid(row=1, column=0, padx=10, pady=5)
        if self.close_command:
            tk.Button(self, text='Fermeture', command=self.close).grid(row=1, column=1, padx=10, pady=5)
        tk.Button(self, text='Annulation', command=self.destroy, default=tk.ACTIVE).grid(row=1, column=2, padx=10,
                                                                                         pady=5)
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(45000, self.destroy)

    def open(self):
        if self.open_command:
            self.open_command()
        self.destroy()

    def close(self):
        if self.close_command:
            self.close_command()
        self.destroy()


class ValveESDDialog(tk.Toplevel):
    def __init__(self, master=None, title: str = '', text: str = '', stop_command=None, pst_command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.transient(master)
        self.grab_set()
        self.title(title)
        self.stop_command = stop_command
        self.pst_command = pst_command
        # build UI
        self.lbl_text = tk.Label(self, text=text)
        self.btn_close = tk.Button(self, text='Fermeture', command=self.stop, background=ui_def_ctx.colors.dial_bg_warn)
        self.btn_test = tk.Button(self, text='Test partiel', command=self.pst)
        self.btn_abort = tk.Button(self, text='Annulation', command=self.destroy, default=tk.ACTIVE)
        # map UI
        self.lbl_text.grid(row=0, column=0, columnspan=3, padx=20, pady=20)
        self.btn_close.grid(row=1, column=0, padx=10, pady=5)
        self.btn_test.grid(row=1, column=1, padx=10, pady=5)
        self.btn_abort.grid(row=1, column=2, padx=10, pady=5)
        # abort on 'Escape' press or after inactivity timeout
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(ms=45_000, func=self.destroy)

    def stop(self):
        if self.stop_command:
            self.stop_command()
        self.destroy()

    def pst(self):
        if self.pst_command:
            self.pst_command()
        self.destroy()


class SetStrValueDialog(tk.Toplevel):
    def __init__(self, master=None, title: str = 'SetStrValueDialog', text: str = 'Set a string',
                 valid_txt: str = 'Ok', cancel_txt: str = 'Cancel',
                 valid_command=None, **kwargs):
        super().__init__(master, **kwargs)
        # args
        self.dialog_title = title
        self.dialog_text = text
        self.valid_command = valid_command
        # public
        self.value = tk.StringVar(self, '')
        # TopLevel setup
        self.transient(master)
        self.grab_set()
        self.title(self.dialog_title)
        # design the dialog box
        self.tk_txt_lbl = tk.Label(self, text=text, bg=self.cget('bg'))
        self.tk_entry = tk.Entry(self, textvariable=self.value)
        self.tk_btn_valid = tk.Button(self, text=valid_txt, command=self.ok)
        self.tk_btn_cancel = tk.Button(self, text=cancel_txt, command=self.cancel)
        self.tk_txt_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        self.tk_entry.grid(row=1, column=0, columnspan=2, padx=20, pady=20)
        self.tk_btn_valid.grid(row=2, column=0, padx=10, pady=10)
        self.tk_btn_cancel.grid(row=2, column=1, padx=10, pady=10)
        # default focus
        self.tk_btn_cancel.focus_set()
        # destroy this dialog box on Escape press or after a 45s timeout
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(ms=45_000, func=self.destroy)

    def ok(self):
        if self.valid_command:
            self.valid_command(self.value.get())
        self.destroy()

    def cancel(self):
        self.destroy()


class SetIntValueDialog(tk.Toplevel):
    def __init__(self, master=None, title: str = '', text: str = '', valid_command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.transient(master)
        self.grab_set()
        self.title(title)
        self.valid_command = valid_command
        self.value = tk.IntVar()
        tk.Label(self, text=text).grid(row=0, column=0, columnspan=2, padx=20, pady=20)
        tk.Entry(self, textvariable=self.value).grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        tk.Button(self, text='Validation', command=self.ok).grid(row=2, column=0, padx=10, pady=10)
        tk.Button(self, text='Annulation', command=self.cancel, default=tk.ACTIVE).grid(row=2, column=1, padx=10,
                                                                                        pady=10)
        self.bind('<Escape>', lambda evt: self.destroy())
        self.after(45000, self.destroy)

    def ok(self):
        if self.valid_command:
            self.valid_command(self.value.get())
        self.destroy()

    def cancel(self):
        self.destroy()
