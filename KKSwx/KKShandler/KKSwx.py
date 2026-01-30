import re

import os

from ultralytics import YOLO
import pyautogui
import pyperclip
import threading
import time
from KKShandler.processhandler.phandler import phandler
import keyboard
from autoqueue.redisMq import RedisQueue
import cv2
import numpy as np
from rapidocr import RapidOCR

class KKSWx():
    def __init__(self):
        self.model_avatar = None
        self.model_text = None
        self.phandler = phandler()
        self.hwnd = None
        self.stop_event = None
        self.lastqueue = []
        self.input_pos = None
        
    
    
    def start(self, quit_hotkey = 'ctrl+alt+p', wxqueues:list[RedisQueue] | list[list] = [RedisQueue('wxqueue')], name:list[str] = []):
        if len(name) != 0:
            self.hwnd = [self.phandler.find_all_windows_by_keyword(name)[0]['hwnd'] for name in name]
        self.loadmodel()
        monitor_thread = threading.Thread(target=self.monitor, args=(wxqueues,))
        self.stop_event = threading.Event()
        keyboard.add_hotkey(quit_hotkey, self.cleanup,args=[wxqueues])
        monitor_thread.start()
        
    def identify(self, model, img):
        '''
        0 = 'I'
        1 = 'Search'
        2 = 'partner'
        3 = 'avatar'
        4 = 'text'
        5 = 'mytext'
        6 = 'myavatar'
        7 = 'nomytext'
        8 = 'notext'
        9 = 'Input'
        10 = 'history'
        11 = 'url'
        '''
        model_results = model.predict(img, save=False, verbose=False)
        return model_results
    

    def monitor(self,wxqueues:list[RedisQueue]| list[list]):
        ocr = RapidOCR()
        ready_list = [i for i in range(len(wxqueues))]
        change_able = [[] for i in range(len(wxqueues))]
        map_sheet = {}
        while  not self.stop_event.is_set():
            num = ready_list.pop(0)
            time.sleep(1)
            # screenshot,left,top = self.phandler.capture_window(self.hwnd[num])
            screenshot = self.phandler.capture_win_alt(hwnd = self.hwnd[num])
            # screenshot = self.phandler.screenshot_window_by_handle(hwnd= self.hwnd,save= True)
            map_sheet[num] = screenshot
            results = self.identify(self.model_avatar, screenshot)
            answer_list = []
            input_box = None
             # 将每个气泡存下用来后续判断新的对话加入
            for i,box in enumerate(results[0].boxes):
                if box.cls == 5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    change_able[num].append((x1,y1,x2,y2))
                elif box.cls == 4:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    change_able[num].append((x1,y1,x2,y2))
                    crop_img = np.array(screenshot)[y1:y2,x1:x2]
                    texts = ocr(crop_img).txts
                    result = ''.join(texts) if isinstance(texts, tuple) else ''
                    answer_list.append((y1, result))
                elif box.cls == 9:
                    input_box = box
            
            if input_box is None:
                print('input box not found')
                continue
            else:
                x, y, w, h = input_box.xywh[0]
                self.input_pos = (int(x.item()),int(y.item()))
            answer_list.sort(key=lambda x: x[0])
            answer_list = [x[1] for x in answer_list]
            self.detectnew(answer_list, wxqueues[num])
            ready_list.append(num)


    def loadmodel(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(os.path.join(base_dir,r"handlermodel\best.pt"))
        self.model_avatar =  YOLO(os.path.join(base_dir,r"handlermodel\best.pt"))  # YOLOv8 Nano 模型

    def cleanup(self, wxqueues:list[RedisQueue]|list[list]):
        self.stop_event.set()
        if isinstance(wxqueues[0], RedisQueue):
            for wxqueue in wxqueues:
                wxqueue.delete()
        else:
            for wxqueue in wxqueues:
                wxqueue.clear()
        print("执行优雅退出流程...")
        return 
    

    def detectnew(self, setences:list, wxqueue:RedisQueue|list):
        def find_indices(target, newlist):
            indices = [i for i, x in enumerate(newlist) if x == target]
            sorted(indices)
            return indices
        
        new_setence = []
        if len(self.lastqueue) == 0:
                new_setence.extend(setences)
                
        else:
            indices = find_indices(self.lastqueue[-1], setences)
            if len(indices) == 0:
                new_setence.extend(setences)
            else:
                
                for index in indices:
                    newlabel = 1
                    for num in range(index, -1, -1):
                        if setences[num] != self.lastqueue[-1-index+num]:
                            newlabel = 0
                            break
                    if newlabel == 1:
                        new_setence.extend(setences[index+1:])
                        
        if len(new_setence) == 0:
            return
        if isinstance(wxqueue, RedisQueue):
            for s in new_setence:
                wxqueue.rput(s)
        elif isinstance(wxqueue, list):
            for s in new_setence:
                wxqueue.append(s)
            print(wxqueue)

        self.lastqueue = setences

    def send_text(self, hwnd:int, text:str):
        for char in text:
            self.phandler.send_char_pywin32(hwnd, char)
        self.phandler.send_enter_pywin32(hwnd)

    
    def get_history(self, hwnd, roll_times: int = 5):

        ocr = RapidOCR()
        self.loadmodel()
        history = []
        from PIL import Image
        
        pos = self.phandler.get_window_coordinates(hwnd)
        for roll in range(roll_times):
            answer_list = []
            screenshot = self.phandler.capture_win_alt(hwnd = hwnd)
            results = self.identify(self.model_avatar, screenshot)
            for i,box in enumerate(results[0].boxes):
                if box.cls == 5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                elif box.cls == 4:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    crop_img = np.array(screenshot)[y1:y2,x1:x2]
                    Img = Image.fromarray(crop_img)
                    texts = ocr(Img).txts
                    results = ''.join(texts) if isinstance(texts, tuple) else ''
                    answer_list.append((y1, results))
            answer_list.sort(key=lambda x: x[0], reverse=True)
            for setence in answer_list:
                if setence[1] not in history:
                    history.append(setence[1])
            for b in range(4):
                self.phandler.scroll_window(hwnd, scroll_delta=100, mouse_pos=(pos[0]+100, pos[1]+300))
        for b in range(4*roll_times):
            self.phandler.scroll_window(hwnd, scroll_delta=-100, mouse_pos=(pos[0]+100, pos[1]+300))

        return history[::-1]
