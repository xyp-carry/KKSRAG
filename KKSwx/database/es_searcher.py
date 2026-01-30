from elasticsearch import Elasticsearch
from database.Base_database.searcher import Searcher
from elasticsearch import helpers


class ES_Search(Searcher):
    def __init__(
            self, 
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.client = Elasticsearch(self.path)
        self.query = self.init_query(self.query['range'] if self.query.get('range', False) else {})

    def init_query(self,time_range = {}):
        query = {
                    "query": {
                        "bool": {
                        "must": [
                            {
                            "match": {
                                "content": "question"
                            }
                            },
                            
                        ],
                        "must_not": [],
                        "should": []
                        }
                    },
                    "from": 0,
                    "size": 10,
                    "sort": [],
                    "aggs": {}
                    }
        if len(time_range) != 0:
            time_stramp={
                {
                    "range": {
                        "timestamp": {
                        "gte": time_range['gte'],
                        "lte": time_range['lte']
                        }
                    }
                    }
            }
            query['query']['must'].append(time_stramp)
        
        return query
    
    
    def connection(self):
        if self.client.ping():
            print( "✓ ping测试成功")
            return True
        else:
            raise ValueError(f'无法连接elasticsearch,请确认{self.path}是否有效')
    
    #插入知识块(该部分需要增加检测机制)
    def chunk_insert(self, index:str, data:list[dict]):
        if len(data) == 1:
            self.client.index(index = index, document=data)
        elif len(data) > 1:
            actions = [{"_index":index,"_source": item} for item in data]
            helpers.bulk(self.client, actions)

    #获取有哪些知识库
    def get_index(self):
        return [index for index in self.client.indices.get(index = "*")]
    

    #进行知识块搜索
    def chunk_search(self, index:str, question:str):
        docs = []
        ids = []
        query = self.query
        response = self.client.search(index=index, body=query)
        if response['hits']['total']['value'] <= 10:
            for doc in response['hits']['hits']:
                docs.append(doc['_source']['content'])
                ids.append(doc['_id'])
        else:
            for i in range(10):
                docs.append(response['hits']['hits'][i]['_source']['content'])
                ids.append(response['hits']['hits'][i]['_id'])
        return ids, docs


    def create_index(self, index:str='test', settings:dict={}):
        if settings == {}:
            settings= {
            "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                },"mappings": {
                "properties": {
                "content": {
                    "type": "text"
                },
                "createdate": {
                    "type": "date"
                }
                }
            }
            }

        self.client.indices.create(index=index, body=settings)



