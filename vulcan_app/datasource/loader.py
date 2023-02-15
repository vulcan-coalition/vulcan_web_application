import csv
from pydantic import BaseModel
import random
import os
from datetime import date
import time
import record
from configuration import get_config
import httpx
import zlib


dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(dir_path, "data")
ground_truth_path = os.path.join(dir_path, "ground_truth")
labels = {}
last_touch = "20000101"


def vulcan_hash(data):
    return zlib.adler32(bytearray(data, "utf8"))


class Data:
    def __init__(self):
        self.data_service_address = get_config()["data_service_address"]
        self.iterative_sampling = get_config()["iterative_sampling"]
        self.data_service_token = get_config()["data_service_token"]
        self.cache = {}
        self.content = []
        if self.data_service_address:
            self.remote = not get_config()["data_preload"]
            self.remote_submit = True
            print("System type: Remote", self.remote, "Remote submission", self.remote_submit)
            if self.data_service_token is not None:
                self.header = {'Authorization': 'Bearer ' + self.data_service_token}
            else:
                self.header = {}
        else:
            self.remote = False
            self.remote_submit = False
            print("System type: Remote False.")
        self.percent_ground_truth = 0.05

    def record_question(self, question_id, question):
        self.cache[question_id] = question

    def check_test(self):
        return random.random() < self.percent_ground_truth

    def get_next(self, prev_key):
        if self.remote:
            return self.__next__()
        else:
            if self.iterative_sampling:
                key = (int(prev_key) + 1) % len(self.content)
                return self.__getitem__(key)
            else:
                return self.__next__()

    def __next__(self):
        # this function represent next(this)
        if self.remote and not self.check_test():
            response = httpx.get(self.data_service_address + '/question', headers=self.header)
            data = response.json()
            self.record_question(data["question_id"], data["question"])
            return data["question_id"], data["question"], None
        else:
            choice = random.randint(0, len(self.content) - 1)
            # if the client sends integer id, test may not be issued.
            if choice in self.cache:
                return choice, self.cache[choice], None
            c = self.content[choice]
            return choice, c[1], c

    def __getitem__(self, key):
        # this function represent this[key]
        if self.remote:
            response = httpx.get(self.data_service_address + '/question?question_id=' + key, headers=self.header)
            data = response.json()
            self.record_question(data["question_id"], data["question"])
            return data["question_id"], data["question"], None
        else:
            c = self.content[key]
            return key, c[1], c

    def __len__(self):
        return -1 if self.content is None else len(self.content)

    def reload(self, sub_dir):
        if self.remote:
            self.content.clear()
            all_ground_truth = set()
            for item in os.listdir(ground_truth_path):
                if item.endswith(".csv"):
                    with open(os.path.join(ground_truth_path, item), 'r', encoding="utf8") as csv_file:
                        csv_reader = csv.reader(csv_file, delimiter=',')
                        next(csv_reader, None)
                        for row in csv_reader:
                            all_ground_truth.add(row[1])
            all_ground_truth = list(all_ground_truth)

            for i, gtq in enumerate(all_ground_truth):
                self.content.append(("benchmark", gtq, None, ""))

        else:
            self.content.clear()

            all_ground_truth = set()
            for item in os.listdir(ground_truth_path):
                if item.endswith(".csv"):
                    with open(os.path.join(ground_truth_path, item), 'r', encoding="utf8") as csv_file:
                        csv_reader = csv.reader(csv_file, delimiter=',')
                        next(csv_reader, None)
                        for row in csv_reader:
                            all_ground_truth.add(row[1])
            all_ground_truth = list(all_ground_truth)

            for p in os.listdir(sub_dir):
                if "category" in p or not p.endswith(".csv"):
                    continue

                with open(os.path.join(sub_dir, p), 'r', encoding="utf8") as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    title_row = next(csv_reader, None)
                    try:
                        sentence_index = ["sentence" in x for x in title_row].index(True)
                    except ValueError:
                        sentence_index = 1

                    try:
                        id_index = ["id" in x for x in title_row].index(True)
                    except ValueError:
                        id_index = 0

                    for row in csv_reader:
                        aux = row[2] if len(row) > 2 else ""
                        if len(row) > 1:
                            self.content.append((p, row[sentence_index], row[id_index], aux))
                        else:
                            self.content.append((p, row[sentence_index], "", ""))

            total_valid_data = len(self.content)
            for i in range(min(round(total_valid_data * self.percent_ground_truth), len(all_ground_truth))):
                self.content.insert(random.randint(0, total_valid_data), ("benchmark", all_ground_truth[i], None, ""))

    async def submit(self, question_id, answer, user_email, user_disability):
        if self.remote_submit and question_id in self.cache:
            question = self.cache[question_id]
            case = ""
            data = {
                "question_id": question_id,
                "answer": answer
            }
            try:
                hashed_id = vulcan_hash(user_email)
                httpx.post(self.data_service_address + '/answer?user_id=' + str(hashed_id), json=data, headers=self.header)
            except httpx.HTTPError:
                print("Error while submitting answer.")
        else:
            question_id = int(question_id)
            question = self.content[question_id][1]
            case = self.content[question_id][0]

        await record.dump(user_email, user_disability, question, case, answer)


data = Data()


def check():
    so_far = last_touch
    for item in os.listdir(data_path):
        sub_dir = os.path.join(data_path, item)
        if item > so_far and os.path.isdir(sub_dir):
            so_far = item
    return so_far


def reload():
    sub_dir = os.path.join(data_path, last_touch)
    print("loading new dataset:", sub_dir)

    data.reload(sub_dir)

    labels.clear()
    with open(os.path.join(sub_dir, 'category.csv'), 'r', encoding="utf8") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        label_version = get_config()["label_format_version"] if "label_format_version" in get_config() else 1
        if label_version == 2:
            for row in csv_reader:
                abbreviation = row[0]
                identifier = row[1]
                category = row[2]
                category_detail = row[3]
                subcategory = row[4]
                subcategory_detail = row[5]
                subsubcategory = row[6]
                subsubcategory_detail = row[7]
                code = row[8]
                color = row[9]
                examples = [row[10], row[11], row[12]]

                if category not in labels:
                    labels[category] = {"category": category, "detail": category_detail, "children": {}}
                if subcategory not in labels[category]["children"]:
                    labels[category]["children"][subcategory] = {"category": subcategory, "detail": subcategory_detail, "children": {}}
                if subsubcategory not in labels[category]["children"][subcategory]["children"]:
                    labels[category]["children"][subcategory]["children"][subsubcategory] = {"category": subsubcategory, "detail": subsubcategory_detail, "identifier": identifier, "code": code, "color": color, "examples": examples}
        else:
            for row in csv_reader:
                abbreviation = row[0]
                identifier = row[1]
                category = row[2]
                thai = row[3]
                category_detail = row[4]
                subcategory = row[5]
                subcategory_detail = row[6]
                subcategory_code = row[7]
                subcategory_color = row[8]
                examples = [row[9], row[10], row[11]]

                if category not in labels:
                    labels[category] = {"abbreviation": abbreviation, "title": category, "thai": thai, "description": category_detail, "subcategories": []}
                labels[category]["subcategories"].append({"title": subcategory, "code": subcategory_code, "color": subcategory_color, "description": subcategory_detail, "examples": examples, "identifier": identifier})


def check_and_reload_data():
    global last_touch
    touch = check()
    if touch == last_touch:
        return
    last_touch = touch
    reload()


def parse_question_id(question_id):
    tokens = question_id.split("_")
    sub_id = "_".join(tokens[1:])
    return tokens[0], sub_id


def get_question(prev_question_id=None):
    check_and_reload_data()
    if prev_question_id:
        touch, key = parse_question_id(prev_question_id)
        if touch == last_touch:
            sub_id, question, _ = data.get_next(key)
            return {"question": question, "question_id": last_touch + "_" + str(sub_id)}
    sub_id, question, _ = next(data)
    return {"question": question, "question_id": last_touch + "_" + str(sub_id)}


def get_labels():
    check_and_reload_data()
    return labels


class Answer(BaseModel):
    question_id: str
    answer: str


async def post_answer(answer, user_email, user_disability):
    touch, sub_id = parse_question_id(answer.question_id)
    if touch == last_touch:
        await data.submit(sub_id, answer.answer, user_email, user_disability)


check_and_reload_data()

if __name__ == '__main__':
    assert zlib.adler32(bytearray("aaa", "utf8")) == 38338852, "HASH has changed."
    print(get_question())
    print(get_labels())

    assert(post_answer(Answer(**{"question_id": last_touch + "_0", "answer": "BLA_00"}), "unittest_user@lab.ai") > 0)
    assert(post_answer(Answer(**{"question_id": "20000101_0", "answer": "BLA_00"}), "unittest_incorrect_user@lab.ai") == 0)
