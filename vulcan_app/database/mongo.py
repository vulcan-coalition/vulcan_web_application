from pymongo import MongoClient, DESCENDING, ASCENDING


class Mongo:
    def __init__(self, url, database):
        self.client = MongoClient(url)
        self.database = database

    def get_session(self):
        return self.client[self.database]
