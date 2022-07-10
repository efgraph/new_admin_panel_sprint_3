import abc
import json
import os.path


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state):
        pass

    @abc.abstractmethod
    def retrieve_state(self):
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.exists(self.file_path):
            file = open(self.file_path, 'w+')
            file.write('{}')
            file.close()

    def save_state(self, state):
        curr = self.retrieve_state()
        with open(self.file_path, 'w') as fs:
            json.dump(curr | state, fs)

    def retrieve_state(self):
        with open(self.file_path) as fs:
            data = json.load(fs)
        return data


class State:
    def __init__(self, storage: BaseStorage):
        self.storage = storage

    def set_state(self, key, value):
        self.storage.save_state({key: value})

    def get_state(self, key: str):
        state = self.storage.retrieve_state()
        return state.get(key)
