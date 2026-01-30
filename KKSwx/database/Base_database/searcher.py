
class Searcher():
    def __init__(
        self,
        path:str,
        database:str = '',
        query:dict = {}
    ):
        self.path = path
        self.database = database
        self.query = query

    #检测是否能够连接数据库
    def connection(self):
        pass
    
    def get_path(self):
        return self.path
    

    def get_database(self):
        return self.database
        
    def chunk_insert(self, index:str,data:dict):
        pass

    def chunk_search(self, index:str, question:str):
        pass

# a = Searcher(path='http://localhost:9200', database='elasticsearch')
# print(a.connection())