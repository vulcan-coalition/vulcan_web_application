import os
import process
import analyse
import gdrive
import shutil
import provision
import csv
from datetime import date
from configuration import get_config


dir_path = os.path.dirname(os.path.realpath(__file__))
results_path = os.path.join(dir_path, "results")
artifacts_path = os.path.join(dir_path, "artifacts")
ground_truth_path = os.path.join(dir_path, "ground_truth")
data_path = os.path.join(dir_path, "data")


def representsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def retrieve(drive_id):
    if drive_id is None:
        return "Drive id is not given."
    last_touch = provision.check()
    category_path = os.path.join(data_path, last_touch, "category.csv")
    g_list = gdrive.listFolder(drive_id, "Data for Labeling")
    found_new = False
    for x in g_list:
        title = x['title']
        if representsInt(title) and title > last_touch:
            last_touch = title
            found_new = True
    if not found_new:
        return "No new data available."

    temp_path = os.path.join(artifacts_path, "temp")
    shutil.rmtree(temp_path, ignore_errors=True)
    result = gdrive.downloadFolder(drive_id, "Data for Labeling/" + last_touch, temp_path)
    if not result:
        return "Download failed."
    raw_path = os.path.join(temp_path, last_touch, "raw_data")
    new_data_path = os.path.join(data_path, last_touch)
    os.makedirs(new_data_path, exist_ok=True)

    # 1. copy fallback and misclassification
    with open(os.path.join(ground_truth_path, "gt_" + last_touch + ".csv"), 'w') as csvfile3:
        writer_gt = csv.writer(csvfile3, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer_gt.writerow(["", "Sentence", "Answers"])

        for p in os.listdir(raw_path):

            with open(os.path.join(raw_path, p), 'r', encoding="utf8") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                title_row = next(csv_reader, None)
                sentence_index = ["sentence" in x for x in title_row].index(True)
                answer_index = ["ground" in x for x in title_row].index(True)
                new_title = []
                for item in title_row:
                    new_title.append(item)

                with open(os.path.join(new_data_path, p), 'w') as csvfile2:
                    writer = csv.writer(csvfile2, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(new_title)
                    for i, row in enumerate(csv_reader):
                        new_row = []
                        for item in row:
                            new_row.append(item)
                        writer.writerow(new_row)

                        sentence = row[sentence_index]
                        if len(row) > answer_index:
                            answers = row[answer_index]
                            if len(answers) > 0:
                                writer_gt.writerow(("", sentence, answers))

    # 2. copy category from the last touch
    shutil.copyfile(category_path, os.path.join(new_data_path, "category.csv"))

    return "New data acquired."


def retrieve_from_api(preloader, data_size=10000):

    last_touch = provision.check()
    category_path = os.path.join(data_path, last_touch, "category.csv")

    last_touch = date.today().strftime("%Y%m%d")
    new_data_path = os.path.join(data_path, last_touch)
    os.makedirs(new_data_path, exist_ok=True)

    # 1. copy download new set
    with open(os.path.join(ground_truth_path, "gt_" + last_touch + ".csv"), 'w') as csvfile3:
        writer_gt = csv.writer(csvfile3, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer_gt.writerow(["", "Sentence", "Answers"])

        with open(os.path.join(new_data_path, "preloaded.csv"), 'w') as csvfile2:
            writer = csv.writer(csvfile2, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["id", "question", "answer"])

            status, data = preloader.fetch_batch(data_size)
            if status <= 0:
                return data

            for datum in data:
                new_row = [datum["id"], datum["question"]]
                writer.writerow(new_row)

                if "answer" in datum and datum["answer"] is not None:
                    writer_gt.writerow(("", datum["question"], datum["answer"]))

    # 2. copy category from the last touch
    shutil.copyfile(category_path, os.path.join(new_data_path, "category.csv"))

    return "New data acquired."


async def submit(drive_id):
    if drive_id is None:
        return "Drive id is not given."
    last_touch = provision.check()

    submission_counter = 0
    g_list = gdrive.listFolder(drive_id, "Data for Labeling/" + last_touch)
    for x in g_list:
        if "submission" in x['title']:
            submission_counter = submission_counter + 1
    suffix = "_" + str(submission_counter) if submission_counter > 0 else ""

    temp_path = os.path.join(artifacts_path, "temp", "submission" + suffix)
    os.makedirs(temp_path, exist_ok=True)
    result = gdrive.uploadFolder(drive_id, temp_path, "Data for Labeling/" + last_touch)
    if not result:
        return "Upload failed."

    packages = await process.generate_summary(protected_user=True)
    for p in packages:
        result = gdrive.uploadFolder(drive_id, p, "Data for Labeling/" + last_touch + "/submission" + suffix)
        if not result:
            return "Upload failed."

    return "Upload succeeded."


async def submit_analysis(drive_id, from_time=None):
    if drive_id is None:
        return "Drive id is not given."

    path = await analyse.analyse(from_time)
    result = gdrive.uploadFolder(drive_id, path, "")
    if not result:
        return "Upload failed."

    return "Upload succeeded."


if __name__ == '__main__':
    gdrive.initialize()
    last_touch = provision.check()
    g_list = gdrive.listFolder(get_config()["data_drive_id"], "Data for Labeling/" + last_touch)
    print([x["title"] for x in g_list])
    submission_counter = 0
    for x in g_list:
        if "submission" in x['title']:
            submission_counter = submission_counter + 1
    suffix = "_" + str(submission_counter) if submission_counter > 0 else ""
    print(suffix)
