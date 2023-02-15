import os
import aiofiles
import json


class Content_source:

    def __init__(self, meta_data, case_path):
        protocol = meta_data["protocol"]
        if protocol["source"] == "static":
            self.loader_type = "filesystem"
            self.case_path = case_path
            self.paths = protocol["paths"]

    async def __getitem__(self, index):
        if self.loader_type == "filesystem":
            async with aiofiles.open(os.path.join(self.case_path, self.paths[index]), mode='r') as f:
                contents = await f.read()
            data = json.loads(contents)
        return data

    def __len__(self):
        if self.loader_type == "filesystem":
            return len(self.paths)
        return -1
