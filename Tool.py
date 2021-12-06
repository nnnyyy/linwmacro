import requests
import tkinter
from tkinter import *


class ToolDlg( tkinter.Tk ):
    def __init__(self, parent):
        tkinter.Tk.__init__(self, parent)
        
        self.parent = parent
        from processController import ProcessController        
        self.controller = ProcessController(self)
        self.initialize()
        
    def initialize(self):
        self.title("MogulMogul v1.0")
        self.geometry("800x500+100+100")
        self.resizable(False, False)
        
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
        
        Label(self, text="프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=420,y=10)
        self.listProcess = tkinter.Listbox(self, selectmode='extended')
        self.listProcess.bind('<Double-1>', self.controller.setForegroundWndByDoubleClick)
        self.listProcess.place(x=420,y=32)

        Label(self, text="활성 프로세스 목록", width=16, height=1, padx=1, pady=2, anchor="w").place(x=620,y=10)
        self.listProcessActivated = tkinter.Listbox(self, selectmode='extended')
        self.listProcessActivated.bind('<Double-1>', self.controller.setForegroundWndByDoubleClick)
        self.listProcessActivated.place(x=620,y=32)

        Label(self, text="상태 :", width=4, height=1, padx=1, pady=2).place(x=0,y=0)
        self.lbState = Label(self, width=14, height=1, fg="red", anchor="w", padx=1, pady=2, textvariable=self.lbState)
        self.lbState.place(x=38,y=0)

        self.btnSortWnd1 = Button(self, text="매크로 실행", command=lambda: self.controller.start(1))
        self.btnSortWnd1.place(x=8,y=262)

        self.checkReturnToVillBtn = Checkbutton(self,text="비상 시 단축키 사용",variable=self.checkReturnToVill)
        self.checkReturnToVillBtn   .place(x=0,y=42)
        self.tbShortcut = Entry(self, width=4, textvariable=self.tbShortcut)
        self.tbShortcut.place(x=160,y=44)

        Label(self, text="반복 주기(초) :", anchor="w", width=11, height=1, padx=1, pady=2).place(x=0,y=72)
        self.tbLoopTerm = Entry(self, width=4, textvariable=self.tbLoopTerm)
        self.tbLoopTerm.place(x=160,y=74)

        Label(self, text="창은 800x450 고정\nUI는 1단계로 설정하세요\n슬랙은 chat:write 활성화 필요", width=22, height=4, padx=1, pady=2, fg='blue').place(x=214,y=55)

        Label(self, text="비전투 알람 반복 주기(초) :", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=102)
        self.tbNonAttack = Entry(self, width=4, textvariable=self.tbNonAttack)
        self.tbNonAttack.place(x=160,y=104)

        Label(self, text="슬랙 알람 전송", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=132)

        Label(self, text="토큰 :", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=162)
        self.tbSlackToken = Entry(self, width=32, textvariable=self.tbSlackToken)
        self.tbSlackToken.place(x=160,y=164)

        Label(self, text="채널명 :", anchor="w", width=22, height=1, padx=1, pady=2).place(x=0,y=192)
        self.tbChannel = Entry(self, width=32, textvariable=self.tbChannel)
        self.tbChannel.place(x=160,y=194)

        self.btnArrangeWnd = Button(self, text="윈도우 계단식 정렬", command=self.controller.arragngeWnd)
        self.btnArrangeWnd.place(x=8,y=222)

        self.btnFindWnd = Button(self, text="윈도우 찾기", command=self.controller.findWnd)
        self.btnFindWnd.place(x=420,y=202)

        self.btnFindWnd = Button(self, text="선택된 윈도우 바둑판 정렬", command=self.controller.arragngeWndSelected)
        self.btnFindWnd.place(x=520,y=202)

        self.btnSortWnd3 = Button(self, text="매크로 종료", command=self.controller.stop)
        self.btnSortWnd3.place(x=516,y=262)
        self.btnSortWnd3["state"] = "disabled"

        self.btnMoveActivate = Button(self, text=">>", command=self.controller.moveActivate)
        self.btnMoveActivate.place(x=580,y=80)

        self.btnMoveDeactivate = Button(self, text="<<", command=self.controller.moveDeactivate)
        self.btnMoveDeactivate.place(x=580,y=110)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.controller.findWnd()
        
    def on_closing(self):
        self.controller.stop()
        self.destroy()
    
    def post_message(self, text):
        response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+self.tbSlackToken.get()},data={"channel": self.tbChannel.get(),"text": text})