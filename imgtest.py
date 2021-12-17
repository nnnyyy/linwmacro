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

range = 901
val = 13

img = cv2.imread('./test_str.png', cv2.IMREAD_GRAYSCALE)
dst = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C | cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 301, 200)
"""
img2_cut = dst[862:862+mh, 851:851+mw]
img2_cut = cv2.bitwise_not(img2_cut)
mask_ret = cv2.bitwise_not( cv2.bitwise_or(img2_cut, img_mask) )
"""
# 851, 862 , 41 , 58 포션 마스킹
# dst[862:862+mh, 851:851+mw] = mask_ret

pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
config = ('-l kor')
print(pytesseract.image_to_string(dst, config=config).replace(' ', ''))

#cv2.imshow('binary', binary)
cv2.imshow('dst', dst)
cv2.waitKey(0)
cv2.destroyAllWindows()