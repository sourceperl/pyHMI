#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.Canvas import HMICanvas
from pyHMI.Colors import *
from pyHMI.Dialog import ConfirmDialog, ValveOpenCloseDialog, ValveESDDialog
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag
import time
import tkinter as tk
from tkinter import ttk


class Devices(object):
    # init datasource
    # PLC TBox
    tbx_api = ModbusTCPDevice('163.111.181.85', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx_api.add_bits_table(3050, 61)
    tbx_api.add_bits_table(1536, 8)
    tbx_api.add_words_table(4000, 5)
    tbx_api.add_floats_table(5030, 8)
    # Reg. L1
    tbx_reg1 = ModbusTCPDevice('192.168.10.11', port=502, unit_id=1, timeout=5.0, refresh=1.0)
    tbx_reg1.add_bits_table(20500, 16)
    tbx_reg1.add_floats_table(20700, size=32)
    ### REMOVE THIS ###
    tbx_reg1.add_bits_table(240, 9)
    tbx_reg1.add_words_table(201, 6)
    ### REMOVE THIS ###
    # Reg. L2
    tbx_reg2 = ModbusTCPDevice('192.168.10.12', port=502, unit_id=1, timeout=5.0, refresh=1.0)
    tbx_reg2.add_bits_table(20500, 16)
    tbx_reg2.add_floats_table(20700, size=32)


class Tags(object):
    # tags list
    NULL_TAG = Tag(False)
    # Tbox PLC
    DEF_EDF = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3050})
    DEF_CHG = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3051})
    DEF_OND = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3052})
    DEF_ATD1 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3053})
    DEF_ATD2 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3054})
    DEF_FEU = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3055})
    DEF_CENT = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3056})
    TC_AUTO = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3057})
    TRA_EN_COURS = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3058})
    CONF_NOP = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3059})
    CMD_PST_ACT = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3060})
    CONF_REG = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3061})
    CONF_NEU = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3062})
    CONF_SEC = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3063})
    PIL_TELE = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3064, 'not': True})
    PIL_LOCAL = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3064})
    V1130_EV_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3066})
    V1130_EV_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3067})
    V1135_EV_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3068})
    V1135_EV_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3069})
    V1136_EV_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3070})
    V1136_EV_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3071})
    V1741_EV_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3072})
    V1130_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3074})
    V1130_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3075})
    V1133_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3076})
    V1133_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3077})
    V1134_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3078})
    V1134_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3079})
    V1135_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3080})
    V1135_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3081})
    V1136_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3082})
    V1136_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3083})
    V1137_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3084})
    V1137_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3085})
    V1138_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3086})
    V1138_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3087})
    VL_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3088})
    VL_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3089})
    V1740_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3090})
    V1740_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3091})
    MV7_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3092})
    MV7_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3093})
    MV7_DEF_ELEC = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3094})
    MV7_DIST = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3095})
    MV7_HS = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3096})
    V1741_FDC_OUV = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3097})
    V1741_FDC_FER = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3098})
    DEF_SEQ_MV1130 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3099})
    DEF_SEQ_MV1135 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3100})
    DEF_SEQ_MV1136 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3101})
    SEQ_MV1130_EN_COURS = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3102})
    SEQ_MV1135_EN_COURS = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3103})
    SEQ_MV1136_EN_COURS = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3104})
    DELTA_P_INF_1_5 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3105})
    DELTA_P_INF_0_5 = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3106})
    V1741_PST_EN_COURS = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3107})
    V1741_DEF_PST = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3108})
    DEF_DJ_220V = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3109})
    DEF_DJ_24V = Tag(False, src=Devices.tbx_api, ref={'type': 'bit', 'addr': 3110})
    TRA_REG_V_NEU = Tag(False, src=Devices.tbx_api, ref={'type': 'word', 'addr': 4000})
    TRA_REG_V_SEC = Tag(False, src=Devices.tbx_api, ref={'type': 'word', 'addr': 4001})
    TRA_NEU_V_REG = Tag(False, src=Devices.tbx_api, ref={'type': 'word', 'addr': 4002})
    TRA_NEU_V_SEC = Tag(False, src=Devices.tbx_api, ref={'type': 'word', 'addr': 4003})
    API_TBX_MDV = Tag(False, src=Devices.tbx_api, ref={'type': 'word', 'addr': 4004})
    P_GNY_DN900 = Tag(0.0, src=Devices.tbx_api, ref={'type': 'float', 'addr': 5030})
    # P_GNY_DN800 = Tags(90.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5032})
    P_ARL = Tag(90.0, src=Devices.tbx_api, ref={'type': 'float', 'addr': 5034})
    # P_AV_VL = Tags(90.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5036})
    Q_ANTENNES = Tag(0.0, src=Devices.tbx_api, ref={'type': 'float', 'addr': 5038})
    POS_VL = Tag(0.0, src=Devices.tbx_api, ref={'type': 'float', 'addr': 5040})
    POS_MV7 = Tag(0.0, src=Devices.tbx_api, ref={'type': 'float', 'addr': 5042})
    P_CPTGE = Tag(0.0, src=Devices.tbx_api, ref={'type': 'float', 'addr': 5044})
    # T-Box Reg L1
    # read bits
    REG1_MARCHE = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20500})
    REG1_ERR_C_WOBBE = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20501})
    REG1_ERR_C_PCS = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20502})
    REG1_ERR_C_DEBIT = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20503})
    REG1_DEF_M_WOBBE = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20504})
    REG1_DEF_M_PCS = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20505})
    REG1_DEF_M_DEBIT = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20506})
    REG1_PID_WOBBE_A = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20507})
    REG1_PID_PCS_A = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20508})
    REG1_PID_DEBIT_A = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20509})
    REG1_INH_M_WOBBE = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20510})
    REG1_INH_M_PCS = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20511})
    REG1_INH_M_DEBIT = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20512})
    REG1_AUTO_D = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20513})
    REG1_AUTO_L = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20514})
    REG1_AUTO_MANU = Tag(False, src=Devices.tbx_reg1, ref={'type': 'bit', 'addr': 20515})
    # read floats
    REG1_C_WOBBE_ACT = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20700})
    REG1_C_WOBBE_CSR = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20702})
    REG1_C_PCS_ACT = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20704})
    REG1_C_PCS_CSR = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20706})
    REG1_C_DEBIT_ACT = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20708})
    REG1_C_DEBIT_CSR = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20710})
    REG1_M_WOBBE = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20712})
    REG1_M_PCS = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20714})
    REG1_M_DEBIT = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20716})
    REG1_OUT_REG = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20718})
    REG1_OUT_PID_WOBBE = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20720})
    REG1_OUT_PID_PCS = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20722})
    REG1_OUT_PID_DEBIT = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20724})
    REG1_MDV = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'float', 'addr': 20762})
    # virtuals
    REG1_LOCAL = Tag(False, get_cmd=lambda: not Tags.REG1_AUTO_D.val)
    REG1_ARRET = Tag(False, get_cmd=lambda: not Tags.REG1_MARCHE.val)
    REG1_DLT_C_WOBBE = Tag(0.0, get_cmd=lambda: Tags.REG1_C_WOBBE_ACT.e_val - Tags.REG1_M_WOBBE.e_val)
    REG1_DLT_C_PCS = Tag(0.0, get_cmd=lambda: Tags.REG1_C_PCS_ACT.e_val - Tags.REG1_M_PCS.e_val)
    REG1_DLT_C_DEBIT = Tag(0.0, get_cmd=lambda: Tags.REG1_C_DEBIT_ACT.e_val - Tags.REG1_M_DEBIT.e_val)
    # write bits
    REG1_MODE_AUTO = Tag(False, src=Devices.tbx_reg1, ref={'type': 'w_bit', 'addr': 20560})
    REG1_MODE_MANU = Tag(False, src=Devices.tbx_reg1, ref={'type': 'w_bit', 'addr': 20561})
    # write floats
    REG1_W_CONS_W = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 20780})
    REG1_W_CONS_P = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 20782})
    REG1_W_CONS_D = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 20784})
    REG1_W_OUV_VL = Tag(0.0, src=Devices.tbx_reg1, ref={'type': 'w_float', 'addr': 20786})

    # DELTA_P_VL = Tag(0, get_cmd=lambda: Tags.REG_P_AM_VL.e_val - Tags.REG_P_AV_VL.e_val)
    P_ANTENNES = Tag(0, get_cmd=lambda: Tags.P_CPTGE.e_val - 1.0)
    # local (no external source)
    HMI_WORD = Tag(0)
    HMI_WORD2 = Tag(0)

    @classmethod
    def update_tags(cls):
        # update tags
        cls.HMI_WORD.set(cls.HMI_WORD.val + 1)
        cls.HMI_WORD2.set(cls.HMI_WORD2.val + 3)


class HMITab(tk.Frame):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, notebook, *args, **kwargs)
        # global tk app shortcut
        self.notebook = notebook
        self.app = notebook.master
        # frame auto-refresh delay (in ms)
        self.update_ms = update_ms
        # setup auto-refresh of notebook tab (on-visibility and every update_ms)
        self.bind('<Visibility>', lambda evt: self.tab_update())
        self._tab_update()

    def _tab_update(self):
        if self.winfo_ismapped():
            self.tab_update()
        self.master.after(self.update_ms, self._tab_update)

    def tab_update(self):
        pass


class TabSyno(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # tab "interconnexion"
        self.map_int = HMICanvas(self, width=800, height=550, debug=False)
        # add button
        self.map_int.add_button('GNY_800', 100, 400, text='Gournay DN800', state='disabled',
                                disabledforeground=BLACK, borderwidth=0)
        self.map_int.add_button('GNY_900', 100, 500, text='Gournay DN900',
                                command=lambda: self.notebook.select(self.app.tab_gny_dn900))
        self.map_int.add_button('ARL', 700, 400, text='Arleux DN800', state='disabled',
                                disabledforeground=BLACK, borderwidth=0)
        self.map_int.add_button('ANT_REG', 700, 50, text='Antennes REG', state='disabled',
                                disabledforeground=BLACK, borderwidth=0)
        self.map_int.add_button('MANAGE_V1130', 480, 370, text='V1130',
                                command=self.app.confirm_v1130, state='disabled')
        self.map_int.add_button('MANAGE_V1135', 660, 140, text='V1135',
                                command=self.app.confirm_v1135, state='disabled')
        self.map_int.add_button('MANAGE_V1136', 480, 200, text='V1136',
                                command=self.app.confirm_v1136, state='disabled')
        self.map_int.add_button('MANAGE_V1741', 480, 470, text='V1741',
                                command=self.app.confirm_v1741, state='disabled')
        # add simple valve
        self.map_int.add_s_valve('V1133', 570, 340, label='V1133', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1134', 230, 340, label='V1134', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1137', 230, 260, label='V1137', zoom=0.8, align='v')
        self.map_int.add_s_valve('V1138', 230, 120, label='V1138', zoom=0.8, align='v')
        # add simple valve
        self.map_int.add_m_valve('V1130', 400, 400, label='V1130', zoom=1)
        self.map_int.add_m_valve('V1135', 570, 140, label='V1135', zoom=0.8, align='v')
        self.map_int.add_m_valve('V1136', 400, 230, label='V1136', zoom=0.8)
        self.map_int.add_m_valve('V1741', 400, 500, label='V1741', zoom=1)
        # add flow valve
        self.map_int.add_f_valve('VL1', 230, 190, label='VL', zoom=0.8, align='v')
        # add point
        self.map_int.add_point('p1', 300, 50)
        self.map_int.add_point('p2', 570, 50)
        self.map_int.add_point('p3', 230, 400)
        self.map_int.add_point('p4', 570, 400)
        self.map_int.add_point('p5', 570, 230)
        # add pipes
        self.map_int.add_pipe('t6', from_name='p3', to_name='p1')
        self.map_int.add_pipe('t8', from_name='Q_ANTENNES', to_name='p2')
        self.map_int.add_pipe('t9', from_name='p2', to_name='V1135')
        self.map_int.add_pipe('t10', from_name='p3', to_name='V1130')
        self.map_int.add_pipe('t11', from_name='V1130', to_name='p4')
        self.map_int.add_pipe('t12', from_name='p4', to_name='ARL')
        self.map_int.add_pipe('t13', from_name='GNY_800', to_name='p3')
        self.map_int.add_pipe('t14', from_name='GNY_900', to_name='V1741')
        self.map_int.add_pipe('t15', from_name='p4', to_name='V1741')
        self.map_int.add_pipe('t16', from_name='p1', to_name='V1136')
        self.map_int.add_pipe('t17', from_name='V1136', to_name='p5')
        self.map_int.add_pipe('t18', from_name='p1', to_name='Q_ANTENNES')
        self.map_int.add_pipe('t19', from_name='V1135', to_name='p5')
        self.map_int.add_pipe('t20', from_name='p5', to_name='V1133')
        self.map_int.add_pipe('t21', from_name='V1133', to_name='p4')
        self.map_int.add_pipe('t22', from_name='p4', to_name='ANT_REG')
        # add value box
        self.map_int.add_vbox('P_GNY_DN900', 230, 475, get_value=lambda: Tags.P_GNY_DN900, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_GNY_DN800', 160, 300, get_value=lambda: Tags.NULL_TAG, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_ARL', 640, 300, get_value=lambda: Tags.P_ARL, prefix='P', suffix='bars')
        self.map_int.add_vbox('P_AV_VL', 160, 80, get_value=lambda: Tags.NULL_TAG, prefix='P', suffix='bars')
        self.map_int.add_vbox('OUV_VL', 160, 190, get_value=lambda: Tags.NULL_TAG, prefix='', suffix='%')
        self.map_int.add_vbox('Q_ANTENNES', 375, 50, get_value=lambda: Tags.Q_ANTENNES, prefix='Q', suffix='Nm3/h',
                              tk_fmt='{:.0f}')
        self.map_int.add_vbox('P_ANTENNES', 500, 50, get_value=lambda: Tags.P_ANTENNES, prefix='P', suffix='bars')
        # custom widget
        # Pilotage poste
        self.frmConf = tk.Frame(self.map_int.can)
        tk.Label(self.frmConf, text='Pilot. poste').pack(fill=tk.X)
        self.cnfDist = tk.Label(self.frmConf, text='Distant', background=WHITE)
        self.cnfDist.pack(fill=tk.X)
        self.cnfLoc = tk.Label(self.frmConf, text='Local', background=WHITE)
        self.cnfLoc.pack(fill=tk.X)
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        # Configuration poste
        tk.Label(self.frmConf, text='TC Auto.').pack(fill=tk.X)
        self.cnfAuto = tk.Label(self.frmConf, text='Auto', background=WHITE)
        self.cnfAuto.pack(fill=tk.X)
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        # Configuration poste
        tk.Label(self.frmConf, text='Config. poste').pack(fill=tk.X)
        self.cnfReg = tk.Label(self.frmConf, text='Régionale', background=WHITE)
        self.cnfReg.pack(fill=tk.X)
        self.cnfNeu = tk.Label(self.frmConf, text='Neutre', background=WHITE)
        self.cnfNeu.pack(fill=tk.X)
        self.cnfSec = tk.Label(self.frmConf, text='Sécurité', background=WHITE)
        self.cnfSec.pack(fill=tk.X)
        self.cnfNop = tk.Label(self.frmConf, text='Non op.', background=WHITE)
        self.cnfNop.pack(fill=tk.X)
        self.frmConf.pack()
        tk.Label(self.frmConf, text='', background=GRAY).pack(fill=tk.X)
        self.map_int.can.create_window(55, 130, window=self.frmConf)
        # build all
        self.map_int.build()

    def tab_update(self):
        # update value box
        self.map_int.update_vbox()
        # update simple valves
        self.map_int.simple_valve.tag_anim('V1133', Tags.V1133_FDC_OUV, Tags.V1133_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1134', Tags.V1134_FDC_OUV, Tags.V1134_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1137', Tags.V1137_FDC_OUV, Tags.V1137_FDC_FER)
        self.map_int.simple_valve.tag_anim('V1138', Tags.V1138_FDC_OUV, Tags.V1138_FDC_FER)
        self.map_int.flow_valve.tag_anim('VL1', Tags.VL_FDC_OUV, Tags.VL_FDC_FER)
        self.map_int.flow_valve.pos_tag_anim('VL1', Tags.POS_VL)
        # update motor valves
        self.map_int.motor_valve.tag_anim('V1130', Tags.V1130_FDC_OUV, Tags.V1130_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1130', Tags.V1130_EV_OUV, Tags.V1130_EV_FER,
                                                Tags.DEF_SEQ_MV1130)
        self.map_int.motor_valve.tag_anim('V1135', Tags.V1135_FDC_OUV, Tags.V1135_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1135', Tags.V1135_EV_OUV, Tags.V1135_EV_FER,
                                                Tags.DEF_SEQ_MV1135)
        self.map_int.motor_valve.tag_anim('V1136', Tags.V1136_FDC_OUV, Tags.V1136_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1136', Tags.V1136_EV_OUV, Tags.V1136_EV_FER,
                                                Tags.DEF_SEQ_MV1136)
        self.map_int.motor_valve.tag_anim('V1741', Tags.V1741_FDC_OUV, Tags.V1741_FDC_FER)
        self.map_int.motor_valve.motor_tag_anim('V1741', Tags.NULL_TAG, Tags.V1741_EV_FER)
        # update config.
        self.cnfDist.configure(background=color_tag_state(Tags.PIL_TELE))
        self.cnfLoc.configure(background=color_tag_state(Tags.PIL_LOCAL))
        self.cnfAuto.configure(background=color_tag_state(Tags.TC_AUTO))
        self.cnfReg.configure(background=color_tag_state(Tags.CONF_REG))
        self.cnfNeu.configure(background=color_tag_state(Tags.CONF_NEU))
        self.cnfSec.configure(background=color_tag_state(Tags.CONF_SEC))
        self.cnfNop.configure(background=color_tag_state(Tags.CONF_NOP))
        # validate command when local mode active
        if Tags.PIL_LOCAL.val:
            self.map_int.d_widget['MANAGE_V1130']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1135']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1136']['obj'].configure(state='normal')
            self.map_int.d_widget['MANAGE_V1741']['obj'].configure(state='normal')
        else:
            self.map_int.d_widget['MANAGE_V1130']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1135']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1136']['obj'].configure(state='disabled')
            self.map_int.d_widget['MANAGE_V1741']['obj'].configure(state='disabled')


class TabRegL1(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Some vars
        self.manu_str = tk.StringVar(value='0.0')
        self.cons_w_str = tk.StringVar(value='0')
        self.cons_p_str = tk.StringVar(value='0')
        self.cons_d_str = tk.StringVar(value='0')
        # Etats régulateur
        self.frmEtatReg = tk.LabelFrame(self, text='Etats régulateur', padx=10, pady=10)
        self.frmEtatReg.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.etat_l = HMIBoolList(self.frmEtatReg, lbl_args={'width': 20}, grid_args={'padx': 20})
        self.etat_l.add('Marche', Tags.REG1_MARCHE)
        self.etat_l.add('Arrêt', Tags.REG1_ARRET)
        self.etat_l.add('Auto Distant', Tags.REG1_AUTO_D)
        self.etat_l.add('Auto Local', Tags.REG1_AUTO_L)
        self.etat_l.add('Manuel', Tags.REG1_AUTO_MANU)
        self.etat_l.add('Déf. mesure Wobbe', Tags.REG1_DEF_M_WOBBE, alarm=True)
        self.etat_l.add('Déf. mesure PCS', Tags.REG1_DEF_M_PCS, alarm=True)
        self.etat_l.add('Déf. mesure débit', Tags.REG1_DEF_M_DEBIT, alarm=True)
        self.etat_l.add('Err. consigne Wobbe', Tags.REG1_ERR_C_WOBBE, alarm=True)
        self.etat_l.add('Err. consigne PCS', Tags.REG1_ERR_C_PCS, alarm=True)
        self.etat_l.add('Err. consigne débit', Tags.REG1_ERR_C_DEBIT, alarm=True)
        self.etat_l.build()
        # Consignes régulateur
        self.frmConsReg = tk.LabelFrame(self, text='Consignes régulateur', padx=10, pady=10)
        self.frmConsReg.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        self.cons_r = HMIAnalogList(self.frmConsReg, lbl_args={'width': 10})
        self.cons_r.add('Consigne Wobbe active', Tags.REG1_C_WOBBE_ACT, unit='wh/nm3', fmt='%0.f')
        self.cons_r.add('Consigne Wobbe CSR', Tags.REG1_C_WOBBE_CSR, unit='wh/nm3', fmt='%0.f')
        self.cons_r.add('Consigne PCS active', Tags.REG1_C_PCS_ACT, unit='wh/nm3', fmt='%0.f')
        self.cons_r.add('Consigne PCS CSR', Tags.REG1_C_PCS_CSR, unit='wh/nm3', fmt='%0.f')
        self.cons_r.add('Consigne débit active', Tags.REG1_C_DEBIT_ACT, unit='nm3/h', fmt='%0.f')
        self.cons_r.add('Consigne débit CSR', Tags.REG1_C_DEBIT_CSR, unit='nm3/h', fmt='%0.f')
        self.cons_r.add('DEBUG mot de vie Reg. 1', Tags.REG1_MDV, unit='', fmt='%0.f')
        self.cons_r.build()
        # Mode automatique local
        self.frmAutoReg = tk.LabelFrame(self, text='Mode automatique local', padx=10, pady=10)
        self.frmAutoReg.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NSEW)
        # wobbe
        tk.Label(self.frmAutoReg, text='Consigne Wobbe').grid(row=0, column=0, padx=5, pady=5)
        self.ent_cons_w = tk.Entry(self.frmAutoReg, width='6', justify=tk.RIGHT, textvariable=self.cons_w_str)
        self.ent_cons_w.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.frmAutoReg, text='wh/nm3').grid(row=0, column=2, padx=5, pady=5)
        self.but_cons_w = tk.Button(self.frmAutoReg, text='Set', command=self.send_cons_w_value)
        self.but_cons_w.grid(row=0, column=3, padx=5, pady=5)
        # pcs
        tk.Label(self.frmAutoReg, text='Consigne PCS').grid(row=1, column=0, padx=5, pady=5)
        self.ent_cons_p = tk.Entry(self.frmAutoReg, width='6', justify=tk.RIGHT, textvariable=self.cons_p_str)
        self.ent_cons_p.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(self.frmAutoReg, text='wh/nm3').grid(row=1, column=2, padx=5, pady=5)
        self.but_cons_p = tk.Button(self.frmAutoReg, text='Set', command=self.send_cons_p_value)
        self.but_cons_p.grid(row=1, column=3, padx=5, pady=5)
        # débit
        tk.Label(self.frmAutoReg, text='Consigne débit').grid(row=2, column=0, padx=5, pady=5)
        self.ent_cons_d = tk.Entry(self.frmAutoReg, width='6', justify=tk.RIGHT, textvariable=self.cons_d_str)
        self.ent_cons_d.grid(row=2, column=1, padx=5, pady=5)
        tk.Label(self.frmAutoReg, text='nm3/h').grid(row=2, column=2, padx=5, pady=5)
        self.but_cons_d = tk.Button(self.frmAutoReg, text='Set', command=self.send_cons_d_value)
        self.but_cons_d.grid(row=2, column=3, padx=5, pady=5)
        # PID menant
        self.frmEtatPid = tk.LabelFrame(self, text='PID menant', padx=10, pady=10)
        self.frmEtatPid.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.etat_pid = HMIBoolList(self.frmEtatPid, lbl_args={'width': 10}, grid_args={'padx': 10})
        self.etat_pid.add('Wobbe', Tags.REG1_PID_WOBBE_A)
        self.etat_pid.add('PCS', Tags.REG1_PID_PCS_A)
        self.etat_pid.add('débit', Tags.REG1_PID_DEBIT_A)
        self.etat_pid.build()
        # PID inhibition
        self.frmInhPid = tk.LabelFrame(self, text='PID inhibition', padx=10, pady=10)
        self.frmInhPid.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.inh_pid = HMIBoolList(self.frmInhPid, lbl_args={'width': 10}, grid_args={'padx': 10})
        self.inh_pid.add('Wobbe', Tags.REG1_INH_M_WOBBE)
        self.inh_pid.add('PCS', Tags.REG1_INH_M_PCS)
        self.inh_pid.add('débit', Tags.REG1_INH_M_DEBIT)
        self.inh_pid.build()
        # Mesures régulateur
        self.frmMesReg = tk.LabelFrame(self, text='Mesures régulateur', padx=10, pady=10)
        self.frmMesReg.grid(row=1, column=2, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.mes_r = HMIAnalogList(self.frmMesReg, lbl_args={'width': 10})
        self.mes_r.add('Mesure Wobbe', Tags.REG1_M_WOBBE, unit='wh/nm3', fmt='%0.f')
        self.mes_r.add('Mesure PCS', Tags.REG1_M_PCS, unit='wh/nm3', fmt='%0.f')
        self.mes_r.add('Mesure débit', Tags.REG1_M_DEBIT, unit='nm3/h', fmt='%0.f')
        self.mes_r.add('Sortie régulateur', Tags.REG1_OUT_REG, unit='%', fmt='%0.2f')
        self.mes_r.add('PID Wobbe', Tags.REG1_OUT_PID_WOBBE, unit='%', fmt='%0.2f')
        self.mes_r.add('PID PCS', Tags.REG1_OUT_PID_PCS, unit='%', fmt='%0.2f')
        self.mes_r.add('PID débit', Tags.REG1_OUT_PID_DEBIT, unit='%', fmt='%0.2f')
        self.mes_r.build()
        # Divers
        self.frmErr = tk.LabelFrame(self, text='Ecart consigne/mesure', padx=10, pady=10)
        self.frmErr.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.err_l = HMIAnalogList(self.frmErr, lbl_args={'width': 10})
        self.err_l.add('Ecart Wobbe', Tags.REG1_DLT_C_WOBBE, unit='wh/nm3', fmt='%0.f')
        self.err_l.add('Ecart PCS', Tags.REG1_DLT_C_PCS, unit='wh/nm3', fmt='%0.f')
        self.err_l.add('Ecart débit', Tags.REG1_DLT_C_DEBIT, unit='nm3/h', fmt='%0.f')
        self.err_l.build()
        # Commande de la sortie du régulateur
        self.frmManuReg = tk.LabelFrame(self, text='Mode manuel', padx=10, pady=10)
        self.frmManuReg.grid(row=1, column=3, padx=5, pady=5, sticky=tk.NSEW)
        tk.Label(self.frmManuReg, text='Sortie').grid(row=0, column=0, padx=5, pady=5)
        self.ent_man = tk.Entry(self.frmManuReg, width='6', justify=tk.RIGHT, textvariable=self.manu_str)
        self.ent_man.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.frmManuReg, text='%').grid(row=0, column=2, padx=5, pady=5)
        self.but_man = tk.Button(self.frmManuReg, text='Set', command=self.send_man_value)
        self.but_man.grid(row=0, column=3, padx=5, pady=5)
        # Choix des modes du régulateur
        self.frmManuReg = tk.LabelFrame(self, text='Choix du mode', padx=10, pady=10)
        self.frmManuReg.grid(row=2, column=3, padx=5, pady=5, sticky=tk.NSEW)
        self.mode_l = HMIButtonList(self.frmManuReg, btn_args={'width': 15}, grid_args={'pady': 5})
        self.mode_l.add('mode automatique', tag_valid=Tags.REG1_LOCAL, cmd=lambda: Tags.REG1_MODE_AUTO.set(True),
                        btn_args={'bg': GREEN})
        self.mode_l.add('mode manuel', tag_valid=Tags.REG1_LOCAL, cmd=lambda: Tags.REG1_MODE_MANU.set(True),
                        btn_args={'bg': RED})
        self.mode_l.build()
        # install callback
        self.manu_str.trace('w', self.manu_str_refresh)
        self.cons_w_str.trace('w', self.cons_w_str_refresh)
        self.cons_p_str.trace('w', self.cons_p_str_refresh)
        self.cons_d_str.trace('w', self.cons_d_str_refresh)

    def tab_update(self):
        # refresh widget
        self.etat_l.update()
        self.cons_r.update()
        self.mes_r.update()
        self.err_l.update()
        self.mode_l.update()
        self.etat_pid.update()
        self.inh_pid.update()
        # update manu entry
        self.manu_str_refresh()
        self.cons_w_str_refresh()
        self.cons_p_str_refresh()
        self.cons_d_str_refresh()

    def cons_w_str_refresh(self, *args):
        # update manu entry
        if Tags.REG1_LOCAL.val:
            self.but_cons_w.configure(state='normal')
            try:
                if abs(Tags.REG1_C_WOBBE_ACT.val - float(self.cons_w_str.get())) < 1.0:
                    self.ent_cons_w.config(bg='white')
                else:
                    self.ent_cons_w.config(bg='yellow2')
            except ValueError:
                self.ent_cons_w.config(bg='red')
        else:
            self.ent_cons_w.config(bg='white')
            self.but_cons_w.configure(state='disabled')
            self.cons_w_str.set('%.f' % Tags.REG1_C_WOBBE_ACT.val)

    def send_cons_w_value(self):
        try:
            send_cons = float(self.cons_w_str.get())
            ConfirmDialog(self, title='Confirmation consigne',
                          text='Envoi consigne Wobbe %.f wh/nm3 ?' % send_cons,
                          valid_command=lambda: Tags.REG1_W_CONS_W.set(send_cons))
            self.ent_cons_w.config(bg='white')
        except ValueError:
            self.ent_cons_w.config(bg='red')

    def cons_p_str_refresh(self, *args):
        # update manu entry
        if Tags.REG1_LOCAL.val:
            self.but_cons_p.configure(state='normal')
            try:
                if abs(Tags.REG1_C_PCS_ACT.val - float(self.cons_p_str.get())) < 1.0:
                    self.ent_cons_p.config(bg='white')
                else:
                    self.ent_cons_p.config(bg='yellow2')
            except ValueError:
                self.ent_cons_p.config(bg='red')
        else:
            self.ent_cons_p.config(bg='white')
            self.but_cons_p.configure(state='disabled')
            self.cons_p_str.set('%.f' % Tags.REG1_C_PCS_ACT.val)

    def send_cons_p_value(self):
        try:
            send_cons = float(self.cons_p_str.get())
            ConfirmDialog(self, title='Confirmation consigne',
                          text='Envoi consigne PCS %.f wh/nm3 ?' % send_cons,
                          valid_command=lambda: Tags.REG1_W_CONS_P.set(send_cons))
            self.ent_cons_p.config(bg='white')
        except ValueError:
            self.ent_cons_p.config(bg='red')

    def cons_d_str_refresh(self, *args):
        # update manu entry
        if Tags.REG1_LOCAL.val:
            self.but_cons_d.configure(state='normal')
            try:
                if abs(Tags.REG1_C_DEBIT_ACT.val - float(self.cons_d_str.get())) < 1.0:
                    self.ent_cons_d.config(bg='white')
                else:
                    self.ent_cons_d.config(bg='yellow2')
            except ValueError:
                self.ent_cons_d.config(bg='red')
        else:
            self.ent_cons_d.config(bg='white')
            self.but_cons_d.configure(state='disabled')
            self.cons_d_str.set('%.f' % Tags.REG1_C_DEBIT_ACT.val)

    def send_cons_d_value(self):
        try:
            send_cons = float(self.cons_d_str.get())
            ConfirmDialog(self, title='Confirmation consigne',
                          text='Envoi consigne débit %.f nm3/h ?' % send_cons,
                          valid_command=lambda: Tags.REG1_W_CONS_D.set(send_cons))
            self.ent_cons_d.config(bg='white')
        except ValueError:
            self.ent_cons_d.config(bg='red')

    def manu_str_refresh(self, *args):
        # update manu entry
        if Tags.REG1_AUTO_MANU.val:
            self.but_man.configure(state='normal')
            try:
                if abs(Tags.REG1_OUT_REG.val - float(self.manu_str.get())) < 1.0:
                    self.ent_man.config(bg='white')
                else:
                    self.ent_man.config(bg='yellow2')
            except ValueError:
                self.ent_man.config(bg='red')
        else:
            self.ent_man.config(bg='white')
            self.but_man.configure(state='disabled')
            self.manu_str.set('%.2f' % Tags.REG1_OUT_REG.val)

    def send_man_value(self):
        try:
            send_cons = float(self.manu_str.get())
            ConfirmDialog(self, title='Confirmation consigne',
                          text='Envoi ouveture VL à %.2f %% ?' % send_cons,
                          valid_command=lambda: Tags.REG1_W_OUV_VL.set(send_cons))
            self.ent_man.config(bg='white')
        except ValueError:
            self.ent_man.config(bg='red')


class HMIToolbar(tk.Frame):
    def __init__(self, tk_app, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, tk_app, *args, **kwargs)
        self.tk_app = tk_app
        self.update_ms = update_ms
        # build toolbar
        self.butTbox = tk.Button(self, text='T-Box API', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butTbox.pack(side=tk.LEFT)
        self.butReg1 = tk.Button(self, text='T-Box REG L1', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butReg1.pack(side=tk.LEFT)
        self.butReg2 = tk.Button(self, text='T-Box REG L2', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butReg2.pack(side=tk.LEFT)
        self.lblDate = tk.Label(self, text='', font=('TkDefaultFont', 12))
        self.lblDate.pack(side=tk.RIGHT)
        self.pack(side=tk.BOTTOM, fill=tk.X)
        # setup auto-refresh of notebook tab (on-visibility and every update_ms)
        self.bind('<Visibility>', lambda evt: self.tab_update())
        self._tab_update()

    def _tab_update(self):
        self.tab_update()
        self.master.after(self.update_ms, self._tab_update)

    def tab_update(self):
        self.butTbox.configure(background=GREEN if Devices.tbx_api.connected else PINK)
        self.butReg1.configure(background=GREEN if Devices.tbx_reg1.connected else PINK)
        self.butReg2.configure(background=GREEN if Devices.tbx_reg2.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))


class HMIApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('Arleux mélangeur')
        # self.attributes('-fullscreen', True)
        # self.geometry('800x600')
        # periodic tags update
        self.do_every(Tags.update_tags, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab_syno = TabSyno(self.note)
        self.tab_reg_l1 = TabRegL1(self.note)
        self.note.add(self.tab_syno, text='Synoptique (F1)')
        self.note.add(self.tab_reg_l1, text='Régulation Ligne 1 (F2)')
        self.note.pack(fill=tk.BOTH, expand=True)
        # defaut selected tab
        self.note.select(self.tab_syno)
        # bind function keys to tabs
        self.bind('<F1>', lambda evt: self.note.select(self.tab_syno))
        self.bind('<F2>', lambda evt: self.note.select(self.tab_reg_l1))
        # self.bind('<F3>', lambda evt: self.note.select(self.tab_info))
        # build toolbar
        self.toolbar = HMIToolbar(self, update_ms=500)

    def do_every(self, do_cmd, every_ms=1000):
        do_cmd()
        self.after(every_ms, lambda: self.do_every(do_cmd, every_ms=every_ms))

    def confirm_region(self):
        ConfirmDialog(self, title='Confirmation', text='Passage en configuration régionale ?',
                      valid_command=lambda: Tags.CMD_CONF_REGION.set(True))

    def confirm_neutre(self):
        ConfirmDialog(self, title='Confirmation', text='Passage en configuration neutre ?',
                      valid_command=lambda: Tags.CMD_CONF_NEUTRE.set(True))

    def confirm_v1741(self):
        ValveESDDialog(self, title='V1741', text='Action sur vanne de sécurité V1741 ?',
                       stop_command=lambda: Tags.CMD_V1741_CLOSE.set(True),
                       pst_command=lambda: Tags.CMD_V1741_PST.set(True))

    def confirm_v1130(self):
        ValveOpenCloseDialog(self, title='V1130', text='Mouvement V1130 ?',
                             open_command=lambda: Tags.CMD_V1130_OPEN.set(True),
                             close_command=lambda: Tags.CMD_V1130_CLOSE.set(True))

    def confirm_v1135(self):
        ValveOpenCloseDialog(self, title='V1135', text='Mouvement V1135 ?',
                             open_command=lambda: Tags.CMD_V1135_OPEN.set(True),
                             close_command=lambda: Tags.CMD_V1135_CLOSE.set(True))

    def confirm_v1136(self):
        ValveOpenCloseDialog(self, title='V1136', text='Mouvement V1136 ?',
                             open_command=lambda: Tags.CMD_V1136_OPEN.set(True),
                             close_command=lambda: Tags.CMD_V1136_CLOSE.set(True))

    @staticmethod
    def ack_default():
        Devices.tbx_api.write_bit(522, True)
        time.sleep(.1)
        Devices.tbx_api.write_bit(522, False)


if __name__ == '__main__':
    # main Tk App
    app = HMIApp()
    app.mainloop()
