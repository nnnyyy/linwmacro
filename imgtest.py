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

range = 901
val = 13

img2 = cv2.imread('./test2.png', cv2.IMREAD_COLOR)
check_moving = cv2.imread('./image/moving.png', cv2.IMREAD_GRAYSCALE)
img_mask = cv2.imread('./posion_mask.png', cv2.IMREAD_GRAYSCALE)
img_gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
mh, mw = img_mask.shape[:2] #로고파일 픽셀값 저장
ret, dst = cv2.threshold(img_gray2, 75, 255, cv2.THRESH_BINARY)
_, mv, _, _ = cv2.minMaxLoc(cv2.matchTemplate(dst, check_moving, cv2.TM_CCOEFF_NORMED))
"""
img2_cut = dst[862:862+mh, 851:851+mw]
img2_cut = cv2.bitwise_not(img2_cut)
mask_ret = cv2.bitwise_not( cv2.bitwise_or(img2_cut, img_mask) )
"""

# 851, 862 , 41 , 58 포션 마스킹
# dst[862:862+mh, 851:851+mw] = mask_ret



#cv2.imshow('binary', binary)
cv2.imshow('dst', dst)
cv2.waitKey(0)
cv2.destroyAllWindows()