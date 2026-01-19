import hanlp
import os
import pandas as pd
from langchain_huggingface import HuggingFaceEmbeddings
import string
import torch
# from FlagEmbedding import BGEM3FlagModel


class KKSTokenizer:
    def __init__(self, stopwords_path="tokenizer"):
        self.FinegrainedTokenizer = hanlp.load(
            hanlp.pretrained.tok.FINE_ELECTRA_SMALL_ZH
        )
        self.CoarsegrainedTokenizer = hanlp.load(
            hanlp.pretrained.tok.COARSE_ELECTRA_SMALL_ZH
        )
        self.stopwords = self.load_stopwords_from_txt(stopwords_path)

    def hanlpTokenizer(self, text):
        """
        对文本进行hanlp分词
        :param text: 输入文本
        :return: 分词结果列表
        """
        fine_tokens = self.FinegrainedTokenizer(text)
        coarse_tokens = self.CoarsegrainedTokenizer(text)
        
        if isinstance(text, list):
            Output = []
            tokenslist = [list(set(fine_tokens[i] + coarse_tokens[i])) for i in range(len(fine_tokens))]
            for tokens in tokenslist:
                Output.append([token.translate(str.maketrans('', '', string.punctuation)) for token in tokens if token not in self.stopwords])
            return Output
        elif isinstance(text, str) :
            tokenslist = list(set(fine_tokens + coarse_tokens))
            return [[token.translate(str.maketrans('', '', string.punctuation)) for token in tokenslist if token not in self.stopwords]]

    def load_stopwords_from_txt(self, file_path="tokenizer"):
        def load_stopwords_from_txt(file):
            """
            从txt文件加载停用词
            :param file_path: txt文件路径
            :return: 停用词集合
            """
            stopwords = set()
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:  # 忽略空行
                        stopwords.add(word)
            return stopwords

        current = set()
        for i in os.listdir(file_path):
            if i.endswith(".txt"):
                current = current | load_stopwords_from_txt(file_path + "/" + i)

        return current


class FileReader:
    def __init__(self):
        pass

    def read_excel(self, file_path):
        """
        从excel文件读取数据
        :param file_path: excel文件路径
        :return: 数据框
        """
        data = pd.read_excel(file_path)
        if "content" in data.columns:
            return data["content"].tolist()
        else:
            return data[data.columns[0]].tolist()


class KKSEmbedding:
    def __init__(self, model_name="BAAI/bge-m3"):
        if torch.cuda.is_available():
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name, model_kwargs={'device': 'cuda'})
        else:
            self.embeddings = HuggingFaceEmbeddings(model_name=model_name)

    def get_embedding(self, text):
        """
        获取文本的embedding
        :param text: 输入文本
        :return: 文本的embedding向量
        """
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, documents):
        """
        获取文档的embedding
        :param documents: 输入文档列表
        :return: 文档的embedding向量列表
        """
        return self.embeddings.embed_documents(documents)
    