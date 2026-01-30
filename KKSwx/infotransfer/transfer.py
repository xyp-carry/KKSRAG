
import threading
from autoqueue.redisMq import RedisQueue
import keyboard

class transfer():
    def __init__(
            self, 
            _async:bool = True
        ):
        self.length = 0
        self._async = _async

    def start(self, queues:list[RedisQueue], DChandler, quit_hotkey = 'ctrl+alt+p'):
        monitor_thread = threading.Thread(target=self.monitor, args=(queues,DChandler,))
        self.stop_event = threading.Event()
        keyboard.add_hotkey(quit_hotkey, self.cleanup,args=[queues])
        monitor_thread.start()
    
    def monitor(self, queues:list[RedisQueue], DChandler):
        num = 0
        self.length = [0 for i in range(len(queues))]
        while not self.stop_event.is_set():
            if num >= len(queues):
                num = 0
            length = queues[num].qsize()
            while length > self.length[num]:
                data = queues[num].get_data(self.length[num])
                print(data.decode('utf-8'))
                if data:
                    if data.decode('utf-8') == '好偏':
                        DChandler.send_text("你好，为什么不回我消息")

                self.length[num] += 1
            num += 1

    def cleanup(self, wxqueues:RedisQueue):
        self.stop_event.set()
        print("执行优雅退出后端...")
        return 