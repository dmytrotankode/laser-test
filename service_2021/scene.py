"""Формат сцены: единственное, что связывает просмотрщик с остальными сервисами.

Просмотрщик НЕ знает про 5056, 3030 и что там дальше появится. Он умеет только
эту схему. Любой сервис складывает сюда файл - и его данные видно.

Всё в координатах станка (UFRAME 2) и в миллиметрах. Никаких своих систем
координат просмотрщик не заводит: если что-то нарисовалось не там, это значит,
что оно не там и есть, а не что визуализация подкрутила.

    cameras   где стоит камера, куда смотрит, какой фокус. rotation - вектор
              Родрига, мировая точка переводится как Xc = R (X - position),
              пиксель = focal * Xc[:2] / Xc[2] + размер/2. Ровно то соглашение,
              в котором посчитаны камеры (exp_camera_fit, L4_rays).
    curves    ломаные: линия реза, линия сгиба, что угодно.
    points    отдельные точки: лазерные пятна, маркерные метки.
    meshes    STL; transform - матрица 4x4, приводящая меш в координаты станка.

`image` у камеры - имя файла рядом со сценой, для режима "взгляд камерой".
"""
import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(BASE, 'data', 'scenes')


def camera(name, position, rotation, focal_px, size=(4096, 3000), image=None):
    return dict(name=name, position=[float(x) for x in position],
                rotation=[float(x) for x in rotation], focal_px=float(focal_px),
                size=[int(size[0]), int(size[1])], image=image)


def curve(name, points, color='#2563eb', closed=False, width=2,
          editable=False, ids=None):
    """`editable` - можно ли править точки по одной в 2021.

    `ids` - номер точки в шаблоне .LS (для сборки файла обратно после правки),
    по порядку, тот же индекс, что и в `points`. Обязателен, если editable.
    `points_original`/`touched` заполняются автоматически при editable=True:
    именно они хранят "что мы посчитали" отдельно от "что поправил оператор" -
    учиться потом можно только на touched, остальное не значит "верно".
    """
    out = dict(name=name, points=[[float(x) for x in p] for p in points],
               color=color, closed=bool(closed), width=width)
    if editable:
        if ids is None or len(ids) != len(points):
            raise ValueError('editable-кривой нужны ids той же длины, что points')
        out['editable'] = True
        out['ids'] = list(ids)
        out['points_original'] = [[float(x) for x in p] for p in points]
        out['touched'] = [False] * len(points)
    return out


def points(name, xyz, color='#f59e0b', size=4):
    return dict(name=name, points=[[float(x) for x in p] for p in xyz],
                color=color, size=size)


def placement_matrix(rot_deg=(0, 0, 0), translate=(0, 0, 0), scale=1.0):
    """Матрица 4x4 из читаемых чисел: X_станка = R (scale * X_меша) + translate.

    Порядок поворотов Rz*Ry*Rx. Держим меш в таком параметрическом виде, а не
    только матрицей, потому что руками крутят именно углы и сдвиги, а разбирать
    матрицу обратно на углы - лишний источник ошибок.
    """
    import math
    rx, ry, rz = (math.radians(a) for a in rot_deg)
    cx, sx, cy, sy, cz, sz = (math.cos(rx), math.sin(rx), math.cos(ry),
                              math.sin(ry), math.cos(rz), math.sin(rz))
    R = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
         [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
         [-sy, cy * sx, cy * cx]]
    T = [[R[i][j] * scale for j in range(3)] + [float(translate[i])] for i in range(3)]
    return T + [[0.0, 0.0, 0.0, 1.0]]


def mesh(name, url, rot_deg=(0, 0, 0), translate=(0, 0, 0), scale=1.0,
         color='#94a3b8', opacity=0.55, rim=None):
    """`rim` - собственная нижняя кромка меша в ЕГО координатах.

    Хранится в локальных координатах намеренно: положение модели правят руками,
    и кромка должна ехать вместе с ней, а не оставаться там, где была.
    """
    place = dict(rot_deg=[float(a) for a in rot_deg],
                 translate=[float(a) for a in translate], scale=float(scale))
    out = dict(name=name, url=url, placement=place,
               transform=placement_matrix(rot_deg, translate, scale),
               color=color, opacity=float(opacity))
    if rim is not None:
        out['rim'] = [[float(x) for x in p] for p in rim]
    return out


def write(name, cameras=(), curves=(), point_sets=(), meshes=(),
          frame='UFRAME2', note=''):
    """Сохранить сцену. Возвращает путь."""
    doc = dict(schema=1, frame=frame, note=note, units='mm',
               cameras=list(cameras), curves=list(curves),
               points=list(point_sets), meshes=list(meshes))
    os.makedirs(os.path.join(SCENES, name), exist_ok=True)
    p = os.path.join(SCENES, name, 'scene.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False)
    return p


def asset_dir(name):
    """Куда класть картинки и меши, на которые ссылается сцена."""
    d = os.path.join(SCENES, name)
    os.makedirs(d, exist_ok=True)
    return d
