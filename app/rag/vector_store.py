import faiss
import numpy as np

class FAISSVectorStore:
    def __init__(self,dimension):
        """
        初始化向量库
        """
        self.index = faiss.IndexFlatIP(
            dimension
        )

    def add(self,vectors):
        """
        添加向量
        """
        vectors = np.array(
            vectors,
            dtype=np.float32
        )
        faiss.normalize_L2(vectors)
        self.index.add(vectors)

    def search(self,query_vector,top_k):
        """
        传入query向量并找寻最相似的向量
        :param query_vector: 问题向量
        :param top_k: 返回结果
        :return: scores和ids
        """
        top_k = min(
            top_k,
            self.index.ntotal
        )
        query_vector = np.array(
            query_vector,
            dtype=np.float32
        )
        faiss.normalize_L2(query_vector)
        scores, ids = self.index.search(
            query_vector,
            top_k
        )
        return scores, ids

    def save(self,path):
        """
        将内存中的FAISS索引保存到硬盘
        :param path: 写入路径
        :return:
        """
        faiss.write_index(
            self.index,
            path
        )

    @classmethod
    def load(cls,path):
        """
         从硬盘加载FAISS索引并恢复向量库对象
        :param path: 读取文件的路径
        :return: 读取的index内容
        """
        store = cls.__new__(cls)
        store.index=faiss.read_index(path)
        return store
