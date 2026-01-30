import pandas as pd
from sympy import N
from sqlalchemy import create_engine
import json

class Manager():
    
    def __init__(self):
        pass


    def switch_format(self, data:list[dict],format:list = []):
        if isinstance(data, list) == False:
            raise TypeError('数据必须为list[dict]')
        
        # def to_str(data):
        #     string = ''
        #     for key in data:
        #         string += str(key) + ':' + str(data[key]) 
        Output = [{
            'content':json.dumps(d, ensure_ascii=False),
            'createdate':d['created']} for d in data]

        return Output
    


    def get_format(self):
        return ['content']
            



a = Manager()
# print(a.switch_format(data=[{'content':1},{'content':2}]))

