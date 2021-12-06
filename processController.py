import threading
import requests
import pyautogui
import win32gui
import win32con
import win32api
from ctypes import windll
import psutil
import time
import cv2
import numpy as np
import win32com.client
# Add this to __ini__
shell = win32com.client.Dispatch("WScript.Shell")
from tkinter import *

from slack import WebClient
from GameWndState import GameWndState, GWState
import logging

class ProcessController(object):
    from Tool import ToolDlg
    def __init__(self, app:ToolDlg):        
        self.thread = None
        self.stop_threads = threading.Event()
        self.dNoneAutoAttackAlertTime = dict()
        self.dAttackedAlertTime = dict()        
        self.lineage_window_list = [] 
        self.slackClient = None        
        self.app = app        
        logging.debug(f'컨트롤러 생성')
    
    def refreshWnds(self):
        toplist = []
        self.lineage_window_list = []
        def enum_callback(hwnd, results):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_callback, toplist)
        _wnds = [(_h, _t) for _h,_t in toplist if '리니지w l' in _t.lower() ]
        for (_h, _t) in _wnds:
            gw = GameWndState(_h, _t)
            self.lineage_window_list.append(gw)            
        
        self.lineage_window_list.sort(key=lambda _gw: _gw.name, reverse=True)
                
    
    def findWnd(self):
        # 윈도우 리셋                
        self.app.listProcess.delete(0, END)
        self.app.listProcessActivated.delete(0, END)
        self.refreshWnds()        

        cnt = 0
        for _gw in self.lineage_window_list:
            self.app.listProcess.insert(cnt, _gw.name)
            cnt += 1

    def arragngeWnd(self):    
        self.refreshWnds()

        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        x_init = 60
        x = x_init
        y = 60
        dx = 50
        dy = 45            
        game_width = 800
        game_height = 450

        for _gw in self.lineage_window_list:              
            win32gui.MoveWindow(_gw.hwnd, x, y, game_width, game_height, True)             
            x += 100
            y += 50  
            self.setForegroundWnd(_gw.hwnd)    
            time.sleep(0.1) 
            
    def arragngeWndSelected(self):
        toplist = []
        def enum_callback(hwnd, results):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_callback, toplist)
        _list_selected = []
        _list = [(_h, _t) for _h,_t in toplist if '리니지w l' in _t.lower() ]        
        for (_h,_t) in _list:
            for _idx  in self.app.listProcess.curselection():
                _t_selected = self.app.listProcess.get(_idx)
                if _t == _t_selected: _list_selected.append((_h,_t))
                
            for _idx  in self.app.listProcessActivated.curselection():
                _t_selected = self.app.listProcessActivated.get(_idx)
                if _t == _t_selected: _list_selected.append((_h,_t))
        
        _list_selected.sort(key=lambda x:x[1])        

        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        x_init = 60
        x = x_init
        y = 60
        dx = 50
        dy = 45            
        game_width = 800
        game_height = 450

        for (lw_hwnd, lw_title) in _list_selected:   
            if (x + game_width) > screen_width:
                x = x_init
                y += (game_height + dy)
            win32gui.MoveWindow(lw_hwnd, x, y, game_width, game_height, True)
            x += (game_width + dx)               
                
            if (y + game_height + dy) > screen_height:
                x = x_init
                y = 90
                
            self.setForegroundWnd(lw_hwnd)    
            time.sleep(0.1)      

    def sendAlertMsgDelay(self, wnd, msg):
        tNonAttackTerm = int(self.app.tbNonAttack.get())
        if wnd not in self.dNoneAutoAttackAlertTime: 
            self.post_message(wnd + ' : ' + msg)
            self.dNoneAutoAttackAlertTime[wnd] = time.time()
            return True
        else:
            _t = time.time() - self.dNoneAutoAttackAlertTime[wnd]
            if _t >= tNonAttackTerm: 
                self.post_message(wnd + ' : ' + msg)
                self.dNoneAutoAttackAlertTime[wnd] = time.time()
                return True
            return False
        
    def sendAttackedAlertMsgDelay(self, wnd, msg):
        tNonAttackTerm = 7
        if wnd not in self.dAttackedAlertTime: 
            self.post_message(wnd + ' : ' + msg)
            self.dAttackedAlertTime[wnd] = time.time()
            return True
        else:
            _t = time.time() - self.dAttackedAlertTime[wnd]
            if _t >= tNonAttackTerm: 
                self.post_message(wnd + ' : ' + msg)
                self.dAttackedAlertTime[wnd] = time.time()
                return True
            return False

    def setForegroundWndByDoubleClick(self, event):
        for i in self.app.listProcess.curselection():
            hwnd = win32gui.FindWindow(None, self.app.listProcess.get(i))
            self.setForegroundWnd(hwnd)

        for i in self.app.listProcessActivated.curselection():
            hwnd = win32gui.FindWindow(None, self.app.listProcessActivated.get(i))
            self.setForegroundWnd(hwnd)

    def setForegroundWnd(self, hwnd):
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(hwnd)
        
    def uploadFile(self, filePath):
        if self.slackClient is None: return
        
        self.slackClient.files_upload(channels=self.app.tbChannel.get(), file=filePath)

    def onProcInThread(self, type=1):             
        self.app.lbState.set("매크로 실행 중")   
        
        self.slackClient = WebClient(token=self.app.tbSlackToken.get())  
        loopTerm = int(self.app.tbLoopTerm.get())
        
        _imgCheckSavePower = cv2.imread('./image/checksavepower.png', cv2.IMREAD_COLOR)               
        _imgPowerSaveMenu = cv2.imread('./image/powersavemenu.png', cv2.IMREAD_COLOR)  

        while not self.stop_threads.is_set():   
            _gw: GameWndState   
            for _gw in self.lineage_window_list:
                lw_hwnd = _gw.hwnd
                lw_title = _gw.name
                try:         
                    activatedWndList = np.array(self.app.listProcessActivated.get(0,END))        
                    if np.size(np.where(activatedWndList == lw_title)) <= 0:                         
                        continue;                    
                    
                    
                    win32gui.ShowWindow(lw_hwnd, win32con.SW_NORMAL) 
                    if _gw.screenshot() == False:
                        logging.error(f'{_gw} screenshot failed..')
                        
                        continue                    
                
                    isPowerSaveMode = _gw.isMatching(_gw.getImg(764,11,12,3), _imgCheckSavePower) != True
                    isPowerSaveMenu = _gw.isMatching(_gw.img, _imgPowerSaveMenu)
                    if isPowerSaveMenu == True:
                        self.key_press(lw_hwnd, win32con.VK_ESCAPE)
                        continue
                        
                    # 절전모드가 아닌 상태에서
                    # 귀환 상태인지 체크 -> 마을인지 체크 -> 상점 물약 구매 -> 상점인지 체크 -> 자동 구매 -> 이동 -> 자동사냥 -> 모드 종료
                    if _gw.state == GWState.RETURN_TO_VILL:
                        _gw.goBuyPosion(self.app.tbShortcut.get())
                        continue
                    elif _gw.state == GWState.GO_BUY_POSION:
                        if _gw.checkInShop() == False:
                            self.sendAlertMsgDelay(_gw.name, '상점 이동에 실패 했습니다')                            
                        continue
                    elif _gw.state == GWState.GO_HUNT:
                        _gw.checkGoHunt()
                        continue

                    # 절전모드가 아니면 절전모드 진입 후에 매크로 체크
                    if isPowerSaveMode != True:
                        self.goSavePower(_gw) 
                        continue                    

                    if isPowerSaveMode:
                        self.processOnPowerSaveMode(_gw)
                    else:
                        self.processOnNormalMode(_gw)
                    
                except Exception as e:
                    logging.error(f'{lw_title} -  {e}')
                    # self.post_message(token, '#lineage_alert', 'error:' + e + ' ' + lw_title)
            
            time.sleep(loopTerm)

    def processOnPowerSaveMode(self, _gw:GameWndState):
        _imgCheck1Digit = cv2.imread('./image/check1digit.png', cv2.IMREAD_COLOR)
        _imgCheckHP = cv2.imread('./image/checkhp.png', cv2.IMREAD_COLOR)        
        _imgCheckNoAttackByWeight = cv2.imread('./image/checknoattackbyweight.png', cv2.IMREAD_COLOR)
        _imgCheckAutoAttack = cv2.imread('./image/autoattack.png', cv2.IMREAD_COLOR)        
        _imgCheckAttacked = cv2.imread('./image/attacked.png', cv2.IMREAD_COLOR) 
        
        isAutoAttacking = _gw.isMatching(_gw.img[290:329,324:477], _imgCheckAutoAttack)
        
        isAttacked = _gw.isMatching(_gw.img[290:329,324:477], _imgCheckAttacked)
        
        isDigit1 = _gw.isMatching(_gw.img[413:417,364:369], _imgCheck1Digit)

        if isAttacked:
            if self.sendAttackedAlertMsgDelay(_gw.name, '공격 받고 있습니다!'):
                _gw.click(744, 396)                
                self.uploadFile('./screenshot.png')

        if isAutoAttacking:                        
            # print('HP OK')
            isHPOK = _gw.isMatching(_gw.img[24:31,68:110], _imgCheckHP) == False

            # print('Weight')
            isNoAttackByWeight = False
            isNoAttackByWeight = _gw.isMatching(_gw.img[420:430,410:445], _imgCheckNoAttackByWeight)                        
            
            if isDigit1:
                # 한자리 이하의 물약 상태 - 특정 픽셀의 색으로 판별한다.  
                _gw.returnToVillage(self.app.tbShortcut.get())                
                # self.post_message(_gw.name + ' : 물약을 보충하십시오.') 

            elif isHPOK == False:   
                _gw.returnToVillage(self.app.tbShortcut.get())
                # self.post_message(_gw.name + ' : HP가 부족합니다.')
            elif isNoAttackByWeight:
                self.sendAlertMsgDelay(_gw.name, '가방이 가득차서 공격할 수 없습니다.')
        else:
            self.sendAlertMsgDelay(_gw.name, '대기 중입니다.')

    def processOnNormalMode(self, _gw:GameWndState):
        _imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        isCheckNoVill = self.isMatching(_gw.img, _imgCheckVill)
        if isCheckNoVill:
            self.key_press(_gw.img, ord(self.app.tbShortcut.get().upper()))    

    def start(self, type=1):
        self.stop_threads.clear()
        self.thread = threading.Thread(target = self.onProcInThread, args=(type,))
        self.thread.start()
        self.app.btnSortWnd1["state"] = 'disabled'
        self.app.btnSortWnd3["state"] = "normal"
        self.app.tbShortcut["state"] = 'disabled'
        self.app.tbLoopTerm["state"] = 'disabled'
        self.app.tbNonAttack["state"] = 'disabled'
        self.app.tbSlackToken["state"] = 'disabled'
        self.app.tbChannel["state"] = 'disabled'
        self.app.checkReturnToVillBtn["state"] = 'disabled'

    def goSavePower(self, gw):
        self.key_press(gw.hwnd, ord('G'))
        time.sleep(0.8)
        
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(gw.hwnd)
        gw.click(400, 220)
        time.sleep(0.8)

    def click(self, x, y):
        (prevX,prevY) = pyautogui.position()
        pyautogui.moveTo(x, y)
        pyautogui.click()
        pyautogui.moveTo(prevX, prevY)


    def stop(self):
        if self.thread is None: return
        self.app.lbState.set("매크로 종료 중")

        self.app.btnSortWnd3["state"] = "disabled"
        logging.debug('thread stopping...')
        self.stop_threads.set()
        self.thread.join()
        self.thread = None
        logging.debug('thread stopped')

        # UI 상태 초기화
        self.app.btnSortWnd1["state"] = 'normal'     
        self.app.checkReturnToVillBtn["state"] = 'normal'   
        self.app.tbShortcut["state"] = 'normal'
        self.app.tbLoopTerm["state"] = 'normal'
        self.app.tbNonAttack["state"] = 'normal'
        self.app.tbSlackToken["state"] = 'normal'
        self.app.tbChannel["state"] = 'normal'
        self.app.self.lbState.set("대기 중")

    def post_message(self, text):
        response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+self.app.tbSlackToken.get()},data={"channel": self.app.tbChannel.get(),"text": text})

    def key_press(self, hwnd, vk_key):
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
        win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)

    def moveActivate(self):
        for i in self.app.listProcess.curselection():
            self.app.listProcessActivated.insert(0, self.app.listProcess.get(i))

        for i in self.app.listProcess.curselection()[::-1]:
            self.app.listProcess.delete(i)    

    def moveDeactivate(self):
        for i in self.app.listProcessActivated.curselection():            
            self.app.listProcess.insert(0, self.app.listProcessActivated.get(i))

        for i in self.app.listProcessActivated.curselection()[::-1]:
            self.app.listProcessActivated.delete(i)