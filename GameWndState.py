import win32api
import win32gui
import win32ui
import win32com.client
import win32con
import pyautogui
from ctypes import windll
import ctypes
_user32 = ctypes.WinDLL("user32")
import PIL.Image
from PIL import ImageTk
import time
import cv2
from enum import Enum
shell = win32com.client.Dispatch("WScript.Shell")
import logging
from slack import WebClient
import numpy as np
import tkinter
from tkinter import *
from tkinter import ttk
import clipboard

class GWState(Enum):
    NONE = -1,
    NORMAL = 0,
    RETURN_TO_VILL = 1,
    GO_BUY_POSION = 2,
    GO_HUNT = 3,    
    GO_HUNT_BY_FAVORATE = 4,
    GO_HUNT_BY_TARGET = 5,
    MOVE_TO_TARGET = 6,
    CHECK_MAIL = 7

"""
게임 윈도우 상태 관리 클래스    
"""
class GameWndState:
    from Tool import ToolDlg
    def __init__(self, hwnd, name, app:ToolDlg, idx):
        self.hwnd = hwnd
        self.name = name   
        self.idx = idx
        self.isPause = True   
        self.reserveState = GWState.NONE  
        self.loadImgs()
        self.tAutoHuntStart = time.time()
        self.tNoneAutoAttackAlertTime = 0
        self.tAttackedAlertMsg = 0
        self.app = app
        self.slackClient = WebClient(token=self.app.tbSlackToken.get())          
        self.setState(GWState.NORMAL)        
        
        self.cbvControlMode = tkinter.IntVar()
        
        self.initUI()
        
        # 설정 파일 값 불러오기
        self.reloadSetting()
        
    def __del__(self):                   
        pass
                
    def __str__(self):
        return f'{self.name} : {self.hwnd}'
    
    def destroyAll(self):
        self.frame.forget()
        
    def reloadSetting(self):
        name_split = self.name.split()
        self.setting = next((it for it in self.app.settings["list"] if it["name"] == name_split[-1]), None)        
        
        try:            
            if self.comboMapList is not None: self.comboMapList.set(self.setting["hunt_map"])
        except Exception as e:
            pass
    
    def initUI(self):        
        row_cnt = 5
        self.frame = tkinter.LabelFrame(self.app.frame_detail, text=self.name)        
        self.frame.grid(column=self.idx % row_cnt, row=int(self.idx / row_cnt))        
        
        self.uiCanvas = np.zeros((100,180,3), np.uint8)
        
        self.canvas = tkinter.Canvas(self.frame,width=180,height=100)
        self.canvas.pack()
        
        self.lbvHPMP = tkinter.StringVar()
        self.lbvHPMP.set("")
        tkinter.Label(self.frame, textvariable=self.lbvHPMP).pack(pady=1)
        
        self.btnFrame = tkinter.LabelFrame(self.frame, text="액션 버튼")
        self.btnFrame.pack(fill='both')
        Button(self.btnFrame, text="윈도우 찾기", command=self.setForeground).grid(row=0,column=0)
        Button(self.btnFrame, text="강제 귀환", command=self.forceReturn).grid(row=0,column=1)        
        Button(self.btnFrame, text="우편 확인", command=self.checkMail).grid(row=1,column=0)        
        Button(self.btnFrame, text="타겟 이동", command=self.moveToTarget).grid(row=1,column=1)
        
        self.tReturnToVillSometimes = time.time()        
        
        self.cbControlMode = Checkbutton(self.frame,text="컨트롤 모드",variable=self.cbvControlMode)
        self.cbControlMode.pack()
        
        self.btnFrame2 = tkinter.LabelFrame(self.frame, text="제어")
        self.btnFrame2.pack(fill='both')
        self.btnPause = Button(self.btnFrame2, text="일시정지", command=lambda: self.setPause(True))
        self.btnPause.grid(row=0, column=0)
        self.btnPause["state"] =  'disabled'
        
        self.btnResume = Button(self.btnFrame2, text="재기동", command=lambda: self.setPause(False))
        self.btnResume.grid(row=0, column=1)
        
        self.comboMapList = ttk.Combobox(self.frame, values=self.app.map_list, state="readonly")
        self.comboMapList.bind("<<ComboboxSelected>>", self.changeHuntMap)
        self.comboMapList.current(0)
        self.comboMapList.pack()
    
    def setPause(self, isPause):
        self.isPause = isPause        
        if isPause:
            self.btnPause["state"] = 'disabled'
            self.btnResume["state"] = 'normal'     
            self.app.listProcessActivated.delete(self.app.listProcessActivated.get(0,"end").index(self.name))
            self.app.listProcess.insert(0, self.name)
        else:
            self.btnPause["state"] = 'normal'
            self.btnResume["state"] = 'disabled'
            self.app.listProcess.delete(self.app.listProcess.get(0,"end").index(self.name))
            self.app.listProcessActivated.insert(0, self.name)
        
    def isPaused(self):
        return self.isPause
    
    def loadImgs(self):
        pass
        
    
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
        
    def forceReturn(self):
        self.returnToVillage()
        
    def resetState(self):
        self.setState(GWState.NORMAL)
        
    def setReserveState(self,_state:GWState):
        self.reserveState = _state
        
    def setState(self, _state:GWState) :
        self.state = _state
        self.tAction = time.time()
        if _state == GWState.GO_HUNT:
            self.goHuntCntEnd = 0

        s = self.getStateStr(_state)
        self.tReturnToVillSometimes = time.time()
            
    def getStateStr(self, _state:GWState) :
        if( _state == GWState.NORMAL ): return '일반'
        elif( _state == GWState.RETURN_TO_VILL ): return '마을귀환'
        elif( _state == GWState.GO_BUY_POSION ): return '물약구입'
        elif( _state == GWState.GO_HUNT ): return '사냥하러'
        elif( _state == GWState.GO_HUNT_BY_FAVORATE ): return '사냥하러(텔)'        
        
        return '-'
        
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
            self.img = cv2.cvtColor(np.array(im),  cv2.COLOR_RGB2BGR)
            return True
        else: return False
        
    def getImg(self,x,y,w,h):
        dx = x + w
        dy = y + h
        return self.img[y:dy,x:dx]
    
    def getUICanvas(self,x,y,w,h):
        dx = x + w
        dy = y + h
        return self.uiCanvas[y:dy,x:dx]
    
    def update(self):        
        if self.reserveState != GWState.NONE:
            self.state = self.reserveState
            self.reserveState = GWState.NONE
            
        if self.isPaused():
            return   
        
        self.updateHPMP(int(self.getHPPercent()), int(self.getMPPercent()))  
        
        isPowerSaveMenu = self.isMatching(self.img, self.app._imgPowerSaveMenu)
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
        elif self.state == GWState.GO_HUNT_BY_FAVORATE:
            self.checkGoHunt()
            return
        elif self.state == GWState.GO_HUNT_BY_TARGET:
            self.checkGoHunt()
            return
        elif self.state ==  GWState.MOVE_TO_TARGET:
            if self.isPowerSaveMode():
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.5)
                
            self.key_press(0xBD)
            self.goTarget()
            self.setState(GWState.GO_HUNT_BY_TARGET)
            return
        elif self.state == GWState.CHECK_MAIL:
            self.checkMail()
            self.setState(GWState.NORMAL)
            return
        
        # 절전모드와 관계없이 hp가 낮으면 귀환 우선 ( UI 모양이 절전모양과 같아서 체크 가능)
        if self.getHPPercent() <= 35:
            self.returnToVillage()  
            return

        # 절전모드가 아니면 절전모드 진입 후에 매크로 체크
        if self.isControlMode() != True and self.isPowerSaveMode() != True:
            self.goPowerSaveMode()
            self.app.tConcourse = time.time()
            return     
        
        if self.isControlMode() and self.isPowerSaveMode():
            self.key_press(win32con.VK_ESCAPE)
            return                          

        if self.isPowerSaveMode():
            self.processOnPowerSaveMode()
        else:
            self.processOnControlMode()
            
    def isPowerSaveMode(self):
        return self.isMatching(self.getImg(764,11,12,3), self.app._imgCheckSavePower) != True
    
    def useHealSelf(self):
        if self.isControlMode() and self.isElf() and self.getMPPercent() >= 15 and self.getHPPercent() <= 90:
            self.key_press(ord('2'))
            time.sleep(0.2)
            self.key_press(ord('2'))
            time.sleep(0.2)
            return True
        return False
    
    def useBloodToSoul(self):
        if self.isControlMode() and self.isElf() and self.getMPPercent() < 30 and self.getHPPercent() >= 60:
            self.key_press(ord('3'))
            time.sleep(0.2)
            return True
        else: return False
        
    def useTripleShot(self):
        if self.isControlMode() and self.isElf() and self.getMPPercent() >= 50 and self.getHPPercent() >= 50:
            self.key_press(ord('1'))
            time.sleep(0.2)
            return True
        return False
    
    def isElf(self):
        return True
        
    def isControlMode(self):
        return self.cbvControlMode.get() == 1
            
    def processOnPowerSaveMode(self):
        isAutoAttacking = self.isMatching(self.img[290:329,324:477], self.app._imgCheckAutoAttack)        
        isAttacked = self.isMatching(self.img[290:329,324:477], self.app._imgCheckAttacked)        
        isDigit1 = self.isMatching(self.img[413:417,364:369], self.app._imgCheck1Digit)

        if isAttacked:
            if self.sendAttackedAlertMsgDelay('공격 받고 있습니다!'):
                self.teleport()               
                self.uploadFile()

        isNoAttackByWeight = False
        isNoAttackByWeight = self.isMatching(self.img[420:430,410:445], self.app._imgCheckNoAttackByWeight)                        
        
        if isDigit1:
            # 한자리 이하의 물약 상태 - 특정 픽셀의 색으로 판별한다.  
            # 최후에는 OCR 로 판별하도록 작업한다
            self.returnToVillage()                
            return

        elif self.getHPPercent() <= 35:   
            self.returnToVillage()
            return
        elif isNoAttackByWeight:
            self.sendAlertMsgDelay('가방이 가득차서 공격할 수 없습니다.')  
            return

        if isAutoAttacking:                        
            pass          
        else:
            # 공격 중이 아닌 상태
            # 1. 일단 절전 모드를 끈다
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(1)
            # 2. 마을인지 확인
            if self.isOnVill():
                # 2-1. 마을 이라면 잡화 상점 프로세스부터 진행
                self.setState(GWState.RETURN_TO_VILL)                
            else:
                self.sendAlertMsgDelay('사냥 중이 아닙니다. 게임을 확인 해 주세요.')
                
    def processOnControlMode(self):
        if self.useHealSelf() == False:
            if self.useBloodToSoul() == False:
                self.useTripleShot()        
            
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
        
    def uploadFile(self):
        if self.slackClient is None: return
        
        try:        
            filePath = './screenshot.png'
            cv2.imwrite(filePath, self.img)
            self.slackClient.files_upload(channels=self.app.tbChannel.get(), file=filePath)
        except Exception as e:
            pass
        
    def isOnVill(self):
        return self.isMatching(self.img, self.app._imgCheckVill)     
    
    def goPowerSaveMode(self):
        self.key_press(ord('G'))
        time.sleep(0.5)
        
        self.click(400, 220)
        time.sleep(0.4)
    
    def returnToVillage(self):
        if self.isPowerSaveMode():
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(1)
        self.key_press(ord(self.app.tbShortcut.get().upper()))
        self.setState(GWState.RETURN_TO_VILL)
            
        
    def teleport(self):
        self.key_press(win32con.VK_ESCAPE)
        time.sleep(1)
        self.key_press(ord(self.app.tbShortcutTeleport.get().upper()))
        pass
        
    def key_press(self, vk_key):
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYDOWN, vk_key, 0)
        win32gui.SendMessage(self.hwnd, win32con.WM_KEYUP, vk_key, 0)
        
    def isMatching(self,src,temp,thhold=0.7):
        res = cv2.matchTemplate(src, temp, cv2.TM_CCOEFF_NORMED)                    
        _, maxv, _, max_loc = cv2.minMaxLoc(res)
        return maxv >= thhold
    
    def getMatchPos(self,src,temp):
        res = cv2.matchTemplate(src, temp, cv2.TM_CCOEFF_NORMED)                    
        _, _, _, max_loc = cv2.minMaxLoc(res)
        return max_loc
        
    def goBuyPosion(self, key):
        isCheckNoVill = self.isMatching(self.img, self.app._imgCheckVill)            
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
            if self.isMatching(self.img, self.app._imgCheckShopBtnWithMove):
                pos = self.getMatchPos(self.img, self.app._imgCheckShopBtnWithMove)
                self.click(pos[0] + 5,pos[1] + 5)
                logging.debug(f'{self} - 잡화상점으로 이동합니다')
                self.setState(GWState.GO_BUY_POSION)
            else:
                # 일단 다른 캐릭에게 처리 양보
                self.click(224,302)
                time.sleep(0.3)
            
        time.sleep(0.3)
            
    def checkInShop(self):
        if self.isMatching(self.getImg(358,61,80,32), self.app._checkShop):  
            logging.debug(f'{self} - 잡화상점')
            self.click(643,411)
            time.sleep(0.5)
            self.click(734,411)
            time.sleep(0.3)
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.3)
            
            if self.app.rbvMoveType.get() == 1:                
                self.goPyosik()            
                self.setState(GWState.GO_HUNT)
            elif self.app.rbvMoveType.get() == 2:
                self.goFavorate()            
                self.setState(GWState.GO_HUNT_BY_FAVORATE)
            else:
                self.goTarget()
                self.setState(GWState.GO_HUNT_BY_TARGET)
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
        if self.isMatching(self.img, self.app._checkAutoMoveBtn):
            _pos = self.getMatchPos(self.img, self.app._checkAutoMoveBtn)            
            self.click(_pos[0],_pos[1] + 5)
        else:
            self.click(31,372)
            time.sleep(1.5)
            self.screenshot()
            if self.isMatching(self.img, self.app._checkAutoMoveBtn):
                _pos = self.getMatchPos(self.img, self.app._checkAutoMoveBtn)
                self.click(_pos[0],_pos[1])
            else:
                logging.debug(f'{self} - 맵 이동 실패')
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.3)
                self.key_press(win32con.VK_ESCAPE)
                time.sleep(0.3)
                self.setState(GWState.NORMAL)
                return False
            
    def goFavorate(self):
        self.key_press(ord('M'))
        time.sleep(1.5)
        self.screenshot()
        if self.isMatching(self.img, self.app._imgFavorateBtn):
            _pos = self.getMatchPos(self.img, self.app._imgFavorateBtn)            
            self.click(_pos[0],_pos[1])
            time.sleep(0.8)
            self.screenshot()
            if self.isMatching(self.img, self.app._imgFavorateBtn2):
                _pos = self.getMatchPos(self.img, self.app._imgFavorateBtn2)            
                # 즐찾 클릭
                self.click(_pos[0] + 30,_pos[1] + 5)
                time.sleep(0.8)
                self.click(707,412)
                time.sleep(0.5)
                self.click(452,275)
    
    def goTarget(self):
        self.key_press(ord('M'))
        time.sleep(1.5)
        self.screenshot()
        if self.isMatching(self.img, self.app._imgMapSearch):
            _pos = self.getMatchPos(self.img, self.app._imgMapSearch )            
            self.click(_pos[0],_pos[1])
            time.sleep(0.5)
            self.pasteClipboard()            
        elif self.isMatching(self.img, self.app._imgMapHamberger):
            _pos = self.getMatchPos(self.img, self.app._imgMapHamberger )            
            self.click(_pos[0],_pos[1])
            time.sleep(0.5)
            self.click(_pos[0],_pos[1])
            time.sleep(0.5)
            self.pasteClipboard()
            
        self.click(74, 101)
        time.sleep(0.5)
        self.click(707,412)
        time.sleep(0.5)
        self.click(452,275)
        
    def reserveCheckMail(self):
        self.setReserveState(GWState.CHECK_MAIL)
        
    def checkMail(self):
        self.key_press(win32con.VK_ESCAPE)
        time.sleep(0.5)
        self.click(772,19) # 햄버거 메뉴 클릭
        time.sleep(0.2)
        self.click(734,244) # 우편 클릭
        time.sleep(0.2)
        self.click(457,412) # 모두 받기 클릭
        time.sleep(1)
        self.click(400,318) # 확인 버튼
        time.sleep(0.5)
        self.key_press(win32con.VK_ESCAPE)
        time.sleep(0.5)
        self.goPowerSaveMode()
        pass
    
    def moveToTarget(self):        
        self.setReserveState(GWState.MOVE_TO_TARGET)
        pass
    
    def pasteClipboard(self):
        clipboard.copy(self.comboMapList.get() + ' ')
        key = ord('V')
        lparam = win32api.MAKELONG(0,_user32.MapVirtualKeyA(key, 0))
        lparam_ctrl = win32api.MAKELONG(0,_user32.MapVirtualKeyA(win32con.VK_CONTROL, 0)) | 0x00000001
        
        time.sleep(0.1) # тестирования ради
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_CONTROL, lparam_ctrl)
        time.sleep(0.1)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key, lparam)
        time.sleep(0.1)
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, win32con.VK_BACK, lparam)
        time.sleep(0.5)
        
        pass
            
    def checkGoHunt(self):        
        if self.state == GWState.GO_HUNT:
            # 사냥 가는 길 체크가 어려움. 시간으로 체크한다
            # 고급 이미지 프로세싱 필요
            if (time.time() - self.tAction) >= 360:
                logging.debug(f'{self} - 자동 사냥 시작')
                self.tAutoHuntStart = time.time()
                self.key_press(0xBD)
                #self.click(736,257)
                self.setState(GWState.NORMAL)
            elif self.isMatching(self.img, self.app._checkmap):
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
        else:
            # 텔로 이동할 경우
            time.sleep(2)
            logging.debug(f'{self} - 자동 사냥 시작')
            self.tAutoHuntStart = time.time()
            self.key_press(0xBD)
            #self.click(736,257)
            self.setState(GWState.NORMAL)
            pass
            
    def concourse(self):
        isAutoAttacking = self.isMatching(self.img[290:329,324:477], self.app._imgCheckAutoAttack)
        if isAutoAttacking:
            self.key_press(win32con.VK_ESCAPE)
            time.sleep(0.8)
        
        self.goPyosik()
        self.setState(GWState.GO_HUNT)
        logging.debug(f'{self} - 모으기')
        
    def getHPPercent(self):
        img = cv2.cvtColor(np.array(self.img),  cv2.COLOR_RGB2BGR)
        img_hp = img[24:25,68:218]
        img_hp_gray = cv2.cvtColor(img_hp, cv2.COLOR_BGR2GRAY)
        ret, dst = cv2.threshold(img_hp_gray, 34, 255, cv2.THRESH_BINARY)    
        _arr = dst[0][::-1]
        _arr2 = np.where(_arr == 255)[0]
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
            
            if _cnt >= 7:
                _findidx = x - 6
                break 
        _rate = 100 - (_findidx / _arr.size) * 100
        return _rate
    
    def getMPPercent(self):
        img = cv2.cvtColor(np.array(self.img),  cv2.COLOR_RGB2BGR)
        img_hp = img[35:36,68:218]
        img_hp_gray = cv2.cvtColor(img_hp, cv2.COLOR_BGR2GRAY)
        ret, dst = cv2.threshold(img_hp_gray, 34, 255, cv2.THRESH_BINARY)    
        _arr = dst[0][::-1]
        _arr2 = np.where(_arr == 255)[0]
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
            
            if _cnt >= 7:
                _findidx = x - 6
                break 
        _rate = 100 - (_findidx / _arr.size) * 100
        return _rate
    
    def setHuntMap(self, map):
        self.comboMapList.set(map)
        
    def changeHuntMap(self,event):
        self.setting["hunt_map"] = self.comboMapList.get()
        self.app.saveSetting()
        pass
        
    def updateHPMP(self,hp,mp):
        self.lbvHPMP.set(f"hp:{hp}%, mp:{mp}%")     
        if self.isControlMode():                               
            sx = 0
            sy = 0
            self.uiCanvas[sy:sy+46,sx:sx+57] = self.getImg(9,5,57,46) # 캐릭 및 레벨 사진
            sx = 150
            sy = 48
            self.uiCanvas[sy:sy+31,sx:sx+26] = self.getImg(254,388,26,31) # 물약
            sx = 58
            sy = 3
            self.uiCanvas[sy:sy+14,sx:sx+57] = self.getImg(121,5,57,14) # 방어수치
            sx = 0
            sy = 60
            self.uiCanvas[sy:sy+17,sx:sx+114] = self.getImg(646,76,114,17) # 맵
            sx = 58
            sy = 20
            self.uiCanvas[sy:sy+17,sx:sx+121] = self.getImg(290,4,121,17) # 다이아 아덴
            sx = 58
            sy = 40
            self.uiCanvas[sy:sy+14,sx:sx+74] = self.getImg(22,430,74,14) # 경험치
            img = PIL.Image.fromarray(cv2.cvtColor(self.uiCanvas, cv2.COLOR_BGR2RGB))            
            self.imgtk =  ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0,0,image=self.imgtk,anchor=tkinter.NW) 
        else:                                
            sx = 0
            sy = 0
            self.uiCanvas[sy:sy+46,sx:sx+57] = self.getImg(9,5,57,46) # 캐릭 및 레벨 사진
            sx = 150
            sy = 48
            self.uiCanvas[sy:sy+31,sx:sx+26] = self.getImg(360,388,26,31) # 물약
            sx = 58
            sy = 3
            self.uiCanvas[sy:sy+14,sx:sx+57] = self.getImg(121,5,57,14) # 방어수치
            sx = 0
            sy = 60
            self.uiCanvas[sy:sy+17,sx:sx+114] = self.getImg(26,85,114,17) # 맵
            sx = 58
            sy = 20
            self.uiCanvas[sy:sy+17,sx:sx+121] = self.getImg(290,4,121,17) # 다이아 아덴
            sx = 58
            sy = 40
            self.uiCanvas[sy:sy+14,sx:sx+74] = self.getImg(22,430,74,14) # 경험치
            
            sx = 0
            sy = 79
            _tempImg = self.getImg(20,170,184,36) # 득템            
            self.uiCanvas[sy:sy+18,sx:sx+92] = cv2.resize(_tempImg, None, fx=0.5,fy=0.5 )
            img = PIL.Image.fromarray(cv2.cvtColor(self.uiCanvas, cv2.COLOR_BGR2RGB))            
            self.imgtk =  ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0,0,image=self.imgtk,anchor=tkinter.NW)
        
            