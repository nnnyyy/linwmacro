import requests
import tkinter
import time
from tkinter import *
import tkinter.ttk
import cv2
import json
import os

PATH_CHECK_AUTO_MOVE_BTN = './image/checkautomovebtn.png'
PATH_CHECK_WORLDMAP = './image/checkworldmap.png'
PATH_CHECK_SHOP = './image/checkshop.png'

class ToolDlg( tkinter.Tk ):
    def __init__(self, parent):
        tkinter.Tk.__init__(self, parent)
        
        # json 옵션 파일 사용 예정
        if not os.path.exists('./setting.json'):
            with open('./setting.json','w+') as outfile:
                _d = {}
                _d['test'] = '123'
                json.dump(_d, outfile, indent=4)
        else:
            with open('./setting.json', 'r') as jsonfile:
                _d2 = json.load(jsonfile)
                print(_d2)
        
        self.parent = parent
        from processController import ProcessController                
        self.controller = ProcessController(self)
        self.initialize()
        
        self._checkAutoMoveBtn = cv2.imread(PATH_CHECK_AUTO_MOVE_BTN, cv2.IMREAD_COLOR)
        self._checkShop = cv2.imread(PATH_CHECK_SHOP, cv2.IMREAD_COLOR)
        self._imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)
        self._imgCheckShopBtnWithMove = cv2.imread('./image/checkShopBtnWithMove.png', cv2.IMREAD_COLOR)   
        self._checkmap = cv2.imread(PATH_CHECK_WORLDMAP, cv2.IMREAD_COLOR) 
        self._imgCheckSavePower = cv2.imread('./image/checksavepower.png', cv2.IMREAD_COLOR)               
        self._imgPowerSaveMenu = cv2.imread('./image/powersavemenu.png', cv2.IMREAD_COLOR)   
        self._imgCheckAutoAttack = cv2.imread('./image/autoattack.png', cv2.IMREAD_COLOR)  
        self._imgCheckVill = cv2.imread('./image/checkvil.png', cv2.IMREAD_COLOR)   
        self._imgCheck1Digit = cv2.imread('./image/check1digit.png', cv2.IMREAD_COLOR)
        self._imgCheckHP = cv2.imread('./image/checkhp.png', cv2.IMREAD_COLOR)        
        self._imgCheckMP = cv2.imread('./image/checkmp.png', cv2.IMREAD_COLOR)        
        self._imgCheckNoAttackByWeight = cv2.imread('./image/checknoattackbyweight.png', cv2.IMREAD_COLOR)                
        self._imgCheckAttacked = cv2.imread('./image/attacked.png', cv2.IMREAD_COLOR)
        self._imgFavorateBtn = cv2.imread('./image/favorateBtn.png', cv2.IMREAD_COLOR)
        self._imgFavorateBtn2 = cv2.imread('./image/favorateBtn2.png', cv2.IMREAD_COLOR)
        
    def initialize(self):
        self.title("MogulMogul v1.1")
        self.geometry("1024x500+100+100")
        self.resizable(False, False)
        
        self.lbState = tkinter.StringVar()
        self.lbState.set("대기 중")           
        self.checkConcourse = tkinter.IntVar()
        self.checkConcourse.set(0)       
        
        self.cbvNoHuntOnlyAlarm = tkinter.IntVar()
        self.cbvNoHuntOnlyAlarm.set(0)        
        self.tbShortcut = tkinter.StringVar()
        self.tbShortcut.set("5")
        self.tbShortcutTeleport = tkinter.StringVar()
        self.tbShortcutTeleport.set("6")        
        self.tbLoopTerm = tkinter.StringVar()
        self.tbLoopTerm.set("1")
        self.tbNonAttack = tkinter.StringVar()
        self.tbNonAttack.set("300")
        self.tbSlackToken = tkinter.StringVar()
        self.tbSlackToken.set("xoxb-1436627767411-2747230415026-VHEhgdqFabJk3CvOSU5Yf3M3")
        self.tbChannel = tkinter.StringVar()
        self.tbChannel.set("#lineage_alert")
        self.rbvMoveType = tkinter.IntVar()
        self.rbvMoveType.set(1)
        self.tConcourse = time.time()
        
        _y = 10
        dy = 36
        
        # 공통 설정 페이지
        self.notebook = tkinter.ttk.Notebook(self, width=1004, height=450)
        self.notebook.place(x=10,y=_y)
        
        
        
        frame1 = tkinter.Frame(self)
        self.notebook.add(frame1, text="공통")
        
        Label(frame1, text="상태 :", width=4, height=1, padx=1, pady=2).place(x=0,y=_y)
        self.lbStateUI = Label(frame1, width=14, height=1, fg="red", anchor="w", padx=1, pady=2, textvariable=self.lbState)
        self.lbStateUI.place(x=38,y=_y)    
        
        Label(frame1, text="프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=420,y=_y)
        self.listProcess = tkinter.Listbox(frame1, selectmode='extended')
        self.listProcess.bind('<Double-1>', self.controller.setForegroundWndByDoubleClick)
        self.listProcess.place(x=420,y=32)

        Label(frame1, text="활성 프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=620,y=_y)
        self.listProcessActivated = tkinter.Listbox(frame1, selectmode='extended')
        self.listProcessActivated.bind('<Double-1>', self.controller.setForegroundWndByDoubleClick)
        self.listProcessActivated.place(x=620,y=32)
        
        _y+=dy

        Label(frame1,text="귀환 단축키 설정", fg='blue').place(x=0,y=_y)        
        self.tbShortcutUI = Entry(frame1, width=4, textvariable=self.tbShortcut)
        self.tbShortcutUI.place(x=160,y=_y)
        
        _y+=dy
        
        Label(frame1,text="순간이동 단축키 설정", fg='blue').place(x=0,y=_y)        
        self.tbShortcutTeleportUI = Entry(frame1, width=4, textvariable=self.tbShortcutTeleport)
        self.tbShortcutTeleportUI.place(x=160,y=_y)
        
        _y+=dy

        Label(frame1, text="매크로 반복 주기(초) :", anchor="w", width=17, height=1, padx=1, pady=2, fg='blue').place(x=0,y=_y)
        self.tbLoopTermUI = Entry(frame1, width=4, textvariable=self.tbLoopTerm)
        self.tbLoopTermUI.place(x=160,y=_y)

        Label(frame1, text="창은 800x450 고정\nUI는 1단계로 설정하세요\n슬랙은 chat:write 활성화 필요", width=22, height=4, padx=1, pady=2, fg='blue').place(x=214,y=55)
        
        _y+=dy

        Label(frame1, text="비전투 알람 반복 주기(초) :", anchor="w", width=22, height=1, padx=1, pady=2, fg='blue').place(x=0,y=_y)
        self.tbNonAttackUI = Entry(frame1, width=4, textvariable=self.tbNonAttack)
        self.tbNonAttackUI.place(x=160,y=_y)
        
        _y+=dy
        
        Label(frame1, text="복귀 방식", fg='blue').place(x=0,y=_y)
        
        self.rbMoveType1 = Radiobutton(frame1, text="표식 이동", value=1, variable=self.rbvMoveType)
        self.rbMoveType1.place(x=80, y=_y)
        
        self.rbMoveType2 = Radiobutton(frame1, text="즐겨찾기 이동", value=2, variable=self.rbvMoveType)
        self.rbMoveType2.place(x=160, y=_y)
        
        _y+=dy
        
        self.checkConcourseBtn = Checkbutton(frame1,text="전투 중 모으기",variable=self.checkConcourse)
        self.checkConcourseBtn.place(x=0,y=_y)
        
        self.cbNoHuntOnlyAlarm = Checkbutton(frame1,text="자동복귀 안하고 알람만",variable=self.cbvNoHuntOnlyAlarm)
        self.cbNoHuntOnlyAlarm.place(x=150,y=_y)
        
        _y+=dy

        self.btnFindWnd = Button(frame1, text="윈도우 초기화", command=self.controller.findWnd)
        self.btnFindWnd.place(x=4,y=_y)       
        
        
        self.btnArrangeWnd = Button(frame1, text="윈도우 계단식 정렬", command=self.controller.arragngeWnd)
        self.btnArrangeWnd.place(x=94,y=_y)       
        

        self.btnFindWnd = Button(frame1, text="선택된 윈도우 바둑판 정렬", command=self.controller.arragngeWndSelected)
        self.btnFindWnd.place(x=214,y=_y)
        
        _y+=dy        
        
        
        _y+=dy
        
        self.btnSortWnd1 = Button(frame1, text="매크로 실행", command=lambda: self.controller.start(1))
        self.btnSortWnd1.place(x=8,y=_y)
        
        _y+=dy

        self.btnSortWnd3 = Button(frame1, text="매크로 종료", command=self.controller.stop)
        self.btnSortWnd3.place(x=8,y=_y)
        self.btnSortWnd3["state"] = "disabled"
        
        

        self.btnMoveActivate = Button(frame1, text=">>", command=self.controller.moveActivate)
        self.btnMoveActivate.place(x=580,y=80)

        self.btnMoveDeactivate = Button(frame1, text="<<", command=self.controller.moveDeactivate)
        self.btnMoveDeactivate.place(x=580,y=110)
        
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
        
    def on_closing(self):
        self.controller.stop()
        self.destroy()
    
    def post_message(self, text):
        response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+self.tbSlackToken.get()},data={"channel": self.tbChannel.get(),"text": text})       
    