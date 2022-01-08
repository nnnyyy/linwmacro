import tkinter
import win32com.client
import threading
import requests

# Add this to __ini__
shell = win32com.client.Dispatch("WScript.Shell")
import psutil
import time
import numpy as np
import cv2
import os
import pyautogui
import win32gui
import win32ui
import win32con
import win32api
from ctypes import windll
import PIL.Image
from tkinter import *
from slack import WebClient
from GameWndState import GameWndState, GWState
import pytesseract

def _isAutoAttackingByNormalMode(img):
    x = 722
    y = 241
    w = 32
    h = 32
    dst = cv2.inRange(img[y:y+h,x:x+w], (50,70,160), (90,120,255))        
    _arr2 = np.where(dst == 255)[0]    
    cv2.imshow('dst', dst)
    cv2.moveWindow('dst', 0,480)  
    return _arr2.size > 0

def getPosionNum(dst, val, findIdx):
    ret = -1
    _additionalCheck = dst[1][findIdx - val - 1]
    _additionalCheck2 = dst[1][findIdx - val]
    
    print('add', val)
    print('add2', _additionalCheck)
    print('add3', _additionalCheck2)    
    return ret

def getMPPercent(img):
    img = cv2.cvtColor(np.array(img),  cv2.COLOR_RGB2BGR)
    img_hp = img[36:37,68:218]
    img_hp_gray = cv2.cvtColor(img_hp, cv2.COLOR_BGR2GRAY)
    ret, dst = cv2.threshold(img_hp_gray, 34, 255, cv2.THRESH_BINARY)    
    cv2.imshow('dst', dst)   
    _arr = dst[0][::-1]
    _arr2 = np.where(_arr == 255)[0]
    print(_arr2)
    _temp = -1
    _cnt = 0
    _findidx = _arr.size
    for x in _arr2:
        if _temp == -1:             
            _cnt = _cnt + 1
        elif (x - _temp) > 2:
            _cnt = 1            
        elif (x - _temp) <= 1:
            _cnt = _cnt + 1   
                    
        _temp = x
        
        if _cnt >= 13:
            _findidx = x - 12
            break 
    _rate = 100 - (_findidx / _arr.size) * 100
    return _rate

range = 901
val = 13

imgCheckHoldMove = cv2.imread('./image/checkHoldMove.png', cv2.IMREAD_COLOR)

"""
img2_cut = dst[862:862+mh, 851:851+mw]
img2_cut = cv2.bitwise_not(img2_cut)
mask_ret = cv2.bitwise_not( cv2.bitwise_or(img2_cut, img_mask) )
"""
# 851, 862 , 41 , 58 포션 마스킹
# dst[862:862+mh, 851:851+mw] = mask_ret

"""
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
config = ('-l kor')
print(pytesseract.image_to_string(dst, config=config).replace(' ', ''))
"""

# _imgCheckMP = cv2.imread('./image/checkmp.png', cv2.IMREAD_COLOR)
#_imgCheckHP = cv2.imread('./image/checkhp.png', cv2.IMREAD_COLOR)

toplist = []
lineage_window_list = []
def enum_callback(hwnd, results):
    results.append((hwnd, win32gui.GetWindowText(hwnd)))

win32gui.EnumWindows(enum_callback, toplist)
_wnds = [(_h, _t) for _h,_t in toplist if '리니지w l' in _t.lower() ]
for (_h, _t) in _wnds:    
    left, top, right, bot = win32gui.GetWindowRect(_h)
    w = right - left
    h = bot - top

    hwndDC = win32gui.GetWindowDC(_h)
    mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

    saveDC.SelectObject(saveBitMap)

    # Change the line below depending on whether you want the whole window
    # or just the client area. 
    #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
    result = windll.user32.PrintWindow(_h, saveDC.GetSafeHdc(), 3)

    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)

    im = PIL.Image.frombuffer(
        'RGB',
        (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
        bmpstr, 'raw', 'BGRX', 0, 1)

    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()        
    win32gui.ReleaseDC(_h, hwndDC)
    
    img = cv2.cvtColor(np.array(im),  cv2.COLOR_RGB2BGR)    
    img_posion = img[416:416 + 2,355:355 + 35]
    img_posion_gray = cv2.cvtColor(img_posion, cv2.COLOR_BGR2GRAY)
    ret, dst = cv2.threshold(img_posion_gray, 25, 255, cv2.THRESH_BINARY) 
    _arr = dst[0]
    _arr2 = np.where(_arr == 255)[0]
    
    print('-------')
    
    _temp = -1
    _val = 0
    _vallist = []
    _findidx = _arr.size
    for x in _arr2:
        if _temp == -1:
            _val = 1
        elif (x - _temp) <= 1:
            _val = _val + 1
        else:            
            _vallist.append(getPosionNum(dst, _val, x))
            _val = 1
            
        _temp = x  
        pass
        
    
    _vallist.append(getPosionNum(dst, _val, _temp))                 
    
    print('isAutoAttacking',_isAutoAttackingByNormalMode(img))
    cv2.imshow('img', img)  
    cv2.moveWindow('img', 0,0)      
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
cv2.destroyAllWindows()


# 355,416, 35, 1