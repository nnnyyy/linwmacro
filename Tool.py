from arduino import ArduinoMacro
import requests
import tkinter
import time
from tkinter import *
from tkinter import ttk
import tkinter.ttk
import cv2
import json
import os

# PATH_CHECK_AUTO_MOVE_BTN = './image/checkautomovebtn.png'
PATH_CHECK_WORLDMAP = './image/checkworldmap.png'
PATH_CHECK_SHOP = './image/checkshop.png'

class ToolDlg( tkinter.Tk ):    
    def __init__(self, parent):
        tkinter.Tk.__init__(self, parent)
        
        self.map_list = [
            '비탄의 땅',
            '죽음의 폐허',
            '포도밭',
            '정화의 대지',
            '뒤틀린 땅',
            '밀밭',
            '네루가 오크 부락',
            '아투바 오크 부락',
            '두다 마라 오크 부락',
            '글루디오 던전 1층',
            '글루디오 던전 2층',
            '글루디오 던전 3층',
            '글루디오 던전 4층',
            '글루디오 던전 5층',
            '글루디오 던전 6층',
            '요정 숲 던전 1층',
            '요정 숲 던전 2층',
            '요정 숲 던전 3층',
            '황무지',
            '붉은 개미 군락',
            '개미굴 입구 1구역',
            '개미굴 입구 2구역',
            '개미굴 입구 3구역',
            '개미굴 입구 4구역',
            '개미굴 입구 5구역',
            '개미굴 입구 6구역',
            '개미굴 1층 1구역',
            '개미굴 1층 2구역',
            '개미굴 1층 3구역',
            '개미굴 1층 4구역',
            '개미굴 1층 5구역',
            '개미굴 1층 6구역',
            '개미굴 2층 1구역',
            '개미굴 2층 2구역',
            '개미굴 2층 3구역',
        ]
        from win32api import GetSystemMetrics

        print('Width:', GetSystemMetrics(0))
        print('Height:', GetSystemMetrics(1))
        self.arduino = ArduinoMacro()
        
        # json 옵션 파일 사용 예정
        if not os.path.exists('./setting.json'):
            with open('./setting.json','w+') as outfile:
                self.settings = {}
                json.dump(self.settings, outfile, indent=4)
        else:
            with open('./setting.json', 'r', encoding='UTF8') as jsonfile:
                self.settings = json.load(jsonfile)                                
        
        self.parent = parent
        self.tNoneAutoAttackAlertTime = 0

        from processController import ProcessController                
        self.controller = ProcessController(self)
        self.initialize()
        
        # self._checkAutoMoveBtn = cv2.imread(PATH_CHECK_AUTO_MOVE_BTN, cv2.IMREAD_COLOR)
        self._checkShop = cv2.imread(PATH_CHECK_SHOP, cv2.IMREAD_COLOR)
        self._imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        self._imgCheckShopBtnWithMove = cv2.imread('./image/checkShopBtnWithMove.png', cv2.IMREAD_COLOR)   
        self._checkmap = cv2.imread(PATH_CHECK_WORLDMAP, cv2.IMREAD_COLOR) 
        self._imgCheckSavePower = cv2.imread('./image/checksavepower.png', cv2.IMREAD_COLOR)               
        self._imgPowerSaveMenu = cv2.imread('./image/powersavemenu.png', cv2.IMREAD_COLOR)   
        self._imgCheckAutoAttack = cv2.imread('./image/autoattack.png', cv2.IMREAD_COLOR)  
        self._imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)   
        self._imgCheck1Digit = cv2.imread('./image/check1digit.png', cv2.IMREAD_COLOR)        
        self._imgCheckNoAttackByWeight = cv2.imread('./image/checknoattackbyweight.png', cv2.IMREAD_COLOR)                
        self._imgCheckAttacked = cv2.imread('./image/attacked.png', cv2.IMREAD_COLOR)
        self._imgFavorateBtn = cv2.imread('./image/favorateBtn.png', cv2.IMREAD_COLOR)
        self._imgFavorateBtn2 = cv2.imread('./image/favorateBtn2.png', cv2.IMREAD_COLOR)
        self._imgMapHamberger = cv2.imread('./image/map_hamberger.png', cv2.IMREAD_COLOR)
        self._imgMapSearch = cv2.imread('./image/map_search.png', cv2.IMREAD_COLOR)       
        # self._imgCheckHoldMove = cv2.imread('./image/checkHoldMove.png', cv2.IMREAD_COLOR)       
        self._imgWait = cv2.imread('./image/wait.png', cv2.IMREAD_COLOR)
        self._imgGameExitWnd = cv2.imread('./image/gameexitwnd.png', cv2.IMREAD_COLOR)        
        
    def reloadSetting(self):
        with open('./setting.json', 'r', encoding='UTF8') as jsonfile:
            self.settings = json.load(jsonfile) 
            
        for gw in self.controller.lineage_window_list:
            gw.reloadSetting()
            
    def saveSetting(self):        
        with open('./setting.json','w+', encoding='UTF8') as outfile:            
            json.dump(self.settings, outfile, indent=4, ensure_ascii=False)
        pass
        
    def initialize(self):
        self.toolWidth = 800
        self.toolHeight = 680
        self.title("MogulMogul v1.1")
        self.geometry(f"{self.toolWidth}x{self.toolHeight}+100+100")
        self.resizable(False, False)
           
        self.tbShortcut = tkinter.StringVar()
        self.tbShortcut.set("5")
        self.tbShortcutTeleport = tkinter.StringVar()
        self.tbShortcutTeleport.set("6")        
        self.tbLoopTerm = tkinter.IntVar()
        self.tbLoopTerm.set(2)
        self.tbNonAttack = tkinter.StringVar()
        self.tbNonAttack.set("300")
        self.tbSlackToken = tkinter.StringVar()
        self.tbSlackToken.set("xoxb-1436627767411-2747230415026-VHEhgdqFabJk3CvOSU5Yf3M3")
        self.tbChannel = tkinter.StringVar()
        self.tbChannel.set("#lineage_alert")
        self.rbvMoveType = tkinter.IntVar()
        self.rbvMoveType.set(3)
        self.tConcourse = time.time()
        
        _y = 10
        dy = 36
        
        # 공통 설정 페이지
        self.notebook = tkinter.ttk.Notebook(self, width=self.toolWidth-20, height=self.toolHeight-50)
        self.notebook.place(x=10,y=_y)
        
        menubar=tkinter.Menu(self)
        menu_1=tkinter.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="편의기능", menu=menu_1)
        menu_1.add_command(label="설정 리로드", command=self.reloadSetting)
        menu_1.add_command(label="설정 저장", command=self.saveSetting)        
        menu_1.add_command(label="우편함 보상 받기", command=self.controller.getMailPresent)
        menu_1.add_command(label="단체 귀환", command=self.controller.allReturn)
        self.config(menu=menubar)
        
        
        menu_2=tkinter.Menu(menubar, tearoff=0, selectcolor="red")
        menubar.add_cascade(label="윈도우", menu=menu_2)
        menu_2.add_command(label="새로고침", command=self.controller.refreshWnd)
        menu_2.add_command(label="뭉치기", command=lambda: self.controller.arragngeWnd(0)) 
        menu_2.add_command(label="계단식 정렬", command=lambda: self.controller.arragngeWnd(1))        
        menu_2.add_command(label="바둑판 정렬(선택된 것만)", command=self.controller.arragngeWndSelected)        
        
        frame1 = tkinter.Frame(self)
        self.notebook.add(frame1, text="설정")

        Label(frame1, text="갱신 주기(초)", anchor="w", height=1, padx=1, pady=2, fg='blue').pack()
        scale=tkinter.Scale(frame1, variable=self.tbLoopTerm, orient="horizontal", showvalue=False, tickinterval=1, to=10, length=200)
        scale.pack()

        Label(frame1, text="알람 반복 주기(초)", anchor="w", height=1, padx=1, pady=2, fg='blue').pack()
        scale=tkinter.Scale(frame1, variable=self.tbNonAttack, orient="horizontal", showvalue=False, tickinterval=30, to=600, length=600)
        scale.pack()        
         
        self.frmProcess = tkinter.LabelFrame(frame1, text="프로세스")
        self.frmProcess.pack()


        
        self.listProcess = tkinter.Listbox(self.frmProcess, selectmode='extended')        
        self.listProcess.bind('<<ListboxSelect>>', self.controller.setForegroundWndByDoubleClick)
        self.listProcess.pack()
        
        # self.btnMoveActivate = Button(frame1, text=">>", command=self.controller.moveActivate)
        # self.btnMoveActivate.place(x=560,y=80)

        # self.btnMoveDeactivate = Button(frame1, text="<<", command=self.controller.moveDeactivate)
        # self.btnMoveDeactivate.place(x=560,y=110)

        # Label(frame1, text="활성 프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=600,y=_y)
        # self.listProcessActivated = tkinter.Listbox(frame1, selectmode='extended')
        # self.listProcessActivated.bind('<<ListboxSelect>>', self.controller.setForegroundWndByDoubleClick)
        # self.listProcessActivated.place(x=600,y=32)

        # Label(frame1,text="귀환 단축키 설정", fg='blue').place(x=0,y=_y)        
        # self.tbShortcutUI = Entry(frame1, width=4, textvariable=self.tbShortcut)
        # self.tbShortcutUI.place(x=160,y=_y)
        
        # _y+=dy
        
        # Label(frame1,text="순간이동 단축키 설정", fg='blue').place(x=0,y=_y)        
        # self.tbShortcutTeleportUI = Entry(frame1, width=4, textvariable=self.tbShortcutTeleport)
        # self.tbShortcutTeleportUI.place(x=160,y=_y)
        
        # _y+=dy
        

        
        
        _y+=dy
        
        # Label(frame1, text="복귀 방식", fg='blue').place(x=0,y=_y)
        
        # self.rbMoveType3 = Radiobutton(frame1, text="타겟 이동", value=3, variable=self.rbvMoveType)
        # self.rbMoveType3.place(x=240, y=_y)
        
        # _y+=dy        
        
        # self.comboMapList = ttk.Combobox(frame1, values=self.map_list, state="readonly")
        # self.comboMapList.current(0)
        # self.comboMapList.place(x=4,y=_y+2)
        
        # Button(frame1, text="선택된 윈도우 맵 일괄 변경", command=self.controller.changeMapSelected).place(x=184,y=_y)
        
        # _y+=dy
        
        self.btnSortWnd1 = Button(frame1, text="모니터링 실행", command=lambda: self.controller.start(1))
        self.btnSortWnd1.pack()
        
        self.btnSortWnd3 = Button(frame1, text="모니터링 종료", command=self.controller.stop)
        self.btnSortWnd3.pack()
        self.btnSortWnd3["state"] = "disabled"
        
        _y+=dy       
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 개별 세부 항목
        self.frame_detail = tkinter.Frame(self)
        self.notebook.add(self.frame_detail, text="개별 세부 항목")
        
        # 알람 설정
        frame_alarm = tkinter.Frame(self)
        self.notebook.add(frame_alarm, text="알람")
        
        Label(frame_alarm, text="슬랙 알람 전송", anchor="w", height=1, padx=1, pady=2).pack(side='top', anchor='center')
        
        Label(frame_alarm, text="토큰", anchor="w", height=1, padx=1, pady=2).pack(side='top', anchor='center')
        self.tbSlackTokenUI = Entry(frame_alarm, width=32, textvariable=self.tbSlackToken)
        self.tbSlackTokenUI.pack(side='top', anchor='center')

        Label(frame_alarm, text="채널명", anchor="w", height=1, padx=1, pady=2).pack(side='top', anchor='center')
        self.tbChannelUI = Entry(frame_alarm, width=32, textvariable=self.tbChannel)
        self.tbChannelUI.pack(side='top', anchor='center')
        
        self.controller.initUI()
        
        self.controller.findWnd()
        
        self.controller.start(1)
        
    def on_closing(self):
        self.controller.stop()
        self.destroy()
    
    def post_message(self, text):
        response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+self.tbSlackToken.get()},data={"channel": self.tbChannel.get(),"text": text})
    