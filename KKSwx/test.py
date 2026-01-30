# 示例
from KKShandler.KKSwx import KKSWx

KKSwx = KKSWx()


"""获取指定窗口的历史记录"""
hwnd = KKSwx.phandler.find_all_windows_by_keyword("robot_test")[0]['hwnd']
history = KKSwx.get_history(hwnd, roll_times=5)
print(history)


"""发送文本到指定窗口"""
KKSwx.send_text(hwnd, '你好')



"""监测指定窗口的新消息，键盘输入ctrl+alt+q退出"""
wxqueue = [[]]
KKSwx.start(wxqueues= wxqueue,name=['robot_test'])

