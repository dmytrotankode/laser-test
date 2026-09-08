"""Доопрацьована КОПІЯ кореневого capture.py (сам він НЕ змінювався - лишається
незалежним діагностичним скриптом "чи живі камери", обговорено 2026-09-07).

Логіка отримання кадру (Hikvision MVS SDK: MV_CC_EnumDevices, TriggerMode/
TriggerSource, MV_CC_GetImageBuffer, декодування буфера) - СКОПІЙОВАНА без
змін з capture.py. Додано лише те, що потрібно для виклику з app.py:
    - --out / --result замість жорстко зашитих "./captures"
    - результат у result.json (машинночитаний), а не лише текст у консоль
    - код виходу 0, доки саме ОПИТУВАННЯ мережі не впало - НЕ падає через
      те, що знайшлось менше камер, ніж очікувалось (це вирішує app.py,
      який знає, скільки камер МАЄ бути і як звуть кожен ракурс)

MvImport (SDK-обгортка виробника) все ще має лежати поруч зі скриптом, як і
в оригіналі - у цьому репозиторії її немає (стоїть лише на машині оператора),
тому статус capture.py "по ідеї робочий, завтра перевірю" - саме про це.

Формат result.json:
    {"cameras": [{"index": 0, "serial": "...", "ok": true, "file": "cam_0_....png"}, ...],
     "error": null або текст фатальної помилки (мережу взагалі не опитати)}
"""
import argparse
import json
import os
import sys
from ctypes import cast, memmove, c_ubyte, POINTER

import numpy as np
import cv2

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE, 'MvImport'))


def write_result(result_path, result):
    os.makedirs(os.path.dirname(result_path) or '.', exist_ok=True)
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(BASE, 'captures'))
    ap.add_argument('--result', default=None)
    args = ap.parse_args()
    result_path = args.result or os.path.join(args.out, 'result.json')

    try:
        from MvCameraControl_class import (
            MvCamera, MV_CC_DEVICE_INFO_LIST, MV_GIGE_DEVICE, MV_CC_DEVICE_INFO,
            MV_ACCESS_Exclusive, MV_TRIGGER_MODE_ON, MV_TRIGGER_SOURCE_SOFTWARE,
            MV_FRAME_OUT,
        )
    except ImportError:
        write_result(result_path, {
            'cameras': [],
            'error': "Папку MvImport не знайдено поруч зі скриптом (service_2021/capture/MvImport) - "
                     "SDK камер не встановлено на цій машині."})
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)

    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)
    if ret != 0 or deviceList.nDeviceNum == 0:
        write_result(result_path, {
            'cameras': [],
            'error': f'Камери не знайдено в мережі. Код помилки: {hex(ret)}'})
        sys.exit(1)

    cameras = []
    for i in range(deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        gige_info = mvcc_dev_info.SpecialInfo.stGigEInfo
        serial_num = ''.join(chr(x) for x in gige_info.chSerialNumber if x != 0)
        entry = {'index': i, 'serial': serial_num, 'ok': False}
        cameras.append(entry)

        cam = MvCamera()
        ret = cam.MV_CC_CreateHandle(mvcc_dev_info)
        if ret != 0:
            entry['error'] = f'Не вдалося створити дескриптор (код {hex(ret)})'
            continue

        ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            entry['error'] = f'Камера зайнята або недоступна (код {hex(ret)})'
            cam.MV_CC_DestroyHandle()
            continue

        cam.MV_CC_SetEnumValue('TriggerMode', MV_TRIGGER_MODE_ON)
        cam.MV_CC_SetEnumValue('TriggerSource', MV_TRIGGER_SOURCE_SOFTWARE)

        ret = cam.MV_CC_StartGrabbing()
        if ret != 0:
            entry['error'] = f'Не вдалося почати захоплення (код {hex(ret)})'
            cam.MV_CC_CloseDevice()
            cam.MV_CC_DestroyHandle()
            continue

        cam.MV_CC_SetCommandValue('TriggerSoftware')
        stOutFrame = MV_FRAME_OUT()
        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 2000)
        if ret == 0:
            actual_data_size = stOutFrame.stFrameInfo.nFrameLen
            if actual_data_size > 0:
                pData = (c_ubyte * actual_data_size)()
                memmove(pData, stOutFrame.pBufAddr, actual_data_size)
                raw_bytes = np.frombuffer(pData, dtype=np.uint8)
                if actual_data_size == stOutFrame.stFrameInfo.nWidth * stOutFrame.stFrameInfo.nHeight:
                    img_np = raw_bytes.reshape(stOutFrame.stFrameInfo.nHeight, stOutFrame.stFrameInfo.nWidth)
                else:
                    img_np = cv2.imdecode(raw_bytes, cv2.IMREAD_GRAYSCALE)
                if img_np is not None:
                    filename = f'cam_{i}_{serial_num}.png'
                    cv2.imwrite(os.path.join(args.out, filename), img_np)
                    entry['ok'] = True
                    entry['file'] = filename
                else:
                    entry['error'] = 'Не вдалося декодувати кадр'
            else:
                entry['error'] = 'Порожній буфер кадру'
            cam.MV_CC_FreeImageBuffer(stOutFrame)
        else:
            entry['error'] = f'Не вдалося отримати кадр (код {hex(ret)})'

        cam.MV_CC_StopGrabbing()
        cam.MV_CC_CloseDevice()
        cam.MV_CC_DestroyHandle()

    write_result(result_path, {'cameras': cameras, 'error': None})
    sys.exit(0)


if __name__ == '__main__':
    main()
