import json
import os


class Configuration:

    def __init__(self):
        self.data = {
            "test": True,
            "secret_key": "1234"
        }

    def load(self, path):
        with open(path, "rb") as file:
            self.data = json.load(file)

    def __getitem__(self, key):
        return self.data[key] if key in self.data else None


config_object = Configuration()


def get_config(key: str):
    return config_object[key]


def get_config_object():
    return config_object


def initialize(project_root):
    config_file_path = os.path.join(project_root, "configurations", "config.json")

    if os.path.exists(config_file_path):
        config_object.load(config_file_path)


if __name__ == '__main__':
    initialize(os.path.join(".."))
    print(get_config("data_path"))
