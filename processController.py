import threading
import pyautogui
import win32gui
import win32con
import win32api
from ctypes import windll
import time
import numpy as np
import win32com.client
# Add this to __ini__
shell = win32com.client.Dispatch("WScript.Shell")
from tkinter import *

from slack import WebClient
from GameWndState import GameWndState, GWState
import logging
import ctypes
import psutil

class ProcessController(object):
    from Tool import ToolDlg
    def __init__(self, app:ToolDlg):        
        self.thread = None
        self.stop_threads = threading.Event()
        self.lineage_window_list = [] 
        self.slackClient = None        
        self.app = app        
        self.tCheckActivate = time.time()
        logging.debug(f'컨트롤러 생성')
    
    def refreshWnds(self):
        toplist = []
        self.lineage_window_list = []
        def enum_callback(hwnd, results):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_callback, toplist)
        _wnds = [(_h, _t) for _h,_t in toplist if '리니지w l' in _t.lower() ]
        for (_h, _t) in _wnds:
            gw = GameWndState(_h, _t, self.app)
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

    def onProcInThread(self, type=1):             
        self.app.lbState.set("매크로 실행 중") 
        self.app.tConcourse = time.time()  
        
        self.slackClient = WebClient(token=self.app.tbSlackToken.get())  
        loopTerm = float(self.app.tbLoopTerm.get())       
        
        import psutil
        import os
        
        while not self.stop_threads.is_set():   
            # memory_usage_dict = dict(psutil.virtual_memory()._asdict())
            # memory_usage_percent = memory_usage_dict['percent']
            # print(f"BEFORE CODE: memory_usage_percent: {memory_usage_percent}%")
            _tStart = time.time()
            
            self.checkDeactivatedList()
            _gw: GameWndState   
            
            # 사냥 시 일정 시간 간격으로 모으기
            if self.app.checkConcourse.get() == 1 and (time.time() - self.app.tConcourse) >= 1200:
                for _gw in self.lineage_window_list:
                    activatedWndList = np.array(self.app.listProcessActivated.get(0,END))        
                    if np.size(np.where(activatedWndList == lw_title)) <= 0:                         
                        continue;
                    _gw.concourse()
                self.app.tConcourse = time.time()
                continue
            
            for _gw in self.lineage_window_list:
                lw_hwnd = _gw.hwnd
                lw_title = _gw.name
                try:         
                    # pid = ctypes.windll.kernel32.GetProcessId(lw_hwnd)
                    # current_process = psutil.Process(pid)
                    # current_process_memory_usage_as_KB = current_process.memory_info()[0] / 2.**20
                    # print(f"BEFORE CODE: Current memory KB   : {current_process_memory_usage_as_KB: 9.3f} KB")
                    
                    activatedWndList = np.array(self.app.listProcessActivated.get(0,END))        
                    if np.size(np.where(activatedWndList == lw_title)) <= 0:                         
                        continue;
                    
                    
                    win32gui.ShowWindow(lw_hwnd, win32con.SW_NORMAL) 
                    if _gw.screenshot() == False:
                        logging.error(f'{_gw} screenshot failed..')                        
                        continue 
                    
                    # current_process_memory_usage_as_KB = current_process.memory_info()[0] / 2.**20
                    # print(f"AFTER CODE: Current memory KB   : {current_process_memory_usage_as_KB: 9.3f} KB")
                    
                    _gw.update()
                    
                except Exception as e:
                    print(f'{lw_title} -  {e}')
                    logging.error(f'{lw_title} -  {e}')
                    # self.post_message(token, '#lineage_alert', 'error:' + e + ' ' + lw_title)
            
            _gap = loopTerm - (time.time() - _tStart)
            if _gap <= 0: _gap = 0
            time.sleep(_gap)       
            
    def checkDeactivatedList(self):
        if time.time() - self.tCheckActivate >= 60 * 5:
            self.tCheckActivate = time.time()
            if self.app.listProcess.size() > 0:                
                self.app.post_message(f'활성화 되지 않은 프로세스가 있습니다')
        pass

    def start(self, type=1):
        self.stop_threads.clear()
        self.thread = threading.Thread(target = self.onProcInThread, args=(type,))
        self.thread.start()
        self.app.btnSortWnd1["state"] = 'disabled'
        self.app.btnSortWnd3["state"] = "normal"
        self.app.tbShortcutUI["state"] = 'disabled'
        self.app.tbLoopTermUI["state"] = 'disabled'
        self.app.tbNonAttackUI["state"] = 'disabled'
        self.app.tbSlackTokenUI["state"] = 'disabled'
        self.app.tbChannelUI["state"] = 'disabled'
        self.app.checkReturnToVillBtn["state"] = 'disabled'    

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
        self.app.tbShortcutUI["state"] = 'normal'
        self.app.tbLoopTermUI["state"] = 'normal'
        self.app.tbNonAttackUI["state"] = 'normal'
        self.app.tbSlackTokenUI["state"] = 'normal'
        self.app.tbChannelUI["state"] = 'normal'
        self.app.lbState.set("대기 중")    

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