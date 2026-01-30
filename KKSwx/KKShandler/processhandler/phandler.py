import ctypes
from ctypes import wintypes
import sys
from PIL import Image
import time 
import win32api
import win32con
import win32gui
import win32ui
from ctypes import windll
import numpy as np
import cv2


class RECT(ctypes.Structure):
        _fields_ = [
            ('left', ctypes.c_long),
            ('top', ctypes.c_long),
            ('right', ctypes.c_long),
            ('bottom', ctypes.c_long)
        ]

class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD),
            ('biWidth', wintypes.LONG),
            ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD),
            ('biBitCount', wintypes.WORD),
            ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD),
            ('biXPelsPerMeter', wintypes.LONG),
            ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD),
            ('biClrImportant', wintypes.DWORD)
        ]

class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ('bmiHeader', BITMAPINFOHEADER),
            ('bmiColors', wintypes.DWORD * 3)
        ]

class BITMAPINFO(ctypes.Structure):
        _fields_ = [
            ('bmiHeader', BITMAPINFOHEADER),
            ('bmiColors', wintypes.DWORD * 3)
    ]



class phandler():
    def __init__(self):
        self.found_windows=[]
        # 定义常量
        self.PW_RENDERFULLCONTENT = 2  # 用于 PrintWindow，强制渲染整个窗口内容（包括DWM合成的内容）
        self.DIB_RGB_COLORS = 0
        self.WM_KEYDOWN = 0x0100
        self.WM_KEYUP = 0x0101
        self.WM_CHAR = 0x0102
        self.VK_RETURN = 0x0D
        self.VK_V = 0x56
        self.VK_CONTROL = 0x11

        # 鼠标消息常量
        self.WM_LBUTTONDOWN = 0x0201
        self.WM_LBUTTONUP = 0x0202
        self.WM_RBUTTONDOWN = 0x0204
        self.WM_RBUTTONUP = 0x0205

        # 鼠标虚拟键码 (wParam 参数)
        self.MK_LBUTTON = 0x0001
        self.MK_RBUTTON = 0x0002
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        self.gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

        self.user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
        self.user32.FindWindowW.restype = wintypes.HWND 

        self.user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(RECT))
        self.user32.GetWindowRect.restype = wintypes.BOOL

        self.user32.GetWindowDC.argtypes = (wintypes.HWND,)
        self.user32.GetWindowDC.restype = wintypes.HDC

        self.gdi32.CreateCompatibleDC.argtypes = (wintypes.HDC,)
        self.gdi32.CreateCompatibleDC.restype = wintypes.HDC

        self.gdi32.CreateCompatibleBitmap.argtypes = (wintypes.HDC, ctypes.c_int, ctypes.c_int)
        self.gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP

        self.gdi32.SelectObject.argtypes = (wintypes.HDC, wintypes.HGDIOBJ)
        self.gdi32.SelectObject.restype = wintypes.HGDIOBJ

        self.user32.PrintWindow.argtypes = (wintypes.HWND, wintypes.HDC, wintypes.UINT)
        self.user32.PrintWindow.restype = wintypes.BOOL

        self.gdi32.GetDIBits.argtypes = (wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p, ctypes.POINTER('BITMAPINFO'), wintypes.UINT)
        self.gdi32.GetDIBits.restype = ctypes.c_int

        self.gdi32.DeleteObject.argtypes = (wintypes.HGDIOBJ,)
        self.gdi32.DeleteObject.restype = wintypes.BOOL

        self.gdi32.DeleteDC.argtypes = (wintypes.HDC,)
        self.gdi32.DeleteDC.restype = wintypes.BOOL

        self.user32.ReleaseDC.argtypes = (wintypes.HWND, wintypes.HDC)
        self.user32.ReleaseDC.restype = ctypes.c_int


    def send_key_combination(self, key_code, modifiers=None):
        """
        发送组合键
        :param key_code: 主键码
        :param modifiers: 修饰键列表 [ctrl, shift, alt, win]
        """
        if modifiers is None:
            modifiers = []
        
        # 按下修饰键
        for mod in modifiers:
            win32api.keybd_event(mod, 0, 0, 0)
        
        # 按下主键
        win32api.keybd_event(key_code, 0, 0, 0)
        
        # 释放主键
        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        # 释放修饰键
        for mod in reversed(modifiers):
            win32api.keybd_event(mod, 0, win32con.KEYEVENTF_KEYUP, 0)

    def select_all(self):
        """全选 (Ctrl+A)"""
        self.send_key_combination(ord('A'), [win32con.VK_CONTROL])

    def copy(self):
        """复制 (Ctrl+C)"""
        self.send_key_combination(ord('C'), [win32con.VK_CONTROL])

    def paste(self):
        """粘贴 (Ctrl+V)"""
        self.send_key_combination(ord('V'), [win32con.VK_CONTROL])

    def enter(self):
        """回车 (Enter)"""
        self.send_key_combination(self.VK_RETURN)

    def click_at_position(self,hwnd, client_x, client_y, left=True):
        """
        在指定窗口的客户区坐标 上模拟鼠标左键点击
        """
        if not hwnd:
            print("错误：无效的窗口句柄。")
            return

        lparam_value = client_y << 16 | client_x
        if left:
        # 发送 WM_LBUTTONDOWN 消息
            win32api.SendMessage(
                hwnd, 
                win32con.WM_LBUTTONDOWN, 
                win32con.MK_LBUTTON, # wParam: 表示是左键按下
                lparam_value         # lParam: 包含了坐标信息
            )
        else:
        # 发送 WM_RBUTTONDOWN 消息
            win32api.SendMessage(
                hwnd, 
                win32con.WM_RBUTTONDOWN, 
                win32con.MK_RBUTTON, # wParam: 表示是右键按下
                lparam_value         # lParam: 包含了坐标信息
            )

    def send_click_pywin32(self, hwnd, x, y, left=True):
        """
        使用 pywin32 发送鼠标左键点击消息
        :param hwnd: 目标窗口句柄
        :param x: 客户区相对 x 坐标
        :param y: 客户区相对 y 坐标
        """
        lParam = win32api.MAKELONG(x, y)  # 组合坐标
        if left:
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
            win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lParam)
        else:
            win32gui.SendMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, lParam)
            win32gui.SendMessage(hwnd, win32con.WM_RBUTTONUP, 0, lParam)


    def screenshot_window_by_handle(self, hwnd, save, filename = 'windowshot.png'):
        """
        通过窗口句柄(hwnd)截图，即使窗口被遮挡或最小化。
        """
        if not hwnd:
            print("错误：无效的窗口句柄。")
            return False
        
        # 激活窗口，并渲染        
        self.user32.ShowWindow(hwnd, 9)
        self.user32.SendMessageW(hwnd, 0x000F, 0, 0)
        # 获取窗口尺寸

        rect = RECT()
        if not self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            print(f"获取窗口尺寸失败，错误代码: {ctypes.get_last_error()}")
            return False
            
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        print(f"窗口尺寸: {width}x{height}")

        # 获取窗口的设备上下文 (DC)
        hwnd_dc = self.user32.GetWindowDC(hwnd)
        if not hwnd_dc:
            print(f"获取窗口DC失败，错误代码: {ctypes.get_last_error()}")
            return False

        # 创建一个兼容的内存 DC
        mfc_dc = self.gdi32.CreateCompatibleDC(hwnd_dc)
        if not mfc_dc:
            print(f"创建兼容DC失败，错误代码: {ctypes.get_last_error()}")
            self.user32.ReleaseDC(hwnd, hwnd_dc)
            return False

        # 创建一个兼容的位图
        save_bitmap = self.gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
        if not save_bitmap:
            print(f"创建兼容位图失败，错误代码: {ctypes.get_last_error()}")
            self.gdi32.DeleteDC(mfc_dc)
            self.user32.ReleaseDC(hwnd, hwnd_dc)
            return False

        # 将位图选入内存 DC
        self.gdi32.SelectObject(mfc_dc, save_bitmap)

        # 核心步骤：调用 PrintWindow 将窗口绘制到内存 DC 的位图上
        # PW_RENDERFULLCONTENT 是关键，它可以捕获由 DWM (Desktop Window Manager) 合成的内容
        if not self.user32.PrintWindow(hwnd, mfc_dc, self.PW_RENDERFULLCONTENT):
            print(f"PrintWindow 调用失败，错误代码: {ctypes.get_last_error()}")
            # 清理资源
            self.gdi32.DeleteObject(save_bitmap)
            self.gdi32.DeleteDC(mfc_dc)
            self.user32.ReleaseDC(hwnd, hwnd_dc)
            return False

        # --- 4. 从位图获取像素数据并转换为 PIL Image ---
        
        # 准备 BITMAPINFO 结构来告诉 GetDIBits 我们想要什么格式的数据
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # 负值表示位图是自上而下的
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32     # 32位色，每个像素4字节 (BGRA)
        bmi.bmiHeader.biCompression = 0   # BI_RGB
        
        # 创建一个缓冲区来存储像素数据
        buffer_size = width * height * 4
        pixel_buffer = ctypes.create_string_buffer(buffer_size)
        print(mfc_dc, save_bitmap, 0, height, pixel_buffer, ctypes.byref(bmi), self.DIB_RGB_COLORS)
        # 调用 GetDIBits 将位图数据复制到我们的缓冲区
        try:
            pixels_scanned = self.gdi32.GetDIBits(mfc_dc, save_bitmap, 0, height, pixel_buffer, ctypes.byref(bmi), self.DIB_RGB_COLORS)
        except Exception as e:
            print(e)

        
        if pixels_scanned != height:
            print(f"GetDIBits 未能获取所有像素数据。")
            # 清理资源
            self.gdi32.DeleteObject(save_bitmap)
            self.gdi32.DeleteDC(mfc_dc)
            self.user32.ReleaseDC(hwnd, hwnd_dc)
            return False
        
        # 将 BGRA 缓冲区转换为 Pillow 可以理解的格式
        # Pillow 的 "RGBA" 模式期望的字节顺序是 R, G, B, A
        # Windows DIB 给出的是 B, G, R, A，所以我们需要转换
        image = Image.frombuffer('RGBA', (width, height), pixel_buffer.raw, 'raw', 'BGRA', 0, 1)
        print(save)
        # 保存为文件
        if save:
            image.save(filename)
            print(f"截图已成功保存为 {filename}")

        # --- 5. 清理所有 GDI 对象 ---
        self.gdi32.DeleteObject(save_bitmap)
        self.gdi32.DeleteDC(mfc_dc)
        self.user32.ReleaseDC(hwnd, hwnd_dc)
        return image
    

    def capture_window(self,hwnd, file_path="window_capture.png"):

        if win32gui.IsIconic(hwnd):
            # 如果最小化，先恢复
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
            print("窗口已从最小化恢复")
        # 获取窗口区域
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        if width == 0 or height == 0:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
            time.sleep(0.1) # 等待窗口恢复
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            width = right - left
            height = bottom - top
            if width == 0 or height == 0:
                print("无法获取窗口尺寸，可能窗口不可见或已最小化。")
                return
        
        # 获取窗口设备上下文
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        
        save_dc = mfc_dc.CreateCompatibleDC()
        

        # 创建位图对象
        save_bitmap = win32ui.CreateBitmap()
        save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        
        save_dc.SelectObject(save_bitmap)

        # 如果窗口有硬件加速，可以用PrintWindow代替BitBlt
        # windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
        result = save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
        # 使用BitBlt进行截图
        # result = save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
        
        # 获取位图数据并转为PIL图像
        bmpinfo = save_bitmap.GetInfo()
        bmpstr = save_bitmap.GetBitmapBits(True)
        im = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # 保存图像
        im.save(file_path)
        return im,left,top
        # 清理资源
        win32gui.DeleteObject(save_bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return file_path


    def send_key(self,hwnd, vk_code, is_shift_pressed=False):
        """
        向指定窗口发送一个按键（包括按下和释放）
        :param hwnd: 目标窗口句柄
        :param vk_code: 虚拟键码
        :param is_shift_pressed: 是否需要按下 Shift 键 (用于输入大写或符号)
        """
        if not hwnd:
            print("错误：无效的窗口句柄。")
            return



        # 按下目标键
        print(f"按下键: {vk_code:#x}")
        self.user32.PostMessageW(hwnd, self.WM_KEYDOWN, vk_code, 0)
        time.sleep(0.05)

        # 释放目标键
        print(f"释放键: {vk_code:#x}")
        self.user32.PostMessageW(hwnd, self.WM_KEYUP, vk_code, 0)
        time.sleep(0.05)

    def enum_windows_callback(self, hwnd, lparam):
        """
        EnumWindows 的回调函数，对每个窗口执行此逻辑
        """
        # 检查窗口是否可见
        if self.user32.IsWindowVisible(hwnd):
            # 获取窗口标题长度
            length = self.user32.GetWindowTextLengthW(hwnd) + 1
            if length > 1:
                # 创建缓冲区并获取窗口标题
                buffer = ctypes.create_unicode_buffer(length)
                self.user32.GetWindowTextW(hwnd, buffer, length)
                window_title = buffer.value
                
                # 检查标题是否包含我们查找的关键字
                # global target_keyword # 在回调中使用外部变量
                if target_keyword in window_title:
                    self.found_windows.append({'hwnd': hwnd, 'title': window_title})
                    print(f"  - 找到匹配窗口: 句柄={hwnd:#x}, 标题='{window_title}'")
        
        # 返回 True 继续 EnumWindows 的枚举过程
        # 如果返回 False，枚举将停止
        return True
    
    def find_all_windows_by_keyword(self, keyword):
        """
        通过关键字查找所有可见的、标题包含该关键字的窗口
        """
        WNDENUMPROC = ctypes.WINFUNCTYPE(
                        wintypes.BOOL,
                        wintypes.HWND,      # lParam
                        wintypes.LPARAM     # lParam
                    )

        global target_keyword
        target_keyword = keyword
        
        print(f"正在搜索标题包含 '{keyword}' 的窗口...")
        
        # 清空之前的结果
        self.found_windows.clear()
        
        # 创建回调函数的 ctypes 可调用实例
        callback_func = WNDENUMPROC(self.enum_windows_callback)
        
        # 调用 EnumWindows，开始枚举
        self.user32.EnumWindows(callback_func, 0)
        
        if not self.found_windows:
            print("没有找到匹配的窗口。")
        else:
            print(f"\n共找到 {len(self.found_windows)} 个匹配的窗口。")
        
        return self.found_windows
    
    def send_mouse_wheel_up(self,hwnd, x=0, y=0, delta=120):
        """
        向指定窗口发送鼠标滚轮上滑消息（WM_MOUSEWHEEL）
        :param hwnd: 目标窗口句柄
        :param x: 鼠标x坐标（屏幕坐标）
        :param y: 鼠标y坐标（屏幕坐标）
        :param delta: 滚动量，正数向上，负数向下，默认120（WHEEL_DELTA）
        """
        # wParam: 高位为滚动量，低位为按键状态（默认无按键）
        wParam = win32api.MAKELONG(0, delta)
        # lParam: 鼠标位置（低位x，高位y）
        lParam = win32api.MAKELONG(x, y)
        win32api.SendMessage(hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)


    def activate_window(self,hwnd):
        # if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        # else:
        #     win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    
        # 设置为前台窗口
        win32gui.SetForegroundWindow(hwnd)



    def get_window_coordinates(self,hwnd):
        """
        根据窗口句柄hwnd输出窗口坐标信息
        :param hwnd: 目标窗口句柄
        """
        # 获取窗口在屏幕上的矩形区域（包括边框、标题栏等）
        window_rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = window_rect
        window_width = right - left
        window_height = bottom - top

        # 获取窗口客户区左上角在屏幕上的坐标
        client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))

        # 获取客户区大小
        client_rect = win32gui.GetClientRect(hwnd)
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]

        
        # print("窗口坐标信息：")
        # print(f"  窗口左上角屏幕坐标：({left}, {top})")
        # print(f"  窗口右下角屏幕坐标：({right}, {bottom})")
        # print(f"  窗口宽度：{window_width}, 高度：{window_height}")
        # print(f"  客户区左上角屏幕坐标：({client_left}, {client_top})")
        # print(f"  客户区宽度：{client_width}, 高度：{client_height}")

        return left, top
    

    def send_char_pywin32(self,hwnd, char_code):
        """
        使用 PyWin32 发送字符到指定窗口
        :param hwnd: 目标窗口句柄
        :param char_code: 要发送的字符的 Unicode 码点
        """
        # 发送 WM_CHAR 消息
        win32api.SendMessage(hwnd, win32con.WM_CHAR, ord(char_code), 0)
    
    def send_enter_pywin32(self,hwnd):
        """
        使用 PyWin32 发送 Enter 键到指定窗口
        :param hwnd: 目标窗口句柄
        """
        # 发送 WM_KEYDOWN 消息
        win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        # 发送 WM_KEYUP 消息
        win32gui.SendMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)


    def capture_win_alt(self,hwnd:int=None, jpgFileName='hwnd.png', program_windowTitle='微信'):
        windll.user32.SetProcessDPIAware()
        if not hwnd:
            hwnd = win32gui.FindWindow(None, program_windowTitle)
        if not hwnd:
            return None

        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        w = right - left
        h = bottom - top

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, w, h)
        save_dc.SelectObject(bitmap)

        result = windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo["bmHeight"], bmpinfo["bmWidth"], 4))
        img = np.ascontiguousarray(img)[..., :-1]  # drop alpha

        if not result:
            raise RuntimeError(f"Unable to acquire screenshot! Result: {result}")

        cv2.imwrite(jpgFileName, img)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(img_rgb)
    
        return pil_image
        


    def scroll_window(self,hwnd, scroll_delta=100, mouse_pos=(100, 300)):
        """
        给窗口发送滚轮消息
        
        Args:
            hwnd: 窗口句柄
            scroll_delta: 滚动量，正数向上滚，负数向下滚
                        Windows标准是每次滚动120单位（1格）
        """
        # 构造滚轮消息
        # WM_MOUSEWHEEL = 0x020A
        # 滚动值需要放在高位，所以要左移16位
        
        wParam = (scroll_delta << 16) & 0xFFFFFFFF
        
        # 获取窗口位置
        rect = win32gui.GetWindowRect(hwnd)
        x = mouse_pos[0]  # 窗口中心X坐标
        y = mouse_pos[1]  # 窗口中心Y坐标
        
        # lParam = Y坐标(高16位) | X坐标(低16位)
        lParam = (y << 16) | (x & 0xFFFF)
        
        # 发送消息
        win32api.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)



