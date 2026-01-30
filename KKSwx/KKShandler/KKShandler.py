from database.mysql_manager import MYSQL_Manage
from autoqueue.redisMq import RedisQueue
import json

class KKSHandler():
    def __init__(self):
        self.Mysql_user = 'root'
        self.Mysql_passwords = '123456'
        self.Mysql_database_name = None
        self.monitor_name = None
        self.Mysql_client = MYSQL_Manage(username = self.Mysql_user, passwords=self.Mysql_passwords, database_name=self.Mysql_database_name,table_name =self.monitor_name)

    def get_check_point(self):
        mysql = self.Mysql_client
        mysql.init_table({'user':'', 'content':''})
        local_history = mysql.query_database(limit=5)
        return local_history
    
    
    def add_queue(self, queue:RedisQueue, data):
        for r in data:
            if queue.qsize() >= 50:
                break
            queue.rput(json.dumps((r[0],r[1])))
        return True
    

    def find_sam(self, queue:RedisQueue, data):
        for index, r in enumerate(data[self.judge_len:]):
            moniter = json.loads(queue.get_data(2))
            if r[0] == moniter[0] and r[1] == moniter[1]:
                moniter1 = json.loads(queue.get_data(1))
                moniter2 = json.loads(queue.get_data(0))
                if data[index-1][0] == moniter1[0] and data[index-1][1] == moniter1[1] and data[index-2][0] == moniter2[0] and data[index-2][1] == moniter2[1]:
                    [queue.rput(json.dumps((data[i][0], data[i][1]))) for i in range(index+1, len(data))]
                    return True
        return False


    def get_Mysql(self):
        return self.Mysql_client