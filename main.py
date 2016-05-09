#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import HMI_Canvas
from HMI_Canvas import HMICanvas
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
        self.master.geometry("800x600")
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
        # add toolbar
        self.init_toolbar()
        # update tabs when select
        self.do_every(self.update_toolbar, every_ms=500)

    def init_net_task(self):
        # PLC TBox
        self.tbx = ModbusDevice('163.111.181.85', port=502, timeout=2.0)
        # init modbus tables
        # read bit start at @3050, size is 49
        self.tbx.add_bits_table(3050, 49)
        # read bit start at @1536, size is 8
        self.tbx.add_bits_table(1536, 8)
        # read word at @22016
        self.tbx.add_words_table(22016)
        # read floats start at @5030, size is 7
        # self.tbx.add_floats_table(5030, 7)
        # PLC local
        self.reg = ModbusDevice('localhost', port=502, timeout=2.0)
        # read floats start at @5030, size is 7
        self.reg.add_floats_table(5030, 7)
        # read tags
        # external (from an external source)
        # bool
        self.CONF_NOP = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3059})
        self.CMD_PST_ACT = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3060})
        self.CONF_REG = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3061})
        self.CONF_NEU = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3062})
        self.CONF_SEC = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3063})
        self.PIL_TELE = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3064})
        #
        self.V1130_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3074})
        self.V1130_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3075})
        self.V1133_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3076})
        self.V1133_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3077})
        self.V1134_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3078})
        self.V1134_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3079})
        self.V1135_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3080})
        self.V1135_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3081})
        self.V1136_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3082})
        self.V1136_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3083})
        self.V1137_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3084})
        self.V1137_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3085})
        self.V1138_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3086})
        self.V1138_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3087})
        self.VL_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3088})
        self.VL_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3089})
        self.MV10_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3090})
        self.MV10_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3091})
        self.MV7_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3092})
        self.MV7_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3093})
        self.MV7_DEF_ELEC = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3094})
        self.MV7_DIST = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3095})
        self.MV7_HS = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3096})
        self.MV2_FDC_OUV = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3097})
        self.MV2_FDC_FER = Tags(False, src=self.tbx, ref={'type': 'bit', 'addr': 3098})
        # analog
        self.P_GNY_DN900 = Tags(90.0, src=self.reg, ref={'type': 'float', 'addr': 5030})
        # virtual (a tag from tag(s))
        self.V_BIDULE_TEST = Tags(False, get_cmd=lambda: self.V1130_FDC_FER.val and self.V1133_FDC_FER.val)
        # local (no external source)
        self.HMI_WORD = Tags(0)
        # write tags
        self.V1130_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 524})
        self.V1130_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 525})
        self.V1135_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 530})
        self.V1135_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 531})
        self.V1136_OPEN = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 532})
        self.V1136_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 533})
        self.MV2_CLOSE = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 0})
        self.MV2_PST = Tags(False, src=self.tbx, ref={'type': 'w_bit', 'addr': 0})

    def update_net_task(self):
        # update tags
        self.HMI_WORD.set(self.HMI_WORD.val + 1)

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
        self.map_int.add_vbox('PIT_485', 230, 340, get_value=lambda: self.P_GNY_DN900, prefix='P', suffix='bars')
        self.map_int.add_vbox('PIT_486', 570, 340, get_value=lambda: self.V1130_FDC_FER, prefix='P', suffix='bars')
        # self.map_int.add_value('PIT_486', 480, 300, tag='P_ARL', prefix='P', tk_fmt='{:.01f}', size=5, suffix='bars')
        # custom widget
        self.map_int.can.create_oval(50, 50, 150, 150, fill=HMI_Canvas.RED, outline=HMI_Canvas.RED, tag='CUST_LOCAL')
        self.map_int.can.create_text(100, 100, text='LOCAL MODE', tag='CUST_LOCAL')
        # build all
        self.map_int.build()

    def update_tab_interco(self):
        # update value box
        self.map_int.update_vbox()
        # update valves on canvas
        self.map_int.simple_valve.animate('V1130', self.V1130_FDC_OUV, self.V1130_FDC_FER)

    def init_tab_io_simul(self):
        # tab "I/O simul"
        # self.tab_sim['bg'] = 'bisque'
        # self.tab_sim.resizable(width=FALSE, height=FALSE)
        # Vanne 1130
        self.lblVal = LabelFrame(self.tab_sim, text='Etat vannes', padx=20, pady=20)
        self.frame1130 = LabelFrame(self.lblVal, borderwidth=2, text='V.1130', relief=GROOVE, padx=10, pady=10)
        self.open1130But = Button(self.frame1130, text="Open", padx=20, pady=15,
                                  command=lambda: self.V1130_OPEN.set(True) or self.V1130_CLOSE.set(False))
        self.open1130But.pack(fill=X)
        self.close1130But = Button(self.frame1130, text="Close", padx=20, pady=15,
                                   command=lambda: self.V1130_CLOSE.set(True) or self.V1130_OPEN.set(False))
        self.close1130But.pack(fill=X)
        self.frame1130.grid(padx=10, pady=10, row=0, column=0)
        # Vanne 1133
        self.frame1133 = LabelFrame(self.lblVal, borderwidth=2, text='V.1133', relief=GROOVE, padx=10, pady=10)
        self.open1133But = Button(self.frame1133, text='Open', padx=20, pady=15,
                                  command=lambda: self.tbx.write_bits(526, [True, False]))
        self.open1133But.pack(fill=X)
        self.close1133But = Button(self.frame1133, text='Close', padx=20, pady=15,
                                   command=lambda: self.tbx.write_bits(526, [False, True]))
        self.close1133But.pack(fill=X)
        self.frame1133.grid(padx=10, pady=10, row=0, column=1)
        # Vanne 1134
        self.frame1134 = LabelFrame(self.lblVal, borderwidth=2, text='V.1134', relief=GROOVE, padx=10, pady=10)
        self.open1134But = Button(self.frame1134, text='Open', padx=20, pady=15,
                                  command=lambda: self.tbx.write_bits(528, [True, False]))
        self.open1134But.pack(fill=X)
        self.close1134But = Button(self.frame1134, text='Close', padx=20, pady=15,
                                   command=lambda: self.tbx.write_bits(528, [False, True]))
        self.close1134But.pack(fill=X)
        self.frame1134.grid(padx=10, pady=10, row=0, column=2)
        # Vanne 1135
        self.frame1135 = LabelFrame(self.lblVal, borderwidth=2, text='V.1135', relief=GROOVE, padx=10, pady=10)
        self.open1135But = Button(self.frame1135, text='Open', padx=20, pady=15,
                                  command=lambda: self.V1135_OPEN.set(True) or self.V1135_CLOSE.set(False))
        self.open1135But.pack(fill=X)
        self.close1135But = Button(self.frame1135, text='Close', padx=20, pady=15,
                                   command=lambda: self.V1135_CLOSE.set(True) or self.V1135_OPEN.set(False))
        self.close1135But.pack(fill=X)
        self.frame1135.grid(padx=10, pady=10, row=0, column=3)
        # Vanne 1136
        self.frame1136 = LabelFrame(self.lblVal, borderwidth=2, text='V.1136', relief=GROOVE, padx=10, pady=10)
        self.open1136But = Button(self.frame1136, text='Open', padx=20, pady=15,
                                  command=lambda: self.V1136_OPEN.set(True) or self.V1136_CLOSE.set(False))
        self.open1136But.pack(fill=X)
        self.close1136But = Button(self.frame1136, text='Close', padx=20, pady=15,
                                   command=lambda: self.V1136_CLOSE.set(True) or self.V1136_OPEN.set(False))
        self.close1136But.pack(fill=X)
        self.frame1136.grid(padx=10, pady=10, row=1, column=0)
        # Vanne 1137
        self.frame1137 = LabelFrame(self.lblVal, borderwidth=2, text='V.1137', relief=GROOVE, padx=10, pady=10)
        self.open1137But = Button(self.frame1137, text='Open', padx=20, pady=15,
                                  command=lambda: self.tbx.write_bits(534, [True, False]))
        self.open1137But.pack(fill=X)
        self.close1137But = Button(self.frame1137, text='Close', padx=20, pady=15,
                                   command=lambda: self.tbx.write_bits(534, [False, True]))
        self.close1137But.pack(fill=X)
        self.frame1137.grid(padx=10, pady=10, row=1, column=1)
        # Vanne 1138
        self.frame1138 = LabelFrame(self.lblVal, borderwidth=2, text='V.1138', relief=GROOVE, padx=10, pady=10)
        self.open1138But = Button(self.frame1138, text='Open', padx=20, pady=15,
                                  command=lambda: self.tbx.write_bits(536, [True, False]))
        self.open1138But.pack(fill=X)
        self.close1138But = Button(self.frame1138, text='Close', padx=20, pady=15,
                                   command=lambda: self.tbx.write_bits(536, [False, True]))
        self.close1138But.pack(fill=X)
        self.frame1138.grid(padx=10, pady=10, row=1, column=2)
        self.lblVal.grid(padx=5, pady=5, row=0, columnspan=4)
        # Configuration poste
        self.lblConf = LabelFrame(self.tab_sim, text='Configuration', padx=20, pady=20)
        self.lblReg = Label(self.lblConf, text='REGIONAL', background='green')
        self.lblReg.pack(fill=X)
        self.lblNeu = Label(self.lblConf, text='NEUTRE')
        self.lblNeu.pack(fill=X)
        self.lblSec = Label(self.lblConf, text='SECURITE')
        self.lblSec.pack(fill=X)
        self.lblNop = Label(self.lblConf, text='NON OP.')
        self.lblNop.pack(fill=X)
        self.lblConf.grid(padx=5, pady=5, row=1, column=0, sticky=W+E+N+S)
        # Etat automate
        self.lblPlc = LabelFrame(self.tab_sim, text='Etat de l\'automate', padx=20, pady=20)
        self.lblTcAuto = Label(self.lblPlc, text='TC AUTO')
        self.lblTcAuto.pack(fill=X)
        self.lblSeqC = Label(self.lblPlc, text='SEQ EN COURS')
        self.lblSeqC.pack(fill=X)
        self.lblPlc.grid(padx=5, pady=5, row=1, column=1, sticky=W+E+N+S)
        # Pilotage
        self.lblPil = LabelFrame(self.tab_sim, text='Pilotage', padx=20, pady=20)
        self.lblPilTele = Label(self.lblPil, text='TELE')
        self.lblPilTele.pack(fill=X)
        self.lblPil.grid(padx=5, pady=5, row=1, column=2, sticky=W+E+N+S)
        # Commandes
        self.lblCmd = LabelFrame(self.tab_sim, text='Commandes', padx=20, pady=20)
        # Ack button
        self.ackButton = Button(self.lblCmd, text='Acquit défaut', command=self.ack_default)
        self.ackButton.pack(fill=X)
        self.lblCmd.grid(padx=5, pady=5, row=1, column=3, sticky=W+E+N+S)
        # display modbus cycle
        self.cycle_mbus_str = StringVar()
        Label(self.tab_sim, textvariable=self.cycle_mbus_str).grid(padx=5, pady=5, row=7, columnspan=3)

    def update_tab_simul(self):
        # local function
        def v2but(valve_label, fdc_open, fdc_close):
            bg_color_str = ('white', 'green', 'red', 'orange')
            if fdc_open.err or fdc_close.err:
                c_color = 'yellow'
            else:
                c_color = bg_color_str[fdc_open.val * 1 + fdc_close.val * 2]
            valve_label.configure(background=c_color)

        # update valve status
        # vanne 1130
        v2but(self.frame1130, self.V1130_FDC_OUV, self.V1130_FDC_FER)
        # vanne 1133
        v2but(self.frame1133, self.V1133_FDC_OUV, self.V1133_FDC_FER)
        # vanne 1134
        v2but(self.frame1134, self.V1134_FDC_OUV, self.V1134_FDC_FER)
        # vanne 1135
        v2but(self.frame1135, self.V1135_FDC_OUV, self.V1135_FDC_FER)
        # vanne 1136
        v2but(self.frame1136, self.V1136_FDC_OUV, self.V1136_FDC_FER)
        # vanne 1137
        v2but(self.frame1137, self.V1137_FDC_OUV, self.V1137_FDC_FER)
        # vanne 1138
        v2but(self.frame1138, self.V1138_FDC_OUV, self.V1138_FDC_FER)
        # update config.
        self.lblReg.configure(background='green' if self.CONF_REG.val else 'gray')
        self.lblNeu.configure(background='green' if self.CONF_NEU.val else 'gray')
        self.lblSec.configure(background='green' if self.CONF_SEC.val else 'gray')
        self.lblNop.configure(background='green' if self.CONF_NOP.val else 'gray')
        # PLC state
        self.lblPilTele.configure(text='TELE' if self.PIL_TELE.val else 'LOCAL')
        # label cycle modbus
        self.cycle_mbus_str.set('mot de vie TBOX=' + str(self.HMI_WORD.val))

    def update_tabs(self):
        # current ID of notebook select tab
        cur_tab = self.note.index(self.note.select())
        # run current update handler
        if cur_tab == self.note.index(self.tab_int):
            self.update_tab_interco()
        elif cur_tab == self.note.index(self.tab_sim):
            self.update_tab_simul()

    def init_toolbar(self):
        self.tbarFm = Frame(self.master)
        self.butTbox = Button(self.tbarFm, text='API T-Box', relief=SUNKEN)
        self.butTbox.pack(side=LEFT)
        self.butReg = Button(self.tbarFm, text='REG T640', relief=SUNKEN)
        self.butReg.pack(side=LEFT)
        self.tbarFm.pack(side=BOTTOM, fill=X)

    def update_toolbar(self):
        self.butTbox.configure(background='green' if self.tbx.connected else 'red')
        self.butReg.configure(background='green' if self.reg.connected else 'red')

    def ack_default(self):
        self.tbx.write_bit(522, True)
        time.sleep(.1)
        self.tbx.write_bit(522, False)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))


if __name__ == '__main__':
    # main Tk App
    root = tk.Tk()
    app = HMIApp(master=root)
    app.mainloop()
