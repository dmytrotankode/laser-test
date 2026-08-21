"""exp_all_methods.py на новых камерах (кольцо+пятна+маркеры, 20.08).

Не копия файла - подменяю только источник камер (`export_ls.cameras`) перед
вызовом оригинального `main()`. Сам exp_all_methods.py не тронут ни строкой,
способы 1-4 и вся дисциплина (TRAIN/CLEAN, мастер/чужие) - как есть.

top не участвует: с него не видна линия сгиба (line_features.py: VIEWS = (back,
left) - "на top линия сгиба не видна"), способы 3 и 4 в принципе не могут его
использовать, это не упущение здесь.

    python exp_all_methods_joint2.py
"""
import os
import json
import numpy as np

import exp_camera_fit as E
import export_ls as X
import exp_all_methods as M

BASE = os.path.dirname(os.path.abspath(__file__))


def cameras_joint2():
    foc = json.load(open(E.LASER_CAMS, encoding='utf-8'))
    return {w: (np.load(os.path.join(BASE, 'data', f'cam_{w}_joint2.npy')), foc[w]['focus'])
            for w in ('back', 'left')}


if __name__ == '__main__':
    X.cameras = cameras_joint2
    print('Камеры: cam_back_joint2.npy / cam_left_joint2.npy (кольцо+пятна+маркеры)\n')
    M.main()
