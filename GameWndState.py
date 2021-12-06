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

PATH_CHECK_AUTO_MOVE_BTN = './image/checkautomovebtn.png'
PATH_CHECK_WORLDMAP = './image/checkworldmap.png'
PATH_CHECK_SHOP = './image/checkshop.png'

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
        self.setState(GWState.NORMAL)
        self.loadImgs()
        self.tAutoHuntStart = time.time()
                
    def __str__(self):
        return f'{self.name} : {self.hwnd}'
    
    def loadImgs(self):
        self._checkAutoMoveBtn = cv2.imread(PATH_CHECK_AUTO_MOVE_BTN, cv2.IMREAD_COLOR)
        self._checkShop = cv2.imread(PATH_CHECK_SHOP, cv2.IMREAD_COLOR)
        self._imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        self._imgCheckShopBtnWithMove = cv2.imread('./image/checkShopBtnWithMove.png', cv2.IMREAD_COLOR)   
        self._checkmap = cv2.imread(PATH_CHECK_WORLDMAP, cv2.IMREAD_COLOR)       
        
    
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
        
    def setState(self, _state:GWState) :
        self.state = _state
        self.tAction = time.time()    
        if _state == GWState.GO_HUNT:
            self.goHuntCntEnd = 0
        
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
    
    def goPowerSaveMode(self):
        self.key_press(self.hwnd, ord('G'))
        time.sleep(0.8)
        
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(self.hwnd)
        self.click(400, 220)
        time.sleep(0.8)
    
    def returnToVillage(self, key):
        self.key_press(win32con.VK_ESCAPE)
        time.sleep(1)
        self.key_press(ord(key.upper()))
        self.setState(GWState.RETURN_TO_VILL)
        
    def key_press(self, vk_key):
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, vk_key, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, vk_key, 0)
        
    def isMatching(self,src,temp,thhold=0.7):
        res = cv2.matchTemplate(src, temp, cv2.TM_CCOEFF_NORMED)                    
        _, maxv, _, _ = cv2.minMaxLoc(res)
        return maxv >= thhold
    
    def getMatchPos(self,src,temp):
        res = cv2.matchTemplate(src, temp, cv2.TM_CCOEFF_NORMED)                    
        _, _, _, max_loc = cv2.minMaxLoc(res)
        return max_loc
        
    def goBuyPosion(self, key):
        for _ in range(0,5):
            isCheckNoVill = self.isMatching(self.img, self._imgCheckVill)            
            if isCheckNoVill: 
                print(self, '마을이 아닙니다')
                self.key_press(ord(key.upper()))
                time.sleep(1.5)
                self.screenshot()
            else:
                print(self, '마을입니다')
                self.click(709,315)
                time.sleep(0.5)
                self.click(496,227)
                time.sleep(1.5)                
                self.screenshot()
                if self.isMatching(self.img, self._imgCheckShopBtnWithMove):
                    pos = self.getMatchPos(self.img, self._imgCheckShopBtnWithMove)
                    self.click(pos[0] + 5,pos[1] + 5)
                    print(self, '잡화상점으로 이동합니다')
                    self.setState(GWState.GO_BUY_POSION)
                else:
                    # 일단 다른 캐릭에게 처리 양보
                    self.click(224,302)
                    time.sleep(0.3)
                
                break
            
        time.sleep(0.3)
            
    def checkInShop(self):
        if self.isMatching(self.getImg(358,61,80,32), self._checkShop):  
            print(self, '잡화상점입니다')
            self.click(643,411)
            time.sleep(0.5)
            self.click(734,411)
            time.sleep(0.3)
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.3)
            print(self, '맵 이동 시작')
            self.goPyosik()
            
            self.setState(GWState.GO_HUNT)
            print(self, '사냥하러')
            return True
        else:
            if (time.time() - self.tAction) >= 80:
                # 60초 안에 상점에 도착하지 않으면 처음부터 다시 시도한다
                print(self, '상점 도착 실패')
                self.setState(GWState.RETURN_TO_VILL)
                return False
            
            return True
        
        return True
    
    def goPyosik(self):        
        self.key_press(ord('M'))
        time.sleep(1)
        self.click(31,331)
        time.sleep(0.6)
        self.click(31,372)
        time.sleep(1)
        self.screenshot()
        if self.isMatching(self.img, self._checkAutoMoveBtn):
            _pos = self.getMatchPos(self.img, self._checkAutoMoveBtn)
            print(_pos)
            self.click(_pos[0],_pos[1] + 5)
        else:
            self.click(31,372)
            time.sleep(1.5)
            self.screenshot()
            if self.isMatching(self.img, self._checkAutoMoveBtn):
                _pos = self.getMatchPos(self.img, self._checkAutoMoveBtn)
                self.click(_pos[0],_pos[1])
            else:
                print(self, '맵 이동 실패')
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.3)
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.3)
                self.setState(GWState.NORMAL)
                return False
            
    def checkGoHunt(self):        
        # 사냥 가는 길 체크가 어려움. 시간으로 체크한다
        # 고급 이미지 프로세싱 필요
        if (time.time() - self.tAction) >= 180:
            print(self, '자동 사냥 시작')
            self.tAutoHuntStart = time.time()
            self.key_press(0xBD)
            #self.click(736,257)
            self.setState(GWState.NORMAL)
        elif self.isMatching(self.img, self._checkmap):
            # 사냥 이동 중에 월드 맵 상태가 가끔 되는데 이유는 모르겠고 일단 풀어주자
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.3)
        else:
            # 이진화 후 이동 시 깜빡 거리는 글씨를 체크 한다
            check_moving = cv2.imread('./image/moving.png', cv2.IMREAD_GRAYSCALE)
            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            ret, dst = cv2.threshold(gray, 74, 255, cv2.THRESH_BINARY)
            _, mv, _, _ = cv2.minMaxLoc(cv2.matchTemplate(dst, check_moving, cv2.TM_CCOEFF_NORMED))
            if mv >= 0.28:
                print(self.name, '이동 중', mv, self.goHuntCntEnd)
                self.goHuntCntEnd = 0
            else:
                print(self.name, '이동 안하는 중', mv, self.goHuntCntEnd)
                self.goHuntCntEnd = self.goHuntCntEnd + 1
        
        if self.goHuntCntEnd >= 5:
            print(self, '자동 사냥 시작')
            self.tAutoHuntStart = time.time()
            self.key_press(0xBD)
            #self.click(736,257)
            self.setState(GWState.NORMAL)
            
            
# 상점 이동 탐색 범위            
# 440, 92, 164, 286
# checkShopBtnWithMove

