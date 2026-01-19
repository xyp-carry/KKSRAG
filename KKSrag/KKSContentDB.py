from .KKStool import KKSTokenizer, KKSEmbedding

import sqlite3
import struct
import numpy as np
import json
import math





class KKSContentDB:
    def __init__(
        self,
        hanlpTokenizer,
        db_path="db/ad_content.db",
        Embedding: KKSEmbedding = None,
    ):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.embedding = Embedding
        self.cursor.execute(
            f"""
                        CREATE TABLE IF NOT EXISTS items (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            content TEXT NOT NULL,
                            embedding BLOB,
                            keywords TEXT NOT NULL
                        )
                        """
        )
        self.conn.commit()
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS keyword_index (
                    keyword TEXT PRIMARY KEY, 
                    item_ids TEXT NOT NULL
                );"""
        )
        self.conn.commit()
        self.maxnum = self.get_max()
        self.num = self.get_num()
        self.hanlpTokenizer: KKSTokenizer = hanlpTokenizer

    def get_embedding(self):
        self.cursor.execute("SELECT id, content FROM items WHERE embedding is null")
        if len(self.cursor.fetchall()) > 0:
            return True
        return False

    def init_embedding(self):
        self.cursor.execute("SELECT id, content FROM items WHERE embedding is null")
        for row in self.cursor.fetchall():
            id, content = row
            ad_embedding = self.embedding.get_embedding(content)
            self.cursor.execute(
                "UPDATE items SET embedding = ? WHERE id = ?",
                (self.array_to_blob(ad_embedding), id),
            )
            self.conn.commit()

    def get_num(self):
        self.cursor.execute("SELECT count(*) FROM items")
        result = self.cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_max(self):
        self.cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='items'")
        result = self.cursor.fetchone()
        return result[0] if result is not None else 0

    def array_to_blob(self, float_array):
        """将浮点数列表/NumPy数组转换为二进制数据"""
        return struct.pack("f" * len(float_array), *float_array)

    def blob_to_array(self, blob_data):
        """将二进制数据解包回浮点数列表"""
        fmt = "f" * (len(blob_data) // 4)
        return list(struct.unpack(fmt, blob_data))

    def close(self):
        self.conn.close()

    def get_freq(self):
        """获取关键词频率"""
        self.cursor.execute("SELECT * FROM keyword_index")
        rows = self.cursor.fetchall()
        freq_dict = {}
        for row in rows:
            keyword = row[0]
            countlist = json.loads(row[1])
            freq_dict[keyword] = countlist
        return freq_dict

    def refresh_freq(self):
        """刷新关键词频率"""
        self.cursor.execute("DELETE FROM keyword_index")
        self.conn.commit()
        self.cursor.execute("SELECT id, keywords FROM items")
        rows = self.cursor.fetchall()
        freq_dict = {}
        for row in rows:
            for keyword in json.loads(row[1]):
                if freq_dict.get(keyword, False):
                    freq_dict[keyword].append(row[0])
                else:
                    freq_dict[keyword] = [row[0]]
        self.cursor.executemany(
            "INSERT INTO keyword_index (keyword, item_ids) VALUES (?, ?)",
            [(keyword, json.dumps(freq_dict[keyword])) for keyword in freq_dict.keys()],
        )
        self.conn.commit()        
        return freq_dict
    
    def split_contents(self, contents):
        """将广告内容、embedding和关键词列表拆分为单独的元素"""
        insertcontents = []
        ad_keywords = self.hanlpTokenizer.hanlpTokenizer(contents)
        if self.embedding:
            ad_embedding = self.embedding.embed_documents(contents)          
            [insertcontents.append((content, ad_keywords, ad_embedding)) for content, ad_keywords, ad_embedding in zip(contents, ad_keywords, ad_embedding)]
        else:
            [insertcontents.append((content, ad_keywords)) for content, ad_keywords in zip(contents, ad_keywords)]
        return insertcontents

    def insert_ad(self, contents):
        """插入内容、embedding和关键词"""
        print("embedding contents")
        insertcontents = self.split_contents(contents)
        print("insert contents")
        if self.embedding:
            data_to_insert = [
                (ad_content, self.array_to_blob(ad_embedding), json.dumps(ad_keywords))
                for ad_content, ad_keywords, ad_embedding in insertcontents
            ]
        else:
            data_to_insert = [
                (ad_content, json.dumps(ad_keywords))
                for ad_content, ad_keywords in insertcontents
            ]
        
        if self.embedding:
            self.cursor.executemany(
                "INSERT INTO items (content, embedding, keywords) VALUES (?, ?, ?)",
                data_to_insert,
            )
        else:
            self.cursor.executemany(
                "INSERT INTO items (content, keywords) VALUES (?, ?)",
                data_to_insert,
            )
        self.conn.commit()
        print("over and refresh freq")
        self.refresh_freq()
        print("all over")

    def delete_ad(self, content_list: list):
        """删除广告"""
        for content in content_list:
            self.cursor.execute(f"DELETE FROM items WHERE id = {content['id']}")
            self.conn.commit()
        self.refresh_freq()

    def get_tf_idf(self, content: list | str, querywords, result):
        """计算TF-IDF"""
        if isinstance(content, str):
            contentwords = self.hanlpTokenizer.hanlpTokenizer(content)
        else:
            contentwords = content
        tf_idf = []
        for queryword in querywords:
            tf = contentwords.count(queryword) / len(contentwords)
            idf = math.log(self.num / (1 + result[queryword]))
            tf_idf.append(tf * idf)
        return tf_idf

    def query(self, query):
        import time
        print("begin split query")
        start = time.time()
        querywords = list(set(self.hanlpTokenizer.hanlpTokenizer(query)[0]))
        end = time.time()
        print(end - start)

        result = {"keywords": []}
        print("begin get freq")
        start = time.time()
        for queryword in querywords:
            self.cursor.execute(
                "SELECT item_ids FROM keyword_index WHERE keyword = ?",
                (queryword,),
            )
            row = self.cursor.fetchone()
            if row:
                result[str(queryword)] = len(json.loads(row[0]))
                result["keywords"] = result["keywords"] + json.loads(row[0])
            else:
                result[str(queryword)] = 0
        end = time.time()
        print(end - start)
        query_id_list = list(set(result["keywords"]))
        print("begin get data")
        if self.embedding:
            self.cursor.execute(
                "SELECT content, keywords, id, embedding FROM items WHERE id IN ({})".format(
                    ",".join(map(str, query_id_list))
                )
            )
        else:
            self.cursor.execute(
                "SELECT content, keywords, id FROM items WHERE id IN ({})".format(
                    ",".join(map(str, query_id_list))
                )
            )
        rows = self.cursor.fetchall()
        

        # 代码冗余 本来就已经有分词了 需要考虑设计问题

        print("begin compute data")
        if self.embedding:
            contents = [(row[0], json.loads(row[1]), row[2], self.blob_to_array(row[3])) for row in rows]
            selfscore = self.get_tf_idf(querywords, querywords, result)
            embedding = self.embedding.get_embedding(query)
            score = [
                (
                    self.get_tf_idf(content[1], querywords, result),
                    content[0],
                    content[1],
                    content[2],
                    np.dot(np.array(embedding), np.array(content[3])),
                )
                for content in contents
            ]
            res = sorted(
                [
                    (np.dot(np.array(s[0]), np.array(selfscore)), s[1], s[2], s[3], s[4])
                    for s in score
                ],
                key=lambda x: x[0],
                reverse=True,
            )
            return sorted(res, key=lambda x: x[4], reverse=True)
        else:
            contents = [(row[0], json.loads(row[1]), row[2]) for row in rows]
            selfscore = self.get_tf_idf(querywords, querywords, result)
            score = [
                (
                    self.get_tf_idf(content[1], querywords, result),
                    content[0],
                    content[1],
                    content[2],
                )
                for content in contents
            ]
            return sorted(
                [
                    (np.dot(np.array(s[0]), np.array(selfscore)), s[1], s[2], s[3])
                    for s in score
                ],
                key=lambda x: x[0],
                reverse=True,
            )

    def select_ad(self, page_size: int = 0, offset: int = 0):
        if self.embedding:
            sql = f"SELECT id, content, keywords, embedding FROM items order by id {f'LIMIT {page_size}' if page_size != 0 else ''} {f'OFFSET {offset}' if page_size != 0 else ''}"
        else:
            sql = f"SELECT id, content, keywords FROM items order by id {f'LIMIT {page_size}' if page_size != 0 else ''} {f'OFFSET {offset}' if page_size != 0 else ''}"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return [
            {"ID": row[0], "content": row[1], "keywords": json.loads(row[2])}
            for row in rows
        ]

    def select_ad_by_keywords(self):
        """根据关键词查询广告"""
        self.cursor.execute("SELECT * FROM keyword_index")
        rows = self.cursor.fetchall()
        for row in rows:
            print(f"keyword: {row[0]}, list: {json.loads(row[1])}")

