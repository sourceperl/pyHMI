#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import HMI
from HMI import HMICanvas
from HMI_Modbus import ModbusDevice
from HMI_Tags import Tags
import time
from tkinter import *
import tkinter as tk
from tkinter import ttk


class HMIApp(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        # create modbus client
        self.master.wm_title('Chilly simulator')
        # self.master.attributes('-fullscreen', True)
        self.master.geometry("800x500")
        # networks tasks
        self.init_net_task()
        self.do_every(self.update_net_task, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self.master)
        self.tab_int = Frame(self.note)
        self.tab_sim = Frame(self.note)
        self.note.add(self.tab_int, text='Interconnexion')
        self.note.add(self.tab_sim, text='I/O simul')
        self.note.select(self.tab_sim)
        self.note.pack(fill=X)
        # build tabs
        self.init_tab_interco()
        self.init_tab_io_simul()
        # update tabs when select
        self.do_every(self.update_tabs, every_ms=500)

    def init_net_task(self):
        # PLC TBox
        self.tbx = ModbusDevice('163.111.181.85', 502, timeout=2.0)
        # init modbus tables
        # read bit start at @512 size is 48
        self.tbx.r_bits(512, 48)
        # read bit start at @1536 size is 8
        self.tbx.r_bits(1536, 8)
        # read word at @22016
        self.tbx.r_words(22016)
        # create tags
        self.V1130_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 524})
        self.V1130_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 525})
        self.V1133_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 526})
        self.V1133_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 527})
        self.V1134_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 528})
        self.V1134_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 529})
        self.V1135_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 530})
        self.V1135_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 531})
        self.V1136_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 532})
        self.V1136_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 533})
        self.V1137_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 534})
        self.V1137_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 535})
        self.V1138_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 536})
        self.V1138_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 537})

        self.V_BIDULE_TEST = Tags(False, get_cmd=lambda: self.V1130_FDC_FER.val and self.V1133_FDC_FER.val)

    def update_net_task(self):
        # update tags
        pass

    def init_tab_interco(self):
        # tab "interconnexion"
        self.map_int = HMICanvas(self.tab_int, width=800, height=400, debug=False)
        # add button
        self.map_int.add_button('GNY', 230, 300, label='Gournay')
        self.map_int.add_button('ARL', 570, 300, label='Arleux')
        self.map_int.add_button('b3', 400, 230, label='VL 1')
        # add simple valve
        self.map_int.add_s_valve('V1134', 400, 50, label='V1134', zoom=0.8)
        self.map_int.add_s_valve('V1131', 350, 120, label='V1131', zoom=0.8)
        self.map_int.add_s_valve('V1132', 450, 120, label='V1132', zoom=0.8)
        self.map_int.add_s_valve('V1130', 400, 300, label='V1130', zoom=1)
        # add flow valve
        self.map_int.add_f_valve('VL1', 400, 190, zoom=0.8)
        # add point
        self.map_int.add_point('p1', 300, 50)
        self.map_int.add_point('p2', 500, 50)
        # add pipes
        self.map_int.add_pipe('t1', from_name='p1', to_name='V1134')
        self.map_int.add_pipe('t2', from_name='V1134', to_name='p2')
        self.map_int.add_pipe('t3', from_name='p1', to_name='V1131')
        self.map_int.add_pipe('t4', from_name='p2', to_name='V1132')
        self.map_int.add_pipe('t5', from_name='V1131', to_name='V1132')
        self.map_int.add_pipe('t6', from_name='GNY', to_name='p1')
        self.map_int.add_pipe('t7', from_name='ARL', to_name='p2')
        self.map_int.add_pipe('t8', from_name='p1', to_name='VL1')
        self.map_int.add_pipe('t9', from_name='p2', to_name='VL1')
        self.map_int.add_pipe('t10', from_name='GNY', to_name='V1130')
        self.map_int.add_pipe('t11', from_name='V1130', to_name='ARL')
        # add value box
        self.map_int.add_value('PIT_485', 230, 340, tag='P_GNY', prefix='P', suffix='bars')
        self.map_int.add_value('PIT_486', 570, 340, tag='P_ARL', prefix='P', suffix='bars')
        # self.map_int.add_value('PIT_486', 480, 300, tag='P_ARL', prefix='P', tk_fmt='{:.01f}', size=5, suffix='bars')
        # custom widget
        self.map_int.can.create_oval(50, 50, 150, 150, fill=HMI.RED, outline=HMI.RED, tag='CUST_LOCAL')
        self.map_int.can.create_text(100, 100, text='LOCAL MODE', tag='CUST_LOCAL')
        # build all
        self.map_int.build()

    def update_tab_interco(self):
        # update valve status
        with self.tbx.lock:
            # edit map_int canvas with analog value
            self.map_int.can.itemconfig(self.map_int.d_widget['PIT_486']['id_txt'], text=str(self.tbx.poll_cycle))

    def init_tab_io_simul(self):
        # tab "I/O simul"
        self.tab_sim['bg'] = 'bisque'
        # self.tab_sim.resizable(width=FALSE, height=FALSE)
        # Vanne 1130
        self.frame1130 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1130But = Button(self.frame1130, text="Open V.1130",
                                  command=lambda: self.tbx.w_bits(524, [True, False]))
        self.open1130But.pack()
        self.close1130But = Button(self.frame1130, text="Close V.1130",
                                   command=lambda: self.tbx.w_bits(524, [False, True]))
        self.close1130But.pack()
        self.frame1130.grid(padx=10, pady=10, row=0, column=0)
        # Vanne 1133
        self.frame1133 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1133But = Button(self.frame1133, text="Open V.1133",
                                  command=lambda: self.tbx.w_bits(526, [True, False]))
        self.open1133But.pack()
        self.close1133But = Button(self.frame1133, text="Close V.1133",
                                   command=lambda: self.tbx.w_bits(526, [False, True]))
        self.close1133But.pack()
        self.frame1133.grid(padx=10, pady=10, row=0, column=1)
        # Vanne 1134
        self.frame1134 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1134But = Button(self.frame1134, text="Open V.1134",
                                  command=lambda: self.tbx.w_bits(528, [True, False]))
        self.open1134But.pack()
        self.close1134But = Button(self.frame1134, text="Close V.1134",
                                   command=lambda: self.tbx.w_bits(528, [False, True]))
        self.close1134But.pack()
        self.frame1134.grid(padx=10, pady=10, row=0, column=2)
        # Vanne 1135
        self.frame1135 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1135But = Button(self.frame1135, text="Open V.1135",
                                  command=lambda: self.tbx.w_bits(530, [True, False]))
        self.open1135But.pack()
        self.close1135But = Button(self.frame1135, text="Close V.1135",
                                   command=lambda: self.tbx.w_bits(530, [False, True]))
        self.close1135But.pack()
        self.frame1135.grid(padx=10, pady=10, row=1, column=0)
        # Vanne 1136
        self.frame1136 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1136But = Button(self.frame1136, text="Open V.1136",
                                  command=lambda: self.tbx.w_bits(532, [True, False]))
        self.open1136But.pack()
        self.close1136But = Button(self.frame1136, text="Close V.1136",
                                   command=lambda: self.tbx.w_bits(532, [False, True]))
        self.close1136But.pack()
        self.frame1136.grid(padx=10, pady=10, row=1, column=1)
        # Vanne 1137
        self.frame1137 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1137But = Button(self.frame1137, text="Open V.1137",
                                  command=lambda: self.tbx.w_bits(534, [True, False]))
        self.open1137But.pack()
        self.close1137But = Button(self.frame1137, text="Close V.1137",
                                   command=lambda: self.tbx.w_bits(534, [False, True]))
        self.close1137But.pack()
        self.frame1137.grid(padx=10, pady=10, row=1, column=2)
        # Vanne 1138
        self.frame1138 = Frame(self.tab_sim, borderwidth=2, relief=GROOVE)
        self.open1138But = Button(self.frame1138, text="Open V.1138",
                                  command=lambda: self.tbx.w_bits(536, [True, False]))
        self.open1138But.pack()
        self.close1138But = Button(self.frame1138, text="Close V.1138",
                                   command=lambda: self.tbx.w_bits(536, [False, True]))
        self.close1138But.pack()
        self.frame1138.grid(padx=10, pady=10, row=2, column=0)
        # Ack
        self.ackButton = Button(self.tab_sim, text="Acquit défaut", command=self.ack_default)
        self.ackButton.grid(padx=5, pady=5, row=3, columnspan=3)
        # TCP link
        self.mbusButton = Button(self.tab_sim, text='Etat modbus')
        self.mbusButton.grid(padx=6, pady=5, row=4, columnspan=3)
        # Quit
        self.quitButton = Button(self.tab_sim, text="Quit", command=self.quit)
        self.quitButton.grid(padx=5, pady=5, row=5, columnspan=3)
        # display modbus cycle
        self.cycle_mbus_str = StringVar()
        Label(self.tab_sim, textvariable=self.cycle_mbus_str).grid(padx=5, pady=5, row=6, columnspan=3)

    def update_tab_simul(self):
        # local function
        def v2but(but_open, but_close, fdc_open, fdc_close):
            bg_color_str = ('white', 'green', 'red', 'orange')
            if fdc_open.err or fdc_close.err:
                c_color = 'yellow'
            else:
                c_color = bg_color_str[fdc_open.val * 1 + fdc_close.val * 2]
            but_open.configure(background=c_color)
            but_close.configure(background=c_color)

        # update valve status
        with self.tbx.lock:
            # vanne 1130
            v2but(self.open1130But, self.close1130But, self.V1130_FDC_OUV, self.V1130_FDC_FER)
            # vanne 1133
            v2but(self.open1133But, self.close1133But, self.V1133_FDC_OUV, self.V1133_FDC_FER)
            # vanne 1134
            v2but(self.open1134But, self.close1134But, self.V1134_FDC_OUV, self.V1134_FDC_FER)
            # vanne 1135
            v2but(self.open1135But, self.close1135But, self.V1135_FDC_OUV, self.V1135_FDC_FER)
            # vanne 1136
            v2but(self.open1136But, self.close1136But, self.V1136_FDC_OUV, self.V1136_FDC_FER)
            # vanne 1137
            v2but(self.open1137But, self.close1137But, self.V1137_FDC_OUV, self.V1137_FDC_FER)
            # vanne 1138
            v2but(self.open1138But, self.close1138But, self.V1138_FDC_OUV, self.V1138_FDC_FER)
            # mbus button is green if connection ok
            self.mbusButton.configure(background='green' if self.tbx.connected else 'red')
            # label cycle modbus
            self.cycle_mbus_str.set('mot de vie TBOX=' + str(self.tbx.poll_cycle))

    def update_tabs(self):
        # current ID of notebook select tab
        cur_tab = self.note.index(self.note.select())
        # run current update handler
        if cur_tab == self.note.index(self.tab_int):
            self.update_tab_interco()
        elif cur_tab == self.note.index(self.tab_sim):
            self.update_tab_simul()

    def ack_default(self):
        self.tbx.w_bit(522, True)
        time.sleep(.1)
        self.tbx.w_bit(522, False)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))


if __name__ == '__main__':
    # main Tk App
    root = tk.Tk()
    app = HMIApp(master=root)
    app.mainloop()
