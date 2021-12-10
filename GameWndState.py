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
import logging

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
    from Tool import ToolDlg
    def __init__(self, hwnd, name, app:ToolDlg):
        self.hwnd = hwnd
        self.name = name
        self.setState(GWState.NORMAL)
        self.loadImgs()
        self.tAutoHuntStart = time.time()
        self.tNoneAutoAttackAlertTime = 0
        self.tAttackedAlertMsg = 0
        self.app = app
                
    def __str__(self):
        return f'{self.name} : {self.hwnd}'
    
    def loadImgs(self):
        self._checkAutoMoveBtn = cv2.imread(PATH_CHECK_AUTO_MOVE_BTN, cv2.IMREAD_COLOR)
        self._checkShop = cv2.imread(PATH_CHECK_SHOP, cv2.IMREAD_COLOR)
        self._imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        self._imgCheckShopBtnWithMove = cv2.imread('./image/checkShopBtnWithMove.png', cv2.IMREAD_COLOR)   
        self._checkmap = cv2.imread(PATH_CHECK_WORLDMAP, cv2.IMREAD_COLOR) 
        self._imgCheckSavePower = cv2.imread('./image/checksavepower.png', cv2.IMREAD_COLOR)               
        self._imgPowerSaveMenu = cv2.imread('./image/powersavemenu.png', cv2.IMREAD_COLOR)   
        self._imgCheckAutoAttack = cv2.imread('./image/autoattack.png', cv2.IMREAD_COLOR)     
        
    
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
    
    def update(self):
        isPowerSaveMode = self.isMatching(self.getImg(764,11,12,3), self._imgCheckSavePower) != True
        isPowerSaveMenu = self.isMatching(self.img, self._imgPowerSaveMenu)
        if isPowerSaveMenu == True:
            self.key_press(win32con.VK_ESCAPE)
            return
            
        # 절전모드가 아닌 상태에서
        # 귀환 상태인지 체크 -> 마을인지 체크 -> 상점 물약 구매 -> 상점인지 체크 -> 자동 구매 -> 이동 -> 자동사냥 -> 모드 종료
        if self.state == GWState.RETURN_TO_VILL:
            self.goBuyPosion(self.app.tbShortcut.get())
            return
        elif self.state == GWState.GO_BUY_POSION:
            if self.checkInShop() == False:
                self.sendAlertMsgDelay('상점 이동에 실패 했습니다')                            
                pass
            return
        elif self.state == GWState.GO_HUNT:
            self.checkGoHunt()
            return

        # 절전모드가 아니면 절전모드 진입 후에 매크로 체크
        if isPowerSaveMode != True:
            self.goPowerSaveMode()
            self.app.tConcourse = time.time()
            return       

        if isPowerSaveMode:
            self.processOnPowerSaveMode() 
            
    def processOnPowerSaveMode(self):
        _imgCheck1Digit = cv2.imread('./image/check1digit.png', cv2.IMREAD_COLOR)
        _imgCheckHP = cv2.imread('./image/checkhp.png', cv2.IMREAD_COLOR)        
        _imgCheckNoAttackByWeight = cv2.imread('./image/checknoattackbyweight.png', cv2.IMREAD_COLOR)                
        _imgCheckAttacked = cv2.imread('./image/attacked.png', cv2.IMREAD_COLOR) 
        
        isAutoAttacking = self.isMatching(self.img[290:329,324:477], self._imgCheckAutoAttack)
        
        isAttacked = self.isMatching(self.img[290:329,324:477], _imgCheckAttacked)
        
        isDigit1 = self.isMatching(self.img[413:417,364:369], _imgCheck1Digit)

        if isAttacked:
            if self.sendAttackedAlertMsgDelay('공격 받고 있습니다!'):
                self.click(744, 396)                
                self.uploadFile('./screenshot.png')

        if isAutoAttacking:                        
            # print('HP OK')
            isHPOK = self.isMatching(self.img[24:31,68:110], _imgCheckHP) == False

            # print('Weight')
            isNoAttackByWeight = False
            isNoAttackByWeight = self.isMatching(self.img[420:430,410:445], _imgCheckNoAttackByWeight)                        
            
            if isDigit1:
                # 한자리 이하의 물약 상태 - 특정 픽셀의 색으로 판별한다.  
                self.returnToVillage(self.app.tbShortcut.get())                
                # self.post_message(_gw.name + ' : 물약을 보충하십시오.') 

            elif isHPOK == False:   
                self.returnToVillage(self.app.tbShortcut.get())
                # self.post_message(_gw.name + ' : HP가 부족합니다.')
            elif isNoAttackByWeight:
                self.sendAlertMsgDelay('가방이 가득차서 공격할 수 없습니다.')            
        else:
            self.returnToVillage(self.app.tbShortcut.get())
            
    def sendAlertMsgDelay(self, msg):
        tNonAttackTerm = int(self.app.tbNonAttack.get())
        _t = time.time() - self.tNoneAutoAttackAlertTime
        if _t >= tNonAttackTerm:            
            self.app.post_message(f'{self.name} : {msg}')
            self.tNoneAutoAttackAlertTime = time.time()
            return True
        else:
            return False
        
    def sendAttackedAlertMsgDelay(self, msg):
        tNonAttackTerm = 7
        _t = time.time() - self.tAttackedAlertMsg
        if _t >= tNonAttackTerm:            
            self.app.post_message(f'{self.name} : {msg}')
            self.tAttackedAlertMsg = time.time()
            return True
        else:
            return False

    def processOnNormalMode(self):
        _imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        isCheckNoVill = self.isMatching(self.img, _imgCheckVill)
        if isCheckNoVill:
            self.key_press(ord(self.app.tbShortcut.get().upper()))     
    
    def goPowerSaveMode(self):
        self.key_press(ord('G'))
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
        isCheckNoVill = self.isMatching(self.img, self._imgCheckVill)            
        if isCheckNoVill is False: 
            logging.debug(f'{self} - 마을이 아닙니다')
            self.key_press(ord(key.upper()))
            time.sleep(1.5)
        else:
            logging.debug(f'{self} - 마을입니다')
            self.click(709,315)
            time.sleep(0.5)
            self.click(496,227)
            time.sleep(1.5)                
            self.screenshot()
            if self.isMatching(self.img, self._imgCheckShopBtnWithMove):
                pos = self.getMatchPos(self.img, self._imgCheckShopBtnWithMove)
                self.click(pos[0] + 5,pos[1] + 5)
                logging.debug(f'{self} - 잡화상점으로 이동합니다')
                self.setState(GWState.GO_BUY_POSION)
            else:
                # 일단 다른 캐릭에게 처리 양보
                self.click(224,302)
                time.sleep(0.3)
            
        time.sleep(0.3)
            
    def checkInShop(self):
        if self.isMatching(self.getImg(358,61,80,32), self._checkShop):  
            logging.debug(f'{self} - 잡화상점')
            self.click(643,411)
            time.sleep(0.5)
            self.click(734,411)
            time.sleep(0.3)
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.3)
            self.goPyosik()
            
            self.setState(GWState.GO_HUNT)            
            return True
        else:
            if (time.time() - self.tAction) >= 100:
                logging.debug(f'{self} - 상점 이동 실패')
                self.setState(GWState.RETURN_TO_VILL)
                return False
            
            return True
        
        return True
    
    def goPyosik(self):        
        self.key_press(ord('M'))
        time.sleep(1.5)
        self.click(31,331)
        time.sleep(1)
        self.click(31,372)
        time.sleep(1)
        self.screenshot()
        if self.isMatching(self.img, self._checkAutoMoveBtn):
            _pos = self.getMatchPos(self.img, self._checkAutoMoveBtn)            
            self.click(_pos[0],_pos[1] + 5)
        else:
            self.click(31,372)
            time.sleep(1.5)
            self.screenshot()
            if self.isMatching(self.img, self._checkAutoMoveBtn):
                _pos = self.getMatchPos(self.img, self._checkAutoMoveBtn)
                self.click(_pos[0],_pos[1])
            else:
                logging.debug(f'{self} - 맵 이동 실패')
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.3)
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.3)
                self.setState(GWState.NORMAL)
                return False
            
    def checkGoHunt(self):        
        # 사냥 가는 길 체크가 어려움. 시간으로 체크한다
        # 고급 이미지 프로세싱 필요
        if (time.time() - self.tAction) >= 360:
            logging.debug(f'{self} - 자동 사냥 시작')
            self.tAutoHuntStart = time.time()
            self.key_press(0xBD)
            #self.click(736,257)
            self.setState(GWState.NORMAL)
        elif self.isMatching(self.img, self._checkmap):
            # 사냥 이동 중에 포커싱을 풀면 지도화면으로 자동 변환 된다. 풀어주자.
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.3)
        else:
            # 이진화 후 이동 시 깜빡 거리는 글씨를 체크 한다
            check_moving = cv2.imread('./image/moving.png', cv2.IMREAD_GRAYSCALE)
            gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
            ret, dst = cv2.threshold(gray, 74, 255, cv2.THRESH_BINARY)
            _, mv, _, _ = cv2.minMaxLoc(cv2.matchTemplate(dst, check_moving, cv2.TM_CCOEFF_NORMED))
            if mv >= 0.28:
                self.goHuntCntEnd = 0
            else:
                self.goHuntCntEnd = self.goHuntCntEnd + 1
        
        if self.goHuntCntEnd >= 7:
            logging.debug(f'{self} - 자동 사냥 시작')
            self.tAutoHuntStart = time.time()
            self.key_press(0xBD)
            #self.click(736,257)
            self.setState(GWState.NORMAL)
            
    def concourse(self):
        isAutoAttacking = self.isMatching(self.img[290:329,324:477], self._imgCheckAutoAttack)
        if isAutoAttacking:
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.8)
            self.goPyosik()
            self.setState(GWState.GO_HUNT)
            logging.debug(f'{self} - 모으기')