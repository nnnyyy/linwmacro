import threading
import pyautogui
import win32gui
import win32con
import win32api
import win32process
from ctypes import windll
from datetime import datetime, timedelta
import time
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
        self.lineage_window_list = [] 
        self.slackClient = None        
        self.app = app        
        self.tCheckActivate = time.time()           
        self.actionLock = -1
        self.dtLastRadonAlarm = datetime(1900,1,1,0,0,0)        
        
        logging.debug(f'컨트롤러 생성')
        
    def initUI(self):
        #self.app.notebook.bind('<<NotebookTabChanged>>', self.tabChanged)
        pass
    
    def registerWnds(self):
        toplist = []
        self.lineage_window_list = []
        def enum_callback(hwnd, results):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_callback, toplist)
        _wnds = [(_h, _t) for _h,_t in toplist if '리니지w l' in _t.lower() ]
        _wnds.sort(key=lambda d: d[1], reverse=True)
        idx = 0
        for (_h, _t) in _wnds:
            gw = GameWndState(_h, _t, self.app, idx)
            self.lineage_window_list.append(gw)            
            idx = idx + 1
            
    def refreshWnd(self):
        self.stop()
        self.findWnd()
        pass
    
    def findWnd(self):
        # 윈도우 리셋            
        self.destroyWnds();        
        self.registerWnds()
        
        cnt = 0        
        for _gw in self.lineage_window_list:       
            self.app.listProcess.insert(cnt, _gw.name)                
            cnt += 1
            
    def resetWnd(self):
        # 윈도우 리셋    
        # _temp = self.app.listProcessActivated.get(0, END)
        self.destroyWnds();        
        self.registerWnds()
        
        cnt = 0        
        for _gw in self.lineage_window_list:       
            self.app.listProcess.insert(cnt, _gw.name)            
            cnt += 1

    def arragngeWnd(self, type):

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
            if type == 1:
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
        _list.sort(key=lambda d: d[1], reverse=True)      
        for (_h,_t) in _list:
            for _idx  in self.app.listProcess.curselection():
                _t_selected = self.app.listProcess.get(_idx)
                if _t == _t_selected: _list_selected.append((_h,_t))
                
            """
            for _idx  in self.app.listProcessActivated.curselection():
                _t_selected = self.app.listProcessActivated.get(_idx)
                if _t == _t_selected: _list_selected.append((_h,_t))
            """
        
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
            
    def changeMapSelected(self):
        toplist = []
        def enum_callback(hwnd, results):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))

        win32gui.EnumWindows(enum_callback, toplist)
        _list_selected = []
        _list = [(_h, _t) for _h,_t in toplist if '리니지w l' in _t.lower() ]        
        for (_h,_t) in _list:
            for _idx  in self.app.listProcess.curselection():
                _t_selected = self.app.listProcess.get(_idx)
                if _t == _t_selected: _list_selected.append(_t)
                
            """
            for _idx  in self.app.listProcessActivated.curselection():
                _t_selected = self.app.listProcessActivated.get(_idx)
                if _t == _t_selected: _list_selected.append(_t)
            """
        
        _list_selected.sort(key=lambda x:x[1])
        for _gw in self.lineage_window_list:
            lw_title = _gw.name                
            
            if np.size(np.where(np.array(_list_selected) == lw_title)) <= 0:                         
                continue;
            
            _gw.setHuntMap(self.app.comboMapList.get())
            
        self.app.saveSetting()
        pass
            
    def getMailPresent(self):
        for gw in self.lineage_window_list:
            gw.reserveCheckMail()
        pass   
    
    def allReturn(self):
        for gw in self.lineage_window_list:
            gw.reserveReturnToVill()
        pass     

    def setForegroundWndByDoubleClick(self, event):
        if len(self.app.listProcess.curselection()) > 1: return
        
        for i in self.app.listProcess.curselection():
            _title = self.app.listProcess.get(i)
            _finded = next((gw for gw in self.lineage_window_list if gw.name == _title), None)
            if _finded is not None:
                pass

        """
        for i in self.app.listProcessActivated.curselection():
            _title = self.app.listProcessActivated.get(i)
            _finded = next((gw for gw in self.lineage_window_list if gw.name == _title), None)
            if _finded is not None:
                pass
        """
        
        for i in self.app.listProcess.curselection():
            hwnd = win32gui.FindWindow(None, self.app.listProcess.get(i))
            self.setForegroundWnd(hwnd)

        """
        for i in self.app.listProcessActivated.curselection():
            hwnd = win32gui.FindWindow(None, self.app.listProcessActivated.get(i))
            self.setForegroundWnd(hwnd)
        """

    def setForegroundWnd(self, hwnd):
        shell.SendKeys('%')
        win32gui.SetForegroundWindow(hwnd)

    def onProcInThread(self, type=1):             
        #self.app.lbState.set("매크로 실행 중") 
        self.app.tConcourse = time.time()  
        
        self.slackClient = WebClient(token=self.app.tbSlackToken.get())          
        
        import psutil
        prevX = -1
        prevY = -1
        while not self.stop_threads.is_set():       
            (curX,curY) = pyautogui.position()     
            if curX == prevX and curY == prevY:                
                if time.time() - tMouseMoved > 2:
                    pass
                else:
                    # print('macro stopped', time.time() - tMouseMoved)
                    continue
            else:
                tMouseMoved = time.time()
                prevX = curX
                prevY = curY
                continue
            
            loopTerm = float(self.app.tbLoopTerm.get())       
            cpu = psutil.cpu_percent()
            memory_usage_dict = dict(psutil.virtual_memory()._asdict())
            memory_usage_percent = memory_usage_dict['percent']
            #print(f"BEFORE CODE: memory_usage_percent: {memory_usage_percent}%")
            _tStart = time.time()
            
            # self.checkDeactivatedList()
            _gw: GameWndState
            
            for _gw in self.lineage_window_list:
                lw_hwnd = _gw.hwnd
                lw_title = _gw.name
                
                # 라돈 시간 알림
                now = datetime.now()
                if now.hour == 14 and now.minute == 54 and (now - self.dtLastRadonAlarm).days > 0:
                    self.dtLastRadonAlarm = now
                    self.app.post_message('라돈 잡아라~')
        
                try:                             
                    TId, pid = win32process.GetWindowThreadProcessId(lw_hwnd)
                    current_process = psutil.Process(pid)
                    current_process_memory_usage_as_KB = current_process.memory_info()[0] / 2.**20                    
                    win32gui.ShowWindow(lw_hwnd, win32con.SW_NORMAL) 
                    
                    """
                    activatedWndList = np.array(self.app.listProcessActivated.get(0,END))        
                    if np.size(np.where(activatedWndList == lw_title)) <= 0:
                        if memory_usage_percent < 80:
                            _gw.updateUIOnly()
                        continue
                    """
                    
                    # print(f"{pid} : {lw_title} BEFORE CODE: Current memory KB   : {current_process_memory_usage_as_KB: 9.3f} KB")
                    if (memory_usage_percent >= 80 and current_process_memory_usage_as_KB >= 2500) or current_process_memory_usage_as_KB >= 5000:
                        self.app.post_message(f'{lw_title}, {lw_hwnd} : 메모리 부족 및 과사용으로 프로세스 종료 : {memory_usage_percent}%, {current_process_memory_usage_as_KB}KB')
                        parent = psutil.Process(pid)                        
                        for child in parent.children(recursive=True): #자식-부모 종료                             
                            child.kill()
                        
                        parent.kill()
                        time.sleep(1)
                        self.resetWnd()
                        break
                    
                    if _gw.screenshot() == False:
                        logging.error(f'{_gw} screenshot failed..')                        
                        continue 
                    
                    # current_process_memory_usage_as_KB = current_process.memory_info()[0] / 2.**20
                    # print(f"AFTER CODE: Current memory KB   : {current_process_memory_usage_as_KB: 9.3f} KB")
                    
                    _gw.update()
                    
                except Exception as e:
                    print(f'{lw_title} -  {e}')
                    # logging.error(f'{lw_title} -  {e}')
                    self.sendAlertMsgDelay(lw_title, e)
                    # _gw.setPause(True)
                    # self.removeFromProcList(_gw)
                    break
            
            _gap = loopTerm - (time.time() - _tStart)
            if _gap <= 0: _gap = 0
            time.sleep(_gap)  

    def sendAlertMsgDelay(self, name, msg):
        tNonAttackTerm = int(self.app.tbNonAttack.get())
        _t = time.time() - self.app.tNoneAutoAttackAlertTime
        if _t >= tNonAttackTerm:            
            self.app.post_message(f'{name} : {msg}')
            self.app.tNoneAutoAttackAlertTime = time.time()
            return True
        else:
            return False
            
    def removeFromProcList(self, gw:GameWndState):
        self.lineage_window_list = [item for item in self.lineage_window_list if item.name == gw.name]
        self.app.listProcess.delete(self.app.listProcess.get(0, "end").index(gw.name))        
        # self.app.listProcessActivated.delete(self.app.listProcessActivated.get(0, "end").index(gw.name))        
            
    def checkDeactivatedList(self):
        if time.time() - self.tCheckActivate >= 60 * 5:
            self.tCheckActivate = time.time()
            if self.app.listProcess.size() > 0:                
                self.app.post_message(f'활성화 되지 않은 프로세스가 있습니다')
        pass

    def start(self, type=1):
        self.stop_threads.clear()
        self.thread = threading.Thread(target = self.onProcInThread, args=(type,))
        self.thread.setDaemon(True)
        self.thread.start()
        self.app.btnSortWnd1["state"] = 'disabled'
        self.app.btnSortWnd3["state"] = "normal"
        # self.app.tbShortcutUI["state"] = 'disabled'
        # self.app.tbLoopTermUI["state"] = 'disabled'
        # self.app.tbNonAttackUI["state"] = 'disabled'
        self.app.tbSlackTokenUI["state"] = 'disabled'
        self.app.tbChannelUI["state"] = 'disabled'   
        # self.app.tbShortcutTeleportUI["state"] = 'disabled' 

    def click(self, x, y):
        (prevX,prevY) = pyautogui.position()
        pyautogui.moveTo(x, y)
        pyautogui.click()
        pyautogui.moveTo(prevX, prevY)


    def stop(self):
        if self.thread is None: return

        logging.debug('thread stopping...')
        self.stop_threads.set()        
        self.thread.join(timeout=2.0)
        self.thread = None
        logging.debug('thread stopped')        
        
        # UI 상태 초기화
        self.app.btnSortWnd3["state"] = "disabled"
        self.app.btnSortWnd1["state"] = 'normal'     
        # self.app.tbShortcutUI["state"] = 'normal'
        # self.app.tbLoopTermUI["state"] = 'normal'
        # self.app.tbNonAttackUI["state"] = 'normal'
        self.app.tbSlackTokenUI["state"] = 'normal'
        self.app.tbChannelUI["state"] = 'normal'
        # self.app.tbShortcutTeleportUI["state"] = 'normal'
        #self.app.lbState.set("대기 중")         

    def key_press(self, hwnd, vk_key):
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, vk_key, 0)
        win32gui.SendMessage(hwnd, win32con.WM_KEYUP, vk_key, 0)

    def moveActivate(self):
        wndNames = []
        for i in self.app.listProcess.curselection():
            _name = self.app.listProcess.get(i)
            wndNames.append(_name)
        
        for _name in wndNames:
            for _gw in self.lineage_window_list:
                if _gw.name == _name: 
                    _gw.setPause(False)

    def moveDeactivate(self):
        wndNames = []
        """
        for i in self.app.listProcessActivated.curselection():
            _name = self.app.listProcessActivated.get(i)
            wndNames.append(_name)
        """
        
        for _name in wndNames:
            for _gw in self.lineage_window_list:
                if _gw.name == _name: 
                    _gw.setPause(True)
                    _gw.resetState()
                    
    def destroyWnds(self):
        wndNames = []
        for _name in self.app.listProcess.get(0, "end"):
            wndNames.append(_name)
            
        for _name in wndNames:
            for _gw in self.lineage_window_list:
                if _gw.name == _name: 
                    _gw.destroyAll()
        
        wndNames = []
        """
        for _name in self.app.listProcessActivated.get(0, "end"):
            wndNames.append(_name)
            
        for _name in wndNames:
            for _gw in self.lineage_window_list:
                if _gw.name == _name: 
                    _gw.destroyAll()
        """
                    
        self.app.listProcess.delete(0, END)
        # self.app.listProcessActivated.delete(0, END)