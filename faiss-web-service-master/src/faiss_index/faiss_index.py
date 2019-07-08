import faiss
import numpy as np
import MySQLdb

class FaissIndex(object):

    def __init__(self, index, id_to_vector,db_name):
        assert index
        assert id_to_vector
        assert db_name

        self.index = index
        self.id_to_vector = id_to_vector
        self.db_name = db_name

    def search_by_ids(self, ids, k):
        vectors = [self.id_to_vector[id_] for id_ in ids]
        results = self.__search__(ids, vectors, k + 1)

        return results

    def search_by_vectors(self, vectors, k):
        ids = [None] * len(vectors)
        results = self.__search__(ids, vectors, k)

        return results

    def __search__(self, ids, vectors, k):
        def neighbor_dict(id_, score):
            return { 'id': str(id_), 'score': float(score) }

        def result_dict( vector, neighbors):
            return { 'vector':vector.tolist(), 'neighbors': neighbors }

        vectors = [np.array(vector, dtype=np.float32) for vector in vectors]
        vectors = np.atleast_2d(vectors)

        db = MySQLdb.connect('192.168.99.1', port=3306, user='root', password='12345678', db=self.db_name, charset='utf8')
        cursor = db.cursor()

        scores, neighbors = self.index.search(vectors, k) if vectors.size > 0 else ([], [])
        results = []
        for id_, vector, neighbors, scores in zip(ids, vectors, neighbors, scores):
            neighbors_scores = zip(neighbors, scores)
            neighbors_scores = [(n, s) for n, s in neighbors_scores if n != id_ and n != -1]
            # neighbors_scores = [neighbor_dict(n, s) for n, s in neighbors_scores]
            neighbors_scores2=[]
            for n, s in neighbors_scores:
                cursor.execute('select id from feature where mysql_id=%s' % n)
                id = cursor.fetchone()[0]
                neighbors_scores2.append(neighbor_dict(id, s))
            results.append(result_dict(vector,neighbors_scores2))
        return results
