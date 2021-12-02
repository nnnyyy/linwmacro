# Add this import
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

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# 프로세스 확인
"""
print(psutil.version_info)
print(psutil.cpu_count())
print(psutil.cpu_count(logical=False))
print(psutil.virtual_memory())
print(psutil.swap_memory())
"""

class ProcessController(object):
    def __init__(self):        
        self.thread = None
        self.stop_threads = threading.Event()
        self.dNoneAutoAttackAlertTime = dict()
        self.dAttackedAlertTime = dict()
        self.lbState = tkinter.StringVar()
        self.lbState.set("대기 중")
        self.checkReturnToVill = tkinter.IntVar()
        self.checkReturnToVill.set(1)        
        self.tbShortcut = tkinter.StringVar()
        self.tbShortcut.set("5")
        self.tbLoopTerm = tkinter.StringVar()
        self.tbLoopTerm.set("1")
        self.tbNonAttack = tkinter.StringVar()
        self.tbNonAttack.set("300")
        self.tbSlackToken = tkinter.StringVar()
        self.tbSlackToken.set("xoxb-1436627767411-2747230415026-VHEhgdqFabJk3CvOSU5Yf3M3")
        self.tbChannel = tkinter.StringVar()
        self.tbChannel.set("#lineage_alert")
        self.lineage_window_list = [] 
        self.slackClient = None
    
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
        listProcess.delete(0, END)
        listProcessActivated.delete(0, END)
        self.refreshWnds()        

        cnt = 0
        for _gw in self.lineage_window_list:
            listProcess.insert(cnt, _gw.name)
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
            for _idx  in listProcess.curselection():
                _t_selected = listProcess.get(_idx)
                if _t == _t_selected: _list_selected.append((_h,_t))
                
            for _idx  in listProcessActivated.curselection():
                _t_selected = listProcessActivated.get(_idx)
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

        print(screen_width, screen_height)
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
        tNonAttackTerm = int(self.tbNonAttack.get())
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
        for i in listProcess.curselection():
            hwnd = win32gui.FindWindow(None, listProcess.get(i))
            self.setForegroundWnd(hwnd)

        for i in listProcessActivated.curselection():
            hwnd = win32gui.FindWindow(None, listProcessActivated.get(i))
            self.setForegroundWnd(hwnd)

    def setForegroundWnd(self, hwnd):
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(hwnd)
        
    def uploadFile(self, filePath):
        if self.slackClient is None: return
        
        self.slackClient.files_upload(channels=self.tbChannel.get(), file=filePath)

    def onProcInThread(self, type=1):     
        # self.post_message('매크로 프로그램 시작')
        self.lbState.set("매크로 실행 중")   
        
        self.slackClient = WebClient(token=self.tbSlackToken.get())  
        loopTerm = int(self.tbLoopTerm.get())
        
        _imgCheckSavePower = cv2.imread('./image/checksavepower.png', cv2.IMREAD_COLOR)               
        _imgPowerSaveMenu = cv2.imread('./image/powersavemenu.png', cv2.IMREAD_COLOR)  

        while not self.stop_threads.is_set():   
            _gw: GameWndState   
            for _gw in self.lineage_window_list:
                lw_hwnd = _gw.hwnd
                lw_title = _gw.name
                try:         
                    activatedWndList = np.array(listProcessActivated.get(0,END))        
                    if np.size(np.where(activatedWndList == lw_title)) <= 0:                         
                        continue;                    
                    
                    
                    win32gui.ShowWindow(lw_hwnd, win32con.SW_NORMAL) 
                    if _gw.screenshot() == False:
                        print('screenshot failed..', _gw)
                        continue                    
                
                    isPowerSaveMode = _gw.isMatching(_gw.getImg(764,11,12,3), _imgCheckSavePower) != True
                    isPowerSaveMenu = _gw.isMatching(_gw.img, _imgPowerSaveMenu)
                    if isPowerSaveMenu == True:
                        self.key_press(lw_hwnd, win32con.VK_ESCAPE)
                        continue
                        
                    # 절전모드가 아닌 상태에서
                    # 귀환 상태인지 체크 -> 마을인지 체크 -> 상점 물약 구매 -> 상점인지 체크 -> 자동 구매 -> 이동 -> 자동사냥 -> 모드 종료
                    if _gw.state == GWState.RETURN_TO_VILL:
                        _gw.goBuyPosion(self.tbShortcut.get())
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
                    print('error', e, lw_title)
                    # self.post_message(token, '#lineage_alert', 'error:' + e + ' ' + lw_title)
            
            time.sleep(loopTerm)

    def processOnPowerSaveMode(self, _gw:GameWndState):
        rect = win32gui.GetWindowRect(_gw.hwnd)

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
                _gw.returnToVillage(self.tbShortcut.get())                
                self.post_message(_gw.name + ' : 물약을 보충하십시오.') 

            elif isHPOK == False:   
                _gw.returnToVillage(self.tbShortcut.get())
                self.post_message(_gw.name + ' : HP가 부족합니다. 공격받고 있을 수 있습니다.')
            elif isNoAttackByWeight:
                self.sendAlertMsgDelay(_gw.name, '가방이 가득차서 공격할 수 없습니다.')
        else:
            self.sendAlertMsgDelay(_gw.name, '대기 중입니다.')

    def processOnNormalMode(self, _gw:GameWndState):
        _imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        isCheckNoVill = self.isMatching(_gw.img, _imgCheckVill)
        if isCheckNoVill:
            self.key_press(_gw.img, ord(self.tbShortcut.get().upper()))    

    def start(self, type=1):
        self.stop_threads.clear()
        self.thread = threading.Thread(target = self.onProcInThread, args=(type,))
        self.thread.start()
        btnSortWnd1["state"] = 'disabled'
        btnSortWnd3["state"] = "normal"
        tbShortcut["state"] = 'disabled'
        tbLoopTerm["state"] = 'disabled'
        tbNonAttack["state"] = 'disabled'
        tbSlackToken["state"] = 'disabled'
        tbChannel["state"] = 'disabled'
        checkReturnToVill["state"] = 'disabled'

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
        self.lbState.set("매크로 종료 중")

        btnSortWnd3["state"] = "disabled"
        print('thread stopping...')
        self.stop_threads.set()
        self.thread.join()
        self.thread = None
        print('thread stopped')

        # UI 상태 초기화
        btnSortWnd1["state"] = 'normal'     
        checkReturnToVill["state"] = 'normal'   
        tbShortcut["state"] = 'normal'
        tbLoopTerm["state"] = 'normal'
        tbNonAttack["state"] = 'normal'
        tbSlackToken["state"] = 'normal'
        tbChannel["state"] = 'normal'
        self.lbState.set("대기 중")

    def post_message(self, text):
        response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+self.tbSlackToken.get()},data={"channel": self.tbChannel.get(),"text": text})
        print(response)

    def key_press(self, hwnd, vk_key):
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
        win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)

    def moveActivate(self):
        for i in listProcess.curselection():
            listProcessActivated.insert(0, listProcess.get(i))

        for i in listProcess.curselection()[::-1]:
            listProcess.delete(i)    

    def moveDeactivate(self):
        for i in listProcessActivated.curselection():            
            listProcess.insert(0, listProcessActivated.get(i))

        for i in listProcessActivated.curselection()[::-1]:
            listProcessActivated.delete(i)


def on_closing():
    controller.stop()
    root.destroy()


# UI
root = Tk()
root.title("MogulMogul v1.0")
root.geometry("800x300+100+100")
root.resizable(False, False)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

controller = ProcessController()

Label(root, text="프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=420,y=10)
listProcess = tkinter.Listbox(root, selectmode='extended')
listProcess.bind('<Double-1>', controller.setForegroundWndByDoubleClick)
listProcess.place(x=420,y=32)

Label(root, text="활성 프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=620,y=10)
listProcessActivated = tkinter.Listbox(root, selectmode='extended')
listProcessActivated.bind('<Double-1>', controller.setForegroundWndByDoubleClick)
listProcessActivated.place(x=620,y=32)

Label(root, text="상태 :", width=4, height=1, padx=1, pady=2).place(x=0,y=0)
lbState = Label(root, width=14, height=1, fg="red", anchor="w", padx=1, pady=2, textvariable=controller.lbState)
lbState.place(x=38,y=0)

btnSortWnd1 = Button(root, text="매크로 실행", command=lambda: controller.start(1))
btnSortWnd1.place(x=8,y=262)

checkReturnToVill = Checkbutton(root,text="비상 시 단축키 사용",variable=controller.checkReturnToVill)
checkReturnToVill.place(x=0,y=42)
tbShortcut = Entry(root, width=4, textvariable=controller.tbShortcut)
tbShortcut.place(x=160,y=44)

Label(root, text="반복 주기(초) :", anchor="w", width=11, height=1, padx=1, pady=2).place(x=0,y=72)
tbLoopTerm = Entry(root, width=4, textvariable=controller.tbLoopTerm)
tbLoopTerm.place(x=160,y=74)

Label(root, text="창은 800x450 고정\nUI는 1단계로 설정하세요\n슬랙은 chat:write 활성화 필요", width=22, height=4, padx=1, pady=2, fg='blue').place(x=214,y=55)

Label(root, text="비전투 알람 반복 주기(초) :", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=102)
tbNonAttack = Entry(root, width=4, textvariable=controller.tbNonAttack)
tbNonAttack.place(x=160,y=104)

Label(root, text="슬랙 알람 전송", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=132)

Label(root, text="토큰 :", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=162)
tbSlackToken = Entry(root, width=32, textvariable=controller.tbSlackToken)
tbSlackToken.place(x=160,y=164)

Label(root, text="채널명 :", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=192)
tbChannel = Entry(root, width=32, textvariable=controller.tbChannel)
tbChannel.place(x=160,y=194)

btnArrangeWnd = Button(root, text="윈도우 계단식 정렬", command=controller.arragngeWnd)
btnArrangeWnd.place(x=8,y=222)

btnFindWnd = Button(root, text="윈도우 찾기", command=controller.findWnd)
btnFindWnd.place(x=420,y=202)

btnFindWnd = Button(root, text="선택된 윈도우 바둑판 정렬", command=controller.arragngeWndSelected)
btnFindWnd.place(x=520,y=202)

btnSortWnd3 = Button(root, text="매크로 종료", command=controller.stop)
btnSortWnd3.place(x=516,y=262)
btnSortWnd3["state"] = "disabled"

btnMoveActivate = Button(root, text=">>", command=controller.moveActivate)
btnMoveActivate.place(x=580,y=80)

btnMoveDeactivate = Button(root, text="<<", command=controller.moveDeactivate)
btnMoveDeactivate.place(x=580,y=110)

root.protocol("WM_DELETE_WINDOW", on_closing)

controller.findWnd()
# token = "xoxb-1436627767411-2747230415026-VHEhgdqFabJk3CvOSU5Yf3M3"

root.mainloop()