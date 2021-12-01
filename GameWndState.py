import win32gui
import win32ui
import win32com.client
import win32con
import pyautogui
from ctypes import windll
import PIL.Image
import time
import cv2
from enum import Enum
shell = win32com.client.Dispatch("WScript.Shell")

class GWState(Enum):
    NORMAL = 0,
    RETURN_TO_VILL = 1,
    GO_BUY_POSION = 2,
    GO_HUNT = 3,
    

"""
게임 윈도우 상태 관리 클래스    
"""
class GameWndState:
    def __init__(self, hwnd, name):
        self.hwnd = hwnd
        self.name = name
        self.state = GWState.NORMAL
        self.tAction = time.time()
                
    def __str__(self):
        return f'{self.name} : {self.hwnd}'
    
    def click(self, x, y):
        rect = win32gui.GetWindowRect(self.hwnd)
        xPos = rect[0]
        yPos = rect[1]
        xRatio = (rect[2] - rect[0]) / 800
        yRatio = (rect[3] - rect[1]) / 450
        x2 = int(xPos + (x * xRatio))
        y2 = int(yPos + (y * yRatio))
        self.setForeground()        
        (prevX,prevY) = pyautogui.position()
        pyautogui.moveTo(x2, y2)
        pyautogui.click()
        pyautogui.moveTo(prevX, prevY)        
        time.sleep(0.05)
        
    def setForeground(self):
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(self.hwnd)
        
    """
    스크린샷 - Minimize나 화면 잠금 상태가 아니면 스크린샷을 찍는다        
    """
    def screenshot(self):
        # Change the line below depending on whether you want the whole window
        # or just the client area. 
        #left, top, right, bot = win32gui.GetClientRect(hwnd)
        left, top, right, bot = win32gui.GetWindowRect(self.hwnd)
        w = right - left
        h = bot - top

        hwndDC = win32gui.GetWindowDC(self.hwnd)
        mfcDC  = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, w, h)

        saveDC.SelectObject(saveBitMap)

        # Change the line below depending on whether you want the whole window
        # or just the client area. 
        #result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 1)
        result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        im = PIL.Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()        
        win32gui.ReleaseDC(self.hwnd, hwndDC)

        if result == 1:
            #PrintWindow Succeeded
            im.save("screenshot.png")
            self.img = cv2.imread('screenshot.png', cv2.IMREAD_COLOR) 
            self.img = cv2.resize(self.img, dsize=(800,450))
            return True
        else: return False
        
    def getImg(self,x,y,w,h):
        dx = x + w
        dy = y + h
        return self.img[y:dy,x:dx]
    
    def returnToVillage(self, key):
        self.key_press(win32con.VK_ESCAPE)
        time.sleep(1)
        self.key_press(ord(key.upper()))
        self.state = GWState.RETURN_TO_VILL        
        
    def key_press(self, vk_key):
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, vk_key, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, vk_key, 0)
        
    def isMatching(self,src,temp,thhold=0.7):
        res = cv2.matchTemplate(src, temp, cv2.TM_CCOEFF_NORMED)                    
        _, maxv, _, _ = cv2.minMaxLoc(res)
        return maxv >= thhold
        
    def goBuyPosion(self, key):
        # 마을인지 체크하고 
        _imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        
        isFinded = False
        for _ in range(0,5):
            isCheckNoVill = self.isMatching(self.img, _imgCheckVill)            
            if isCheckNoVill: 
                self.key_press(ord(key.upper()))
                time.sleep(0.5)
                self.screenshot()
            else:                
                self.click(709,315)
                time.sleep(0.5)
                self.click(496,227)
                time.sleep(0.5)
                self.click(536,225)
                isFinded = True
                self.state = GWState.GO_BUY_POSION
                self.tAction = time.time()
                break
            
        time.sleep(0.3)
        
        if isFinded == False:
            self.state = GWState.NORMAL
            
    def checkInShop(self):
        _check = cv2.imread('./image/checkshop.png', cv2.IMREAD_COLOR)
        if self.isMatching(self.getImg(358,61,80,32), _check):  
            self.click(643,411)
            time.sleep(0.5)
            self.click(734,411)
            time.sleep(0.3)
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.3)
            self.key_press(ord('M'))
            time.sleep(1)
            self.click(31,331)
            time.sleep(0.6)
            self.click(31,372)
            time.sleep(0.6)
            self.click(478,224)
            self.state = GWState.GO_HUNT
            self.tAction = time.time()
            return True
        else:
            if (time.time() - self.tAction) >= 60:                
                self.state = GWState.NORMAL
                return False
            
            return True
        
        return True
            
    def checkGoHunt(self):
        # 사냥 가는 길 체크가 어려움. 시간으로 체크한다
        if (time.time() - self.tAction) >= 120:
            self.click(736,257)
            self.state = GWState.NORMAL 