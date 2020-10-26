#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyHMI.Canvas import HMICanvas
from pyHMI.Colors import *
from pyHMI.Dialog import ConfirmDialog, ValveOpenCloseDialog, ValveESDDialog
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag, tag_equal
import time
import tkinter as tk
from tkinter import ttk


class Devices(object):
    # init datasource
    # PLC TBox
    tbx = ModbusTCPDevice('163.111.181.85', port=502, timeout=2.0, refresh=1.0)
    # init modbus tables
    tbx.add_bits_table(3050, 80)
    tbx.add_bits_table(1536, 8)
    tbx.add_words_table(4000, 5)
    tbx.add_floats_table(5030, 16)
    # Aconcagua supervisor
    acon = ModbusTCPDevice('163.111.181.83', port=502, timeout=2.0, refresh=1.0)
    acon.add_words_table(12288, 2)
    acon.add_floats_table(12290, 24)
    # PSLS
    psls = ModbusTCPDevice('163.111.181.80', port=502, timeout=2.0, refresh=1.0)


class Tags(object):
    # tags list
    NULL_TAG = Tag(False)
    # Tbox PLC
    DEF_EDF = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3050})
    DEF_CHG = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3051})
    DEF_OND = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3052})
    DEF_ATD1 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3053})
    DEF_ATD2 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3054})
    DEF_FEU = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3055})
    DEF_CENT = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3056})
    TC_AUTO = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3057})
    TRA_EN_COURS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3058})
    CONF_NOP = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3059})
    CMD_PST_ACT = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3060})
    CONF_REG = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3061})
    CONF_NEU = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3062})
    CONF_SEC = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3063})
    PIL_TELE = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3064, 'not': True})
    PIL_LOCAL = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3064})
    V1130_EV_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3066})
    V1130_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3067})
    V1135_EV_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3068})
    V1135_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3069})
    V1136_EV_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3070})
    V1136_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3071})
    V1741_EV_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3072})
    V1130_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3074})
    V1130_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3075})
    V1133_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3076})
    V1133_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3077})
    V1134_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3078})
    V1134_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3079})
    V1135_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3080})
    V1135_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3081})
    V1136_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3082})
    V1136_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3083})
    V1137_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3084})
    V1137_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3085})
    V1138_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3086})
    V1138_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3087})
    VL_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3088})
    VL_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3089})
    V1740_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3090})
    V1740_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3091})
    MV7_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3092})
    MV7_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3093})
    MV7_DEF_ELEC = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3094})
    MV7_DIST = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3095})
    MV7_HS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3096})
    V1741_FDC_OUV = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3097})
    V1741_FDC_FER = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3098})
    DEF_SEQ_MV1130 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3099})
    DEF_SEQ_MV1135 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3100})
    DEF_SEQ_MV1136 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3101})
    SEQ_MV1130_EN_COURS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3102})
    SEQ_MV1135_EN_COURS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3103})
    SEQ_MV1136_EN_COURS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3104})
    DELTA_P_INF_1_5 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3105})
    DELTA_P_INF_0_5 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3106})
    V1741_PST_EN_COURS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3107})
    V1741_DEF_PST = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3108})
    DEF_DJ_TGBT = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3109})
    DEF_DJ_CC = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3110})
    DEF_ELEC_VL = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3111})
    REG_MARCHE = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3112})
    REG_ERR_CONS = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3113})
    REG_DEF_MES_P = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3114})
    REG_OUT_LIM_ON = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3115})
    REG_AUTO_D = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3116})
    REG_AUTO_L = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3117})
    REG_MANU = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3118})
    DEF_O2_1 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3119})
    DEF_O2_2 = Tag(False, src=Devices.tbx, ref={'type': 'bit', 'addr': 3120})
    TRA_REG_V_NEU = Tag(0, src=Devices.tbx, ref={'type': 'word', 'addr': 4000})
    TRA_REG_V_SEC = Tag(0, src=Devices.tbx, ref={'type': 'word', 'addr': 4001})
    TRA_NEU_V_REG = Tag(0, src=Devices.tbx, ref={'type': 'word', 'addr': 4002})
    TRA_NEU_V_SEC = Tag(0, src=Devices.tbx, ref={'type': 'word', 'addr': 4003})
    API_TBX_MDV = Tag(0, src=Devices.tbx, ref={'type': 'word', 'addr': 4004})
    P_GNY_DN900 = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5030})
    # P_GNY_DN800 = Tags(90.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5032})
    P_ARL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5034})
    # P_AV_VL = Tags(90.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5036})
    Q_ANTENNES = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5038})
    POS_VL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5040})
    POS_MV7 = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5042})
    P_CPTGE = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5044})
    P_AM_VL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5046})
    P_AV_VL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5048})
    REG_C_ACTIVE = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5050})
    REG_C_CSR = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5052})
    REG_M_P_AVAL = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5054})
    REG_LIM_OUV = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5056})
    REG_PID_P_OUT = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5058})
    REG_SORTIE = Tag(0.0, src=Devices.tbx, ref={'type': 'float', 'addr': 5060})
    # Aconcagua
    ACON_MDV = Tag(0, src=Devices.acon, ref={'type': 'word', 'addr': 12288})
    ACON_PCS = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12290})
    ACON_N2 = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12294})
    ACON_CO2 = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12296})
    ACON_DENS = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12316})
    ACON_PCS_ANC = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12324})
    ACON_THT = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12326})
    ACON_THT_ANC = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12328})
    ACON_H2O = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12330})
    ACON_H2O_ANC = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12332})
    ACON_P_HE = Tag(0.0, src=Devices.acon, ref={'type': 'float', 'addr': 12334})
    # virtual (a tag from tag(s))
    GET_TAG_TEST = Tag(False, get_cmd=lambda: Tags.V1130_FDC_FER.val and Tags.V1133_FDC_FER.val)
    REG_LOCAL = Tag(False, get_cmd=lambda: Tags.REG_AUTO_L.val or Tags.REG_MANU.val)
    REG_AUTO = Tag(False, get_cmd=lambda: Tags.REG_AUTO_D.val or Tags.REG_AUTO_L.val)
    REG_ARRET = Tag(False, get_cmd=lambda: tag_equal(Tags.REG_MARCHE, False))
    DELTA_P_VL = Tag(0, get_cmd=lambda: Tags.P_AM_VL.e_val - Tags.P_AV_VL.e_val)
    ECART_C_M = Tag(0, get_cmd=lambda: Tags.REG_C_ACTIVE.e_val - Tags.REG_M_P_AVAL.e_val)
    P_ANTENNES = Tag(0, get_cmd=lambda: Tags.P_CPTGE.e_val - 1.0)
    BTN_REG_MARCHE = Tag(False, get_cmd=lambda: Tags.REG_LOCAL.val and not Tags.REG_MARCHE.val)
    BTN_REG_ARRET = Tag(False, get_cmd=lambda: Tags.REG_LOCAL.val and not Tags.REG_ARRET.val)
    BTN_REG_TELE = Tag(False, get_cmd=lambda: Tags.REG_LOCAL.val)
    BTN_REG_LOCAL = Tag(False, get_cmd=lambda: not Tags.REG_LOCAL.val)
    BTN_REG_AUTO = Tag(False, get_cmd=lambda: Tags.REG_LOCAL.val and not Tags.REG_AUTO.val)
    BTN_REG_MANU = Tag(False, get_cmd=lambda: Tags.REG_LOCAL.val and not Tags.REG_MANU.val)
    BTN_REG_ACK = Tag(False, get_cmd=lambda: Tags.REG_LOCAL.val and Tags.REG_DEF_MES_P.val)
    BTN_NEUTRE = Tag(False, get_cmd=lambda: Tags.PIL_LOCAL.val and not Tags.CONF_NEU.val)
    BTN_REGION = Tag(False, get_cmd=lambda: Tags.PIL_LOCAL.val and not Tags.CONF_REG.val)
    TRA_NVR_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_NEU_V_REG, 1))
    TRA_RVN_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_NEU, 1))
    TRA_RVN_STEP_2 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_NEU, 2))
    TRA_RVN_STEP_3 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_NEU, 3))
    TRA_RVN_STEP_4 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_NEU, 4))
    TRA_RVN_STEP_5 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_NEU, 5))
    TRA_RVN_STEP_6 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_NEU, 6))
    TRA_NVS_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_NEU_V_SEC, 1))
    TRA_NVS_STEP_2 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_NEU_V_SEC, 2))
    TRA_RVS_STEP_1 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_SEC, 1))
    TRA_RVS_STEP_2 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_SEC, 2))
    TRA_RVS_STEP_3 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_SEC, 3))
    TRA_RVS_STEP_4 = Tag(0, get_cmd=lambda: tag_equal(Tags.TRA_REG_V_SEC, 4))
    # local (no external source)
    HMI_WORD = Tag(0)
    HMI_WORD2 = Tag(0)
    # WRITE TAGS
    # API
    # write bits
    CMD_V1130_OPEN = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6017})
    CMD_V1130_CLOSE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6018})
    CMD_V1135_OPEN = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6019})
    CMD_V1135_CLOSE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6020})
    CMD_V1136_OPEN = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6021})
    CMD_V1136_CLOSE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6022})
    CMD_V1741_CLOSE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6023})
    CMD_V1741_PST = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6025})
    CMD_CONF_REGION = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6026})
    CMD_CONF_NEUTRE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6027})
    CMD_REG_TELE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6029})
    CMD_REG_LOCAL = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6030})
    CMD_REG_MARCHE = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6031})
    CMD_REG_ARRET = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6032})
    CMD_REG_AUTO = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6033})
    CMD_REG_MANU = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6034})
    CMD_REG_ACK = Tag(False, src=Devices.tbx, ref={'type': 'w_bit', 'addr': 6035})
    # write floats
    REG_W_CONS_P = Tag(0.0, src=Devices.tbx, ref={'type': 'w_float', 'addr': 6100})
    REG_W_OUV_MAN = Tag(0.0, src=Devices.tbx, ref={'type': 'w_float', 'addr': 6102})

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


class TabInterco(HMITab):
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
        self.map_int.add_vbox('P_GNY_DN900', 230, 475, get_value=lambda: Tags.P_GNY_DN900, prefix='P', suffix='barg')
        self.map_int.add_vbox('P_GNY_DN800', 160, 300, get_value=lambda: Tags.P_AM_VL, prefix='P', suffix='barg')
        self.map_int.add_vbox('P_ARL', 640, 300, get_value=lambda: Tags.P_ARL, prefix='P', suffix='barg')
        self.map_int.add_vbox('P_AV_VL', 160, 80, get_value=lambda: Tags.P_AV_VL, prefix='P', suffix='barg')
        self.map_int.add_vbox('OUV_VL', 160, 190, get_value=lambda: Tags.REG_SORTIE, prefix='', suffix='%')
        self.map_int.add_vbox('Q_ANTENNES', 375, 50, get_value=lambda: Tags.Q_ANTENNES, prefix='Q', suffix='nm3/h',
                              tk_fmt='{:.0f}')
        self.map_int.add_vbox('P_ANTENNES', 500, 50, get_value=lambda: Tags.P_ANTENNES, prefix='P', suffix='barg')
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
        self.map_int.can.create_window(55, 170, window=self.frmConf)
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
        self.map_int.flow_valve.motor_pos_tag_anim('VL1', Tags.POS_VL)
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


class TabGnyDN900(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # tab "Gournay DN900"
        self.map_gny_dn900 = HMICanvas(self, width=800, height=550, debug=False)
        # add valves
        self.map_gny_dn900.add_m_valve('V1741', 300, 200, label='V1741', zoom=1, align='v')
        self.map_gny_dn900.add_s_valve('MV7', 500, 200, label='MV7', zoom=0.8, align='v')
        self.map_gny_dn900.add_s_valve('V1740', 600, 300, label='V1740', zoom=0.8)
        # add points
        self.map_gny_dn900.add_point('p2', 300, 300)
        self.map_gny_dn900.add_point('p3', 500, 300)
        # add buttons
        self.map_gny_dn900.add_button('EVENT', 500, 100, text='Event', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('GARE', 700, 300, text='Gare', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('GNY', 100, 300, text='Gournay DN900', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('ARL', 300, 100, text='Arleux DN800', state='disabled', disabledforeground=BLACK,
                                      borderwidth=0)
        self.map_gny_dn900.add_button('MANAGE_V1741', 220, 200, text='V1741',
                                      command=self.app.confirm_v1741, state='disabled')
        # add pipes
        self.map_gny_dn900.add_pipe('t1', from_name='GNY', to_name='p2')
        self.map_gny_dn900.add_pipe('t2', from_name='p2', to_name='p3')
        self.map_gny_dn900.add_pipe('t3', from_name='p3', to_name='V1740')
        self.map_gny_dn900.add_pipe('t4', from_name='p3', to_name='MV7')
        self.map_gny_dn900.add_pipe('t5', from_name='p2', to_name='V1741')
        self.map_gny_dn900.add_pipe('t6', from_name='MV7', to_name='EVENT')
        self.map_gny_dn900.add_pipe('t7', from_name='V1740', to_name='GARE')
        self.map_gny_dn900.add_pipe('t8', from_name='V1741', to_name='ARL')
        # add vbox
        self.map_gny_dn900.add_vbox('POS_MV7', 430, 200, get_value=lambda: Tags.POS_MV7, prefix='', suffix='%')

        # MV7 info panel
        self.frmMV7 = tk.Frame(self.map_gny_dn900.can)
        self.frmMV7.pack()
        self.mv7_list = HMIBoolList(self.frmMV7, head_str='Etat MV7', lbl_args={'width': 10})
        self.mv7_list.add('Distant', Tags.MV7_DIST)
        self.mv7_list.add('Hors-Service', Tags.MV7_HS)
        self.mv7_list.add('Défaut élec.', Tags.MV7_DEF_ELEC)
        self.mv7_list.build()
        self.map_gny_dn900.can.create_window(600, 160, window=self.frmMV7)
        # V1741 info panel
        self.frmV1741 = tk.Frame(self.map_gny_dn900.can, padx=0, pady=0)
        self.frmV1741.pack()
        self.v1741_list = HMIBoolList(self.frmV1741, head_str='Etat V1741', lbl_args={'width': 10})
        self.v1741_list.add('PST actif', Tags.V1741_PST_EN_COURS)
        self.v1741_list.add('Défaut PST', Tags.V1741_DEF_PST, alarm=True)
        self.v1741_list.build()
        self.map_gny_dn900.can.create_window(380, 150, window=self.frmV1741)
        # build panel
        self.map_gny_dn900.build()

    def tab_update(self):
        # update vbox
        self.map_gny_dn900.update_vbox()
        # update valves on canvas
        self.map_gny_dn900.motor_valve.tag_anim('V1741', Tags.V1741_FDC_OUV, Tags.V1741_FDC_FER)
        self.map_gny_dn900.motor_valve.motor_tag_anim('V1741', Tags.NULL_TAG, Tags.V1741_EV_FER)
        self.map_gny_dn900.simple_valve.tag_anim('MV7', Tags.MV7_FDC_OUV, Tags.MV7_FDC_FER)
        self.map_gny_dn900.simple_valve.tag_anim('V1740', Tags.V1740_FDC_OUV, Tags.V1740_FDC_FER)
        # validate command when local mode active
        if Tags.PIL_LOCAL.val:
            self.map_gny_dn900.d_widget['MANAGE_V1741']['obj'].configure(state='normal')
        else:
            self.map_gny_dn900.d_widget['MANAGE_V1741']['obj'].configure(state='disabled')
        # update MV7 info panel
        self.mv7_list.update()
        # update V1741 info panel
        self.v1741_list.update()


class TabReg(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Some vars
        self.manu_str = tk.StringVar(value='0.0')
        self.cons_p_str = tk.StringVar(value='0.0')
        # Etats régulateur
        self.frmEtatReg = tk.LabelFrame(self, text='Etats régulateur', padx=10, pady=10)
        self.frmEtatReg.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.etat_l = HMIBoolList(self.frmEtatReg, lbl_args={'width': 20}, grid_args={'padx': 20})
        self.etat_l.add('Marche', Tags.REG_MARCHE)
        self.etat_l.add('Arrêt', Tags.REG_ARRET)
        self.etat_l.add('Auto Distant', Tags.REG_AUTO_D)
        self.etat_l.add('Auto Local', Tags.REG_AUTO_L)
        self.etat_l.add('Manuel', Tags.REG_MANU)
        self.etat_l.add('Défaut mesure', Tags.REG_DEF_MES_P, alarm=True)
        self.etat_l.add('Erreur consigne', Tags.REG_ERR_CONS, alarm=True)
        self.etat_l.add('Limitation d\'ouverture', Tags.REG_OUT_LIM_ON, alarm=True)
        self.etat_l.build()
        # Consignes régulateur
        self.frmConsReg = tk.LabelFrame(self, text='Consignes régulateur', padx=10, pady=10)
        self.frmConsReg.grid(row=0, column=2, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.cons_r = HMIAnalogList(self.frmConsReg, lbl_args={'width': 10})
        self.cons_r.add('Consigne pression aval active', Tags.REG_C_ACTIVE, unit='barg', fmt='%0.2f')
        self.cons_r.add('Consigne pression aval CSR', Tags.REG_C_CSR, unit='barg', fmt='%0.2f')
        self.cons_r.build()
        # warning label
        self.lblWarn = tk.Label(self.frmConsReg, padx=5, font=('Arial', 9, 'bold'))
        self.lblWarn.place(relx=0.5, rely=0.9, anchor=tk.CENTER)
        # Mode automatique local
        self.frmAutoReg = tk.LabelFrame(self, text='Mode automatique local', padx=10, pady=10)
        self.frmAutoReg.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NSEW)
        tk.Label(self.frmAutoReg, text='Consigne pression').grid(row=0, column=0, padx=5, pady=5)
        self.ent_cons_p = tk.Entry(self.frmAutoReg, width='6', justify=tk.RIGHT, textvariable=self.cons_p_str)
        self.ent_cons_p.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.frmAutoReg, text='barg').grid(row=0, column=2, padx=5, pady=5)
        self.but_cons_p = tk.Button(self.frmAutoReg, text='Set', command=self.send_cons_p_value)
        self.but_cons_p.grid(row=0, column=3, padx=5, pady=5)
        # Mode manuel
        self.frmManuReg = tk.LabelFrame(self, text='Mode manuel', padx=10, pady=10)
        self.frmManuReg.grid(row=1, column=3, padx=5, pady=5, sticky=tk.NSEW)
        tk.Label(self.frmManuReg, text='Sortie').grid(row=0, column=0, padx=5, pady=5)
        self.ent_man = tk.Entry(self.frmManuReg, width='6', justify=tk.RIGHT, textvariable=self.manu_str)
        self.ent_man.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.frmManuReg, text='% ouv.').grid(row=0, column=2, padx=5, pady=5)
        self.but_man = tk.Button(self.frmManuReg, text='Set', command=self.send_man_value)
        self.but_man.grid(row=0, column=3, padx=5, pady=5)
        # Marche/arrêt régulation
        self.frmMarche = tk.LabelFrame(self, text='Marche/Arrêt régulation', padx=10, pady=10)
        self.frmMarche.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.marche_l = HMIButtonList(self.frmMarche, btn_args={'width': 15}, grid_args={'pady': 5})
        self.marche_l.add('En marche', tag_valid=Tags.BTN_REG_MARCHE, cmd=self.send_etat_marche)
        self.marche_l.add('À l\'arrêt', tag_valid=Tags.BTN_REG_ARRET, cmd=self.send_etat_arret)
        self.marche_l.build()
        # Lieu de pilotage
        self.frmPil = tk.LabelFrame(self, text='Lieu de pilotage régulation', padx=10, pady=10)
        self.frmPil.grid(row=3, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.pil_l = HMIButtonList(self.frmPil, btn_args={'width': 15}, grid_args={'pady': 5})
        self.pil_l.add('En distant', tag_valid=Tags.BTN_REG_TELE, cmd=self.send_pil_tele)
        self.pil_l.add('En local', tag_valid=Tags.BTN_REG_LOCAL, cmd=self.send_pil_local)
        self.pil_l.build()
        # Mesures régulateur
        self.frmMesReg = tk.LabelFrame(self, text='Mesures régulateur', padx=10, pady=10)
        self.frmMesReg.grid(row=2, column=2, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.mes_r = HMIAnalogList(self.frmMesReg, lbl_args={'width': 10})
        self.mes_r.add('Débit antennes', Tags.Q_ANTENNES, unit='nm3/h', fmt='%d')
        self.mes_r.add('Mesure pression', Tags.REG_M_P_AVAL, unit='barg', fmt='%0.2f')
        self.mes_r.add('Ecart consigne/mesure', Tags.ECART_C_M, unit='bar', fmt='%0.2f')
        self.mes_r.add('Delta P VL', Tags.DELTA_P_VL, unit='bar', fmt='%0.2f')
        self.mes_r.add('Vitesse ouv. max', Tags.REG_LIM_OUV, unit='% ouv./s', fmt='%0.2f')
        self.mes_r.add('PID pression', Tags.REG_PID_P_OUT, unit='% ouv.', fmt='%0.2f')
        self.mes_r.add('Sortie régulateur', Tags.REG_SORTIE, unit='% ouv.', fmt='%0.2f')
        self.mes_r.add('Retour position VL', Tags.POS_VL, unit='% ouv.', fmt='%0.2f')
        self.mes_r.build()
        # Choix des modes du régulateur
        self.frmModeReg = tk.LabelFrame(self, text='Choix du mode', padx=10, pady=10)
        self.frmModeReg.grid(row=2, column=3, padx=5, pady=5, sticky=tk.NSEW)
        self.mode_l = HMIButtonList(self.frmModeReg, btn_args={'width': 15}, grid_args={'pady': 5})
        self.mode_l.add('mode automatique', tag_valid=Tags.BTN_REG_AUTO, cmd=self.send_auto_mode)
        self.mode_l.add('mode manuel', tag_valid=Tags.BTN_REG_MANU, cmd=self.send_man_mode)
        self.mode_l.build()
        # Acquittement défaut mesure
        self.frmAckReg = tk.LabelFrame(self, text='Acquittement', padx=10, pady=10)
        self.frmAckReg.grid(row=3, column=3, padx=5, pady=5, sticky=tk.NSEW)
        self.ack_l = HMIButtonList(self.frmAckReg, btn_args={'width': 15}, grid_args={'pady': 5})
        self.ack_l.add('Acquit. déf. mesure', tag_valid=Tags.BTN_REG_ACK, cmd=self.send_ack)
        self.ack_l.build()
        # install callback
        self.manu_str.trace('w', self.manu_str_refresh)
        self.cons_p_str.trace('w', self.cons_p_str_refresh)

    def tab_update(self):
        # warning label
        if not abs(Tags.REG_C_ACTIVE.val - Tags.REG_C_CSR.val) <= 3.0:
            self.lblWarn['text'] = 'Attention: consignes CSR et active non alignées'
            self.lblWarn['bg'] = 'yellow1'
        else:
            self.lblWarn['text'] = ''
            self.lblWarn['bg'] = self.cget('bg')
        # refresh widget
        self.etat_l.update()
        self.cons_r.update()
        self.mes_r.update()
        self.marche_l.update()
        self.pil_l.update()
        self.mode_l.update()
        self.ack_l.update()
        # update manu entry
        self.manu_str_refresh()
        self.cons_p_str_refresh()

    def cons_p_str_refresh(self, *args):
        # update manu entry
        if Tags.REG_LOCAL.val:
            try:
                if not (0.0 <= float(self.cons_p_str.get()) <= 100.0):
                    raise ValueError
                if abs(Tags.REG_C_ACTIVE.val - float(self.cons_p_str.get())) < 1.0:
                    self.ent_cons_p.config(bg='white')
                else:
                    self.ent_cons_p.config(bg='yellow2')
                self.but_cons_p.configure(state='normal')
            except ValueError:
                self.ent_cons_p.config(bg='red')
                self.but_cons_p.configure(state='disabled')
        else:
            self.ent_cons_p.config(bg='white')
            self.but_cons_p.configure(state='disabled')
            self.cons_p_str.set('%.2f' % Tags.REG_C_ACTIVE.val)

    def send_cons_p_value(self):
        try:
            send_cons = float(self.cons_p_str.get())
            ConfirmDialog(self, title='Confirmation',
                          text='Envoi consigne pression %.2f barg ?' % send_cons,
                          valid_command=lambda: Tags.REG_W_CONS_P.set(send_cons))
            self.ent_cons_p.config(bg='white')
        except ValueError:
            self.ent_cons_p.config(bg='red')

    def manu_str_refresh(self, *args):
        # update manu entry
        if Tags.REG_MANU.val:
            try:
                if not (0.0 <= float(self.manu_str.get()) <= 100.0):
                    raise ValueError
                if abs(Tags.REG_SORTIE.val - float(self.manu_str.get())) < 1.0:
                    self.ent_man.config(bg='white')
                else:
                    self.ent_man.config(bg='yellow2')
                self.but_man.configure(state='normal')
            except ValueError:
                self.ent_man.config(bg='red')
                self.but_man.configure(state='disabled')
        else:
            self.ent_man.config(bg='white')
            self.but_man.configure(state='disabled')
            self.manu_str.set('%.2f' % Tags.REG_SORTIE.val)

    def send_man_value(self):
        try:
            send_cons = float(self.manu_str.get())
            ConfirmDialog(self, title='Confirmation',
                          text='Envoi ouverture VL à %.2f %% ?' % send_cons,
                          valid_command=lambda: Tags.REG_W_OUV_MAN.set(send_cons))
            self.ent_man.config(bg='white')
        except ValueError:
            self.ent_man.config(bg='red')

    def send_pil_tele(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Passage en pilotage distant du régulateur ?',
                      valid_command=lambda: Tags.CMD_REG_TELE.set(True))

    def send_pil_local(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Passage en pilotage local du régulateur ?',
                      valid_command=lambda: Tags.CMD_REG_LOCAL.set(True))

    def send_etat_marche(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Passage en marche du régulateur ?',
                      valid_command=lambda: Tags.CMD_REG_MARCHE.set(True))

    def send_etat_arret(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Passage à l\'arrêt du régulateur (arrêt = VL 100% ouverte) ?',
                      valid_command=lambda: Tags.CMD_REG_ARRET.set(True))

    def send_auto_mode(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Passage en mode automatique du régulateur ?',
                      valid_command=lambda: Tags.CMD_REG_AUTO.set(True))

    def send_man_mode(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Passage en mode manuel du régulateur ?',
                      valid_command=lambda: Tags.CMD_REG_MANU.set(True))

    def send_ack(self):
        ConfirmDialog(self, title='Confirmation',
                      text='Acquittement du défaut mesure ?',
                      valid_command=lambda: Tags.CMD_REG_ACK.set(True))


class TabInfo(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Energie
        self.frmEnergie = tk.LabelFrame(self, text='Energie', padx=10, pady=10)
        self.frmEnergie.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.energie_list = HMIBoolList(self.frmEnergie, lbl_args={'width': 18})
        self.energie_list.add('Absence EDF', Tags.DEF_EDF, alarm=True)
        self.energie_list.add('Défaut chargeur', Tags.DEF_CHG, alarm=True)
        self.energie_list.add('Défaut onduleur', Tags.DEF_OND, alarm=True)
        self.energie_list.add('Défaut disj. 62-TA-01', Tags.DEF_DJ_TGBT, alarm=True)
        self.energie_list.add('Défaut disj. 50-TA-01', Tags.DEF_DJ_CC, alarm=True)
        self.energie_list.build()
        # DI/DG
        self.frmCentrale = tk.LabelFrame(self, text='DI/DG', padx=10, pady=10)
        self.frmCentrale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.centrale_list = HMIBoolList(self.frmCentrale, lbl_args={'width': 14})
        self.centrale_list.add('Défaut centrale', Tags.DEF_CENT, alarm=True)
        self.centrale_list.add('ATD stade 1', Tags.DEF_ATD1, alarm=True)
        self.centrale_list.add('ATD stade 2', Tags.DEF_ATD2, alarm=True)
        self.centrale_list.add('O2 stade 1', Tags.DEF_O2_1, alarm=True)
        self.centrale_list.add('O2 stade 2', Tags.DEF_O2_2, alarm=True)
        self.centrale_list.add('Feu', Tags.DEF_FEU, alarm=True)
        self.centrale_list.build()
        # Pilotage
        self.lblPil = tk.LabelFrame(self, text='Pilotage', padx=10, pady=10)
        self.lblPil.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        self.pilotage_list = HMIBoolList(self.lblPil, lbl_args={'width': 10})
        self.pilotage_list.add('Distant', Tags.PIL_TELE)
        self.pilotage_list.add('Local', Tags.PIL_LOCAL)
        self.pilotage_list.add('TC Auto', Tags.TC_AUTO)
        self.pilotage_list.build()
        # Configuration
        self.lblConf = tk.LabelFrame(self, text='Configuration', padx=10, pady=10)
        self.lblConf.grid(row=0, column=3, padx=5, pady=5, sticky=tk.NSEW)
        self.conf_list = HMIBoolList(self.lblConf, lbl_args={'width': 10})
        self.conf_list.add('En Transition', Tags.TRA_EN_COURS)
        self.conf_list.add('Régional', Tags.CONF_REG)
        self.conf_list.add('Neutre', Tags.CONF_NEU)
        self.conf_list.add('Sécurité', Tags.CONF_SEC)
        self.conf_list.add('Non Op.', Tags.CONF_NOP)
        self.conf_list.build()
        # Transitions
        self.lblTrans = tk.LabelFrame(self, text='Transitions', padx=0, pady=10)
        self.lblTrans.grid(row=0, column=4, padx=5, pady=5, sticky=tk.NSEW)
        self.tran = HMIAnalogList(self.lblTrans)
        self.tran.add('Neutre vers régionale', Tags.TRA_NEU_V_REG, unit='niv')
        self.tran.add('Régionale vers neutre', Tags.TRA_REG_V_NEU, unit='niv')
        self.tran.add('Neutre vers sécurité', Tags.TRA_NEU_V_SEC, unit='niv')
        self.tran.add('Régionale vers sécurité', Tags.TRA_REG_V_SEC, unit='niv')
        self.tran.build()
        # Laboratoire
        self.frmLabo = tk.LabelFrame(self, text='Laboratoire', padx=5, pady=5)
        self.frmLabo.grid(row=1, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.labo_list = HMIAnalogList(self.frmLabo, lbl_args={'width': 10})
        self.labo_list.add('PCS', Tags.ACON_PCS, 'w/nm3', fmt='%0.0f')
        self.labo_list.add('Densité', Tags.ACON_DENS, fmt='%0.3f')
        self.labo_list.add('Azote', Tags.ACON_N2, '%', fmt='%0.2f')
        self.labo_list.add('CO2', Tags.ACON_CO2, '%', fmt='%0.2f')
        self.labo_list.add('PCS Ancienneté', Tags.ACON_PCS_ANC, 'min', fmt='%0.2f')
        self.labo_list.add('THT', Tags.ACON_THT, 'mg/nm3', fmt='%0.2f')
        self.labo_list.add('THT Ancienneté', Tags.ACON_THT_ANC, 'min', fmt='%0.2f')
        self.labo_list.add('Taux H2O', Tags.ACON_H2O, 'mg/nm3', fmt='%0.2f')
        self.labo_list.add('H2O Ancienneté', Tags.ACON_H2O_ANC, 'min', fmt='%0.2f')
        self.labo_list.add('P Hélium', Tags.ACON_P_HE, 'barg', fmt='%0.2f')
        self.labo_list.build()
        #  Poste
        self.frmPoste = tk.LabelFrame(self, text='Poste', padx=5, pady=5)
        self.frmPoste.grid(row=1, column=2, columnspan=3, padx=5, pady=5, sticky=tk.NSEW)
        self.poste_list = HMIAnalogList(self.frmPoste, lbl_args={'width': 10})
        self.poste_list.add('Q vers antennes régionales', Tags.Q_ANTENNES, 'nm3/h', fmt='%d')
        self.poste_list.add('P comptage (aval VL)', Tags.P_CPTGE, 'bara', fmt='%.02f')
        self.poste_list.add('P Gournay DN900 (amt V1741)', Tags.P_GNY_DN900, 'barg', fmt='%.02f')
        self.poste_list.add('P Arleux', Tags.P_ARL, 'barg', fmt='%.02f')
        self.poste_list.add('P amont VL', Tags.P_AM_VL, 'barg', fmt='%.02f')
        self.poste_list.add('P aval VL', Tags.P_AV_VL, 'barg', fmt='%.02f')
        self.poste_list.add('Position MV7', Tags.POS_MV7, '%', fmt='%.02f')
        self.poste_list.add('Position VL', Tags.POS_VL, '%', fmt='%.02f')
        self.poste_list.add('Sortie régulateur VL', Tags.REG_SORTIE, '%', fmt='%.02f')
        self.poste_list.add('Consigne active REG P aval', Tags.REG_C_ACTIVE, 'barg', fmt='%.02f')
        self.poste_list.add('Consigne CSR REG P aval', Tags.REG_C_CSR, 'barg', fmt='%.02f')
        self.poste_list.build()
        # Vannes
        self.frmValves = tk.LabelFrame(self, text='Vannes configuration', padx=5, pady=5)
        self.frmValves.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.NSEW)
        # V1130
        self.frmV1130 = tk.Frame(self.frmValves, padx=0, pady=0)
        self.frmV1130.grid(row=0, column=0, padx=6, pady=5, sticky=tk.NSEW)
        self.v1130_l = HMIBoolList(self.frmV1130, head_str='V1130', lbl_args={'width': 10})
        self.v1130_l.add('Ouv', Tags.V1130_FDC_OUV)
        self.v1130_l.add('Fer', Tags.V1130_FDC_FER)
        self.v1130_l.add('Def. seq.', Tags.DEF_SEQ_MV1130, alarm=True)
        self.v1130_l.add('Seq. act.', Tags.SEQ_MV1130_EN_COURS)
        self.v1130_l.build()
        # V1135
        self.frmV1135 = tk.Frame(self.frmValves, padx=0, pady=0)
        self.frmV1135.grid(row=0, column=1, padx=6, pady=5, sticky=tk.NSEW)
        self.v1135_l = HMIBoolList(self.frmV1135, head_str='V1135', lbl_args={'width': 10})
        self.v1135_l.add('Ouv', Tags.V1135_FDC_OUV)
        self.v1135_l.add('Fer', Tags.V1135_FDC_FER)
        self.v1135_l.add('Def. seq.', Tags.DEF_SEQ_MV1135, alarm=True)
        self.v1135_l.add('Seq. act.', Tags.SEQ_MV1135_EN_COURS)
        self.v1135_l.build()
        # V1136
        self.frmV1136 = tk.Frame(self.frmValves, padx=0, pady=0)
        self.frmV1136.grid(row=0, column=2, padx=6, pady=5, sticky=tk.NSEW)
        self.v1136_l = HMIBoolList(self.frmV1136, head_str='V1136', lbl_args={'width': 10})
        self.v1136_l.add('Ouv', Tags.V1136_FDC_OUV)
        self.v1136_l.add('Fer', Tags.V1136_FDC_FER)
        self.v1136_l.add('Def. seq.', Tags.DEF_SEQ_MV1136, alarm=True)
        self.v1136_l.add('Seq. act.', Tags.SEQ_MV1136_EN_COURS)
        self.v1136_l.build()
        # Vanne ESD
        self.frmESDValves = tk.LabelFrame(self, text='Vanne ESD', padx=5, pady=5)
        self.frmESDValves.grid(row=2, column=2, padx=5, pady=5, sticky=tk.NSEW)
        # V1741
        self.frmV1741 = tk.Frame(self.frmESDValves, padx=0, pady=0)
        self.frmV1741.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.v1741_l = HMIBoolList(self.frmV1741, head_str='V1741', lbl_args={'width': 10})
        self.v1741_l.add('Ouv', Tags.V1741_FDC_OUV)
        self.v1741_l.add('Fer', Tags.V1741_FDC_FER)
        self.v1741_l.add('PST actif', Tags.V1741_PST_EN_COURS)
        self.v1741_l.add('Déf. PST', Tags.V1741_DEF_PST, alarm=True)
        self.v1741_l.build()
        # Vanne régulation
        self.frmProcValve = tk.LabelFrame(self, text='Vanne régul.', padx=5, pady=5)
        self.frmProcValve.grid(row=2, column=3, padx=5, pady=5, sticky=tk.NSEW)
        # VL
        self.frmVL = tk.Frame(self.frmProcValve, padx=0, pady=0)
        self.frmVL.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.vl_l = HMIBoolList(self.frmVL, head_str='VL', lbl_args={'width': 10})
        self.vl_l.add('Ouv', Tags.VL_FDC_OUV)
        self.vl_l.add('Fer', Tags.VL_FDC_FER)
        self.vl_l.add('Déf. élec.', Tags.DEF_ELEC_VL, alarm=True)
        self.vl_l.build()
        # Système
        self.frmSys = tk.LabelFrame(self, text='Système', padx=5, pady=5)
        self.frmSys.grid(row=2, column=4, columnspan=1, padx=5, pady=5, sticky=tk.NSEW)
        self.sys_l = HMIAnalogList(self.frmSys, lbl_args={'width': 10})
        self.sys_l.add('Mot de vie API', Tags.API_TBX_MDV)
        self.sys_l.add('Mot de vie Acon.', Tags.ACON_MDV)
        self.sys_l.build()

    def tab_update(self):
        self.energie_list.update()
        self.centrale_list.update()
        self.pilotage_list.update()
        self.conf_list.update()
        self.tran.update()
        self.labo_list.update()
        self.poste_list.update()
        self.v1130_l.update()
        self.v1135_l.update()
        self.v1136_l.update()
        self.v1741_l.update()
        self.vl_l.update()
        self.sys_l.update()


class TabTran(HMITab):
    def __init__(self, notebook, update_ms=500, *args, **kwargs):
        HMITab.__init__(self, notebook, update_ms, *args, **kwargs)
        # Transitions
        self.lblTrans = tk.LabelFrame(self, text='Transitions', padx=0, pady=10)
        self.lblTrans.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.tran = HMIAnalogList(self.lblTrans)
        self.tran.add('Neutre vers régionale', Tags.TRA_NEU_V_REG, unit='niv')
        self.tran.add('Régionale vers neutre', Tags.TRA_REG_V_NEU, unit='niv')
        self.tran.add('Neutre vers sécurité', Tags.TRA_NEU_V_SEC, unit='niv')
        self.tran.add('Régionale vers sécurité', Tags.TRA_REG_V_SEC, unit='niv')
        self.tran.build()
        # Configuration
        self.lblConf = tk.LabelFrame(self, text='Configuration', padx=10, pady=10)
        self.lblConf.grid(row=1, column=0, padx=5, pady=5, sticky=tk.NSEW)
        self.conf_list = HMIBoolList(self.lblConf, lbl_args={'width': 20})
        self.conf_list.add('En Transition', Tags.TRA_EN_COURS)
        self.conf_list.add('Régional', Tags.CONF_REG)
        self.conf_list.add('Neutre', Tags.CONF_NEU)
        self.conf_list.add('Sécurité', Tags.CONF_SEC)
        self.conf_list.add('Non Op.', Tags.CONF_NOP)
        self.conf_list.build()
        # Lancement des transitions
        self.frmCmdTra = tk.LabelFrame(self, text='Commandes transitions', padx=10, pady=10)
        self.frmCmdTra.grid(row=2, column=0, rowspan=2, padx=5, pady=5, sticky=tk.NSEW)
        self.cmd_l = HMIButtonList(self.frmCmdTra, btn_args={'width': 10}, grid_args={'pady': 40})
        self.cmd_l.add('Vers régionale', tag_valid=Tags.BTN_REGION, cmd=self.app.confirm_region,
                       btn_args={'bg': GREEN})
        self.cmd_l.add('Vers neutre', tag_valid=Tags.BTN_NEUTRE, cmd=self.app.confirm_neutre,
                       btn_args={'bg': GREEN})
        self.cmd_l.build()
        # Neutre vers régionale
        self.frmCmdNVR = tk.LabelFrame(self, text='Neutre vers régionale', padx=10, pady=10)
        self.frmCmdNVR.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.nvr_list = HMIBoolList(self.frmCmdNVR, lbl_args={'width': 60})
        self.nvr_list.add('1. Fermeture vanne 1136', Tags.TRA_NVR_STEP_1)
        self.nvr_list.build()
        # Réginale vers neutre
        self.frmCmdRVN = tk.LabelFrame(self, text='Régionale vers neutre', padx=10, pady=10)
        self.frmCmdRVN.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.rvn_list = HMIBoolList(self.frmCmdRVN, lbl_args={'width': 60})
        self.rvn_list.add('1. Arrêt régulation (ouv. VL à 100% en pente douce)', Tags.TRA_RVN_STEP_1)
        self.rvn_list.add('2. Attente delta P VL < 1.5 bar', Tags.TRA_RVN_STEP_2)
        self.rvn_list.add('3. Ouverture V1135 (mise en bipasse comptage)', Tags.TRA_RVN_STEP_3)
        self.rvn_list.add('4. Attente delta P VL < 0.5 bar', Tags.TRA_RVN_STEP_4)
        self.rvn_list.add('5. Ouverture V1136', Tags.TRA_RVN_STEP_5)
        self.rvn_list.add('6. Fermeture V1135 (arrêt du bipasse comptage)', Tags.TRA_RVN_STEP_6)
        self.rvn_list.build()
        # Neutre vers sécurité
        self.frmCmdNVS = tk.LabelFrame(self, text='Neutre vers sécurité', padx=10, pady=10)
        self.frmCmdNVS.grid(row=2, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.nvs_list = HMIBoolList(self.frmCmdNVS, lbl_args={'width': 60})
        self.nvs_list.add('1. Ouverture V1135', Tags.TRA_NVS_STEP_1)
        self.nvs_list.add('2. Arrêt régulation (ouv. VL à 100% en pente douce)', Tags.TRA_NVS_STEP_2)
        self.nvs_list.build()
        # Régionale vers sécurité
        self.frmCmdRVS = tk.LabelFrame(self, text='Régionale vers sécurité', padx=10, pady=10)
        self.frmCmdRVS.grid(row=3, column=1, padx=5, pady=5, sticky=tk.NSEW)
        self.rvs_list = HMIBoolList(self.frmCmdRVS, lbl_args={'width': 60})
        self.rvs_list.add('1. Ouverture V1135', Tags.TRA_RVS_STEP_1)
        self.rvs_list.add('2. Arrêt régulation (ouv. VL à 100% en pente douce)', Tags.TRA_RVS_STEP_2)
        self.rvs_list.add('3. Attente delta P VL < 0.5 bar ou attente 3 min', Tags.TRA_RVS_STEP_3)
        self.rvs_list.add('4. Ouverture V1136', Tags.TRA_RVS_STEP_4)
        self.rvs_list.build()

    def tab_update(self):
        self.tran.update()
        self.cmd_l.update()
        self.conf_list.update()
        self.nvr_list.update()
        self.rvn_list.update()
        self.nvs_list.update()
        self.rvs_list.update()


class HMIToolbar(tk.Frame):
    def __init__(self, tk_app, update_ms=500, *args, **kwargs):
        tk.Frame.__init__(self, tk_app, *args, **kwargs)
        self.tk_app = tk_app
        self.update_ms = update_ms
        # build toolbar
        self.butTbox = tk.Button(self, text='API T-Box', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butTbox.pack(side=tk.LEFT)
        self.butAcon = tk.Button(self, text='Aconcagua', relief=tk.SUNKEN,
                                 state='disabled', disabledforeground='black')
        self.butAcon.pack(side=tk.LEFT)
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
        self.butTbox.configure(background=GREEN if Devices.tbx.connected else PINK)
        self.butAcon.configure(background=GREEN if Devices.acon.connected else PINK)
        self.lblDate.configure(text=time.strftime('%H:%M:%S %d/%m/%Y'))


class HMIApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # configure main window
        self.wm_title('Poste de Chilly')
        # self.attributes('-fullscreen', True)
        # self.geometry("800x600")
        # periodic tags update
        self.do_every(Tags.update_tags, every_ms=500)
        # build a notebook with tabs
        self.note = ttk.Notebook(self)
        self.tab_int = TabInterco(self.note)
        self.tab_gny_dn900 = TabGnyDN900(self.note)
        self.tab_reg = TabReg(self.note)
        self.tab_info = TabInfo(self.note)
        self.tab_tran = TabTran(self.note)
        self.note.add(self.tab_int, text='Interconnexion (F1)')
        self.note.add(self.tab_gny_dn900, text='Gournay DN900 (F2)')
        self.note.add(self.tab_reg, text='Régulation (F3)')
        self.note.add(self.tab_info, text='Informations (F4)')
        self.note.add(self.tab_tran, text='Transitions (F5)')
        self.note.pack(fill=tk.BOTH, expand=True)
        # defaut selected tab
        self.note.select(self.tab_int)
        # bind function keys to tabs
        self.bind('<F1>', lambda evt: self.note.select(self.tab_int))
        self.bind('<F2>', lambda evt: self.note.select(self.tab_gny_dn900))
        self.bind('<F3>', lambda evt: self.note.select(self.tab_reg))
        self.bind('<F4>', lambda evt: self.note.select(self.tab_info))
        self.bind('<F5>', lambda evt: self.note.select(self.tab_tran))
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
        Devices.tbx.write_bit(522, True)
        time.sleep(.1)
        Devices.tbx.write_bit(522, False)


if __name__ == '__main__':
    # main Tk App
    app = HMIApp()
    app.mainloop()
