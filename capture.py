import os
import sys
import numpy as np
import cv2
from ctypes import *

sys.path.append("./MvImport")
try:
    from MvCameraControl_class import *
except ImportError:
    print("Помилка: Папку MvImport не знайдено поруч зі скриптом!")
    sys.exit()

SAVE_FOLDER = "./captures"

def main():
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    # 1. Робимо ОДИН стабільний пошук усіх камер у мережі
    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
    
    if ret != 0 or deviceList.nDeviceNum == 0:
        print(f"Камери не знайдено в мережі! Код помилки: {hex(ret)}")
        return

    total_cams = deviceList.nDeviceNum
    print(f"=== Запуск тесту заліза. Знайдено камер: {total_cams} ===")

    # 2. Перебираємо камери за фіксованими в списку посиланнями
    for i in range(total_cams):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        gige_info = mvcc_dev_info.SpecialInfo.stGigEInfo
        serial_num = "".join([chr(x) for x in gige_info.chSerialNumber if x != 0])
        
        print(f"\n>>> КРОК 1: Підключаємося до камери №{i} (SN: {serial_num})")
        
        cam = MvCamera()
        ret = cam.MV_CC_CreateHandle(mvcc_dev_info)
        if ret != 0:
            print(f"Не вдалося створити дескриптор для камери №{i}")
            continue

        ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print(f"Камера №{i} (SN: {serial_num}) зайнята. Код: {hex(ret)}")
            cam.MV_CC_DestroyHandle()
            continue

        cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_ON)
        cam.MV_CC_SetEnumValue("TriggerSource", MV_TRIGGER_SOURCE_SOFTWARE)

        ret = cam.MV_CC_StartGrabbing()
        if ret != 0:
            print(f"Не вдалося почати захоплення для камери №{i}")
            cam.MV_CC_CloseDevice()
            cam.MV_CC_DestroyHandle()
            continue

        print(f">>> КРОК 2: Надсилаємо тригер на камеру №{i}")
        cam.MV_CC_SetCommandValue("TriggerSoftware")
        
        stOutFrame = MV_FRAME_OUT()
        ret = cam.MV_CC_GetImageBuffer(stOutFrame, 2000)
        
        if ret == 0:
            print(f">>> КРОК 3: Кадр в буфері. Обробка даних ({stOutFrame.stFrameInfo.nWidth}x{stOutFrame.stFrameInfo.nHeight})...")
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
                    filename = f"{SAVE_FOLDER}/cam_{i}_{serial_num}.png"
                    cv2.imwrite(filename, img_np)
                    print(f">>> КРОК 4: Успішно збережено БЕЗ ВТРАТ: {filename}")
                else:
                    print("Помилка: Не вдалося декодувати масив байт.")
            else:
                print("Помилка: Порожній буфер.")
                
            cam.MV_CC_FreeImageBuffer(stOutFrame)
        else:
            print(f"Помилка отримання буфера: {hex(ret)}")

        print(f">>> КРОК 5: Звільняємо камеру №{i}")
        cam.MV_CC_StopGrabbing()
        cam.MV_CC_CloseDevice()
        cam.MV_CC_DestroyHandle()

    print("\n=== Тестування всіх камер завершено! ===")

if __name__ == "__main__":
    main()
