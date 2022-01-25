from enum import IntEnum
import serial.tools.list_ports
import serial
import time
import pyautogui

class ACTION(IntEnum):
    MOUSE_CLICK = 199,
    MOUSE_MOVE = 200,
    KEY_PRESS = 201,

class ArduinoMacro:
    def __init__(self):
        ports = list(serial.tools.list_ports.comports())

        find = [p[0] for p in ports if 'Arduino' in p.description]
        if len(find) <= 0: 
            print('not found arduino')
            return

        self.port = find[0]
        print(f'arduino PORT: {self.port} finded!')        

        self.arduino = serial.Serial(self.port, 9600, timeout=.1)
        print('arduino connected...')        

    def mouseMove(self, xPos, yPos):
        curPos = pyautogui.position()    
        _params = [
            ACTION.MOUSE_MOVE, 
            curPos.x & 0xff, (curPos.x & 0xff00) >> 8, curPos.y & 0xff, (curPos.y & 0xff00) >> 8, 
            xPos & 0xff, (xPos & 0xff00) >> 8, yPos & 0xff, (yPos & 0xff00) >> 8 ]
        self.arduino.write(_params)        
        time.sleep(0.1)
        pass

    def mouseClick(self):
        self.arduino.write([ACTION.MOUSE_CLICK])
        time.sleep(0.1)
        pass

    def keyPress(self, key):
        if key == 'esc':
            self.arduino.write([ACTION.KEY_PRESS, 27 ])
        elif key == 'paste':
            self.arduino.write([ACTION.KEY_PRESS, 28 ])
        else:
            var = bytes(key, encoding='utf-8')
            self.arduino.write([ACTION.KEY_PRESS, ord(var) ])
        time.sleep(0.1)
        pass