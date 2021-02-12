#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
import sys
from pyHMI.DS_ModbusTCP import ModbusTCPDevice
from pyHMI.Tag import Tag, TagsBank


# some class
class Devices:
    # init datasource
    # Floboss S600+ API table
    fbs_api = ModbusTCPDevice('163.111.182.153', port=502, unit_id=57, timeout=2.0, refresh=1.0,
                              client_adv_args=dict(debug=True))
    # modbus tables
    fbs_api.add_longs_table(6, 1, use_f4=False, swap_word=False)
    fbs_api.add_longs_table(34, 2, use_f4=False, swap_word=False)
    fbs_api.add_longs_table(78, 2, use_f4=False, swap_word=False)
    fbs_api.add_longs_table(122, 2, use_f4=False, swap_word=False)


class Tags(TagsBank):
    # Floboss S600+ PLC table
    MNE_API_FLOW_DIR = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'addr': 6})
    MNE_API_DP_S1_R1 = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'signed': True, 'addr': 34})
    MNE_API_DP_S2_R1 = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'signed': True, 'addr': 36})
    MNE_API_DP_S1_R2 = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'signed': True, 'addr': 78})
    MNE_API_DP_S2_R2 = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'signed': True, 'addr': 80})
    MNE_API_DP_S1_R3 = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'signed': True, 'addr': 122})
    MNE_API_DP_S2_R3 = Tag(0, src=Devices.fbs_api, ref={'type': 'long', 'signed': True, 'addr': 124})


if __name__ == '__main__':
    # wait modbus thread startup
    time.sleep(1.0)
    # main loop
    while True:
        # for every items in Tags class
        tag_l = list()
        for (tag_name, tag) in Tags.items():
            if not tag.err:
                tag_l.append((tag_name, tag.val))
        # if list is not empty, send to recorder API http endpoint
        if tag_l:
            try:
                r = requests.post('http://localhost:5000/api/set_tag_list', json=tag_l)
                # print(r.status_code, r.text.strip())
            except Exception as e:
                print(e, file=sys.stderr)
        # wait for next update
        time.sleep(10.0)
